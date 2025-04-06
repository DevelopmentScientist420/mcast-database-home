import os
import pymongo
from bson import ObjectId
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Depends
from pydantic import BaseModel, Field, constr
from dotenv import load_dotenv
import motor.motor_asyncio

app = FastAPI()
load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your frontend domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Security-Policy"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

async def get_database():
    """This method is used as a dependency for all the routes which require a connection to the MongoDB database.
    It creates a new client for each request and closes after the request is completed.
    The MONGODB_URI environment variable is used so the password isn't exposed in the code."""

    # Create a new client for each request
    mongodb_uri = os.environ.get("MONGODB_URI")
    client = motor.motor_asyncio.AsyncIOMotorClient(
        mongodb_uri,
        maxPoolSize=1,
        minPoolSize=0,
        serverSelectionTimeoutMS=5000
    )
    try:
        yield client.multimedia_db
    finally:
        client.close()  # Ensure connection is closed after request


class PlayerScore(BaseModel):
    """
    This is a class used to define the schema of the player score.
    The Field class is used to constrain the length of the player name and define minimum and maximum score
    for input sanitization.
    This class prevents NoSQL injection attacks since it only allows the defined fields to be passed.
    """
    player_name: str = Field(..., min_length=1, max_length=50)
    score: int = Field(..., ge=0, le=200)


# GET methods

@app.get("/")
async def root():
    """
    This is a root endpoint used as a test to check if the API is running.
    :return: A 'Hello World' message.
    """

    return {"message": "Hello World"}


@app.get("/player_score")
async def get_player_score(player_id: str, db=Depends(get_database)):
    """
    A simple GET endpoint which returns the player name and score from the database.
    It throws an error if the player is not found.

    :param player_id: The ID of the player whose score is to be retrieved.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the player name and score.
    """
    try:
        if not ObjectId.is_valid(player_id):
            raise HTTPException(status_code=400, detail="Invalid Id")

        score_doc = await db.scores.find_one({"_id": ObjectId(player_id)})
        if score_doc:
            return {"player_name": score_doc["player_name"], "score": score_doc["score"]}
        else:
            raise HTTPException(status_code=404, detail="Player not found")
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error retrieving player score: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to retrieve player score: {str(e)}")


@app.get("/sprite")
async def get_sprite(sprite_id: str, db=Depends(get_database)):
    """
    A simple GET endpoint which searches and returns the sprite file name from the database using a unique ID.
    It throws an error if the sprite is not found.

    :param sprite_id: The ID of the sprite to be retrieved.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the sprite file name.
    """
    try:
        if not ObjectId.is_valid(sprite_id):
            raise HTTPException(status_code=400, detail="Invalid Id")

        sprite_doc = await db.sprites.find_one({"_id": ObjectId(sprite_id)})
        if sprite_doc:
            return {"filename": sprite_doc["filename"]}
        else:
            raise HTTPException(status_code=404, detail="Sprite not found")
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error retrieving sprite: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to retrieve sprite: {str(e)}")


@app.get("/audio")
async def get_audio(audio_id: str, db=Depends(get_database)):
    """
    A simple GET endpoint which returns the audio file name from the database.
    If audio file is not found, it throws a 404.

    :param audio_id: The ID of the audio file to be retrieved.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the audio file name.
    """
    try:
        if not ObjectId.is_valid(audio_id):
            raise HTTPException(status_code=400, detail="Invalid Id")

        audio_doc = await db.audio.find_one({"_id": ObjectId(audio_id)})
        if audio_doc:
            return {"filename": audio_doc["filename"]}
        else:
            raise HTTPException(status_code=404, detail="Audio not found")
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error retrieving audio: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to retrieve audio: {str(e)}")


# POST methods

@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...), db=Depends(get_database)):
    """
    A simple POST endpoint which uploads a sprite to the database.
    An error 400 is thrown if the file type is invalid.

    :param file: The sprite file to be uploaded. It must be PNG or JPG, else the endpoint will return a 400 error.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the message and the ID of the uploaded sprite.
    """
    if not file.filename.endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PNG and JPG are allowed.")
    try:
        # In a real application, the file should be saved to a storage service
        content = await file.read()
        sprite_doc = {"filename": file.filename, "content": content}
        result = await db.sprites.insert_one(sprite_doc)
        return {"message": "Sprite uploaded", "id": str(result.inserted_id)}
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error recording score: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to upload sprite: {str(e)}")


@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...), db=Depends(get_database)):
    """
    A simple POST endpoint which uploads an audio file to the database. An error 400 is thrown if the file type is invalid.

    :param file: The audio file to be uploaded. It must be MP3, WAV or OGG, else the endpoint will return a 400 error.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the message and the ID of the uploaded audio file.
    """
    if not file.filename.endswith(('.mp3', '.wav', '.ogg')):
        raise HTTPException(status_code=400, detail="Invalid file type. File must be an audio file!")
    try:
        content = await file.read()
        audio_doc = {"filename": file.filename, "content": content}
        result = await db.audio.insert_one(audio_doc)
        return {"message": "Audio file uploaded", "id": str(result.inserted_id)}
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error recording score: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to record score: {str(e)}")


@app.post("/player_score")
async def add_score(score: PlayerScore, db=Depends(get_database)):
    """
    A simple POST endpoint which records the player score in the database.
    The endpoint will throw an error 500 if it fails to record the score.

    :param score: The player score to be recorded. It must contain the player name and score.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the message and the ID of the recorded score.
    """
    try:
        score_doc = score.model_dump()
        result = await db.scores.insert_one(score_doc)
        return {"message": "Score recorded", "id": str(result.inserted_id)}
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error recording score: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to record score: {str(e)}")
