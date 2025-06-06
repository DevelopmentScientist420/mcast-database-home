import base64
import os
from bson import ObjectId
from collections import OrderedDict
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi.params import Depends
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import motor.motor_asyncio

from security_middleware import SecurityHeadersMiddleware

app = FastAPI()
load_dotenv()

# Adds security middleware from security_middleware.py
app.add_middleware(SecurityHeadersMiddleware)

async def get_database():
    """
    This method is used as a dependency for all the routes which require a connection to the MongoDB database.
    It creates a new client for each request and closes after the request is completed.
    The MONGODB_URI environment variable is used so the password isn't exposed in the code.
    """

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
    :return: A dictionary containing the sprite file name and content.
    """
    try:
        if not ObjectId.is_valid(sprite_id):
            raise HTTPException(status_code=400, detail="Invalid Id")

        sprite_doc = await db.sprites.find_one({"_id": ObjectId(sprite_id)})
        if sprite_doc:
            sprite_base64 = base64.b64encode(sprite_doc["content"]).decode("utf-8")
            return {"filename": sprite_doc["filename"], "content": sprite_base64}
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
    :return: A dictionary containing the audio file name and content.
    """
    try:
        if not ObjectId.is_valid(audio_id):
            raise HTTPException(status_code=400, detail="Invalid Id")

        audio_doc = await db.audio.find_one({"_id": ObjectId(audio_id)})
        if audio_doc:
            audio_base64 = base64.b64encode(audio_doc["content"]).decode("utf-8")
            return {"filename": audio_doc["filename"], "content": audio_base64}
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

# PUT endpoints

@app.put("/player_score")
async def update_player_score(player_id: str, score: PlayerScore, db=Depends(get_database)):
    """
    A simple PUT endpoint which updates the player score in the database.
    It throws an error if the player is not found.

    :param player_id: The ID of the player whose score is to be updated.
    :param score: The new player score to be updated. It must contain the player name and score.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the message and the ID of the updated score.
    """
    try:
        if not ObjectId.is_valid(player_id):
            raise HTTPException(status_code=400, detail="Invalid Id")

        result = await db.scores.update_one({"_id": ObjectId(player_id)}, {"$set": score.model_dump()})
        if result.modified_count == 1: # Checks if mongo successfully updated the player score
            return {"message": "Player score updated", "id": player_id}
        else:
            raise HTTPException(status_code=404, detail="Player not found")
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error updating player score: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to update player score: {str(e)}")

@app.put("/sprite")
async def update_sprite(sprite_id: str, file: UploadFile = File(...), db=Depends(get_database)):
    """
    A simple PUT endpoint which updates the sprite in the database.
    It throws an error if the sprite is not found.

    :param sprite_id: The ID of the sprite to be updated.
    :param file: The new sprite file to be uploaded. It must be PNG or JPG, else the endpoint will return a 400 error.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the message and the ID of the updated sprite.
    """
    if not file.filename.endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PNG and JPG are allowed.")
    try:
        if not ObjectId.is_valid(sprite_id):
            raise HTTPException(status_code=400, detail="Invalid Id")

        content = await file.read()
        result = await db.sprites.update_one({"_id": ObjectId(sprite_id)}, {"$set": {"filename": file.filename, "content": content}})
        if result.modified_count == 1: # Checks if mongo successfully updated the file
            return {"message": "Sprite updated", "id": sprite_id}
        else:
            raise HTTPException(status_code=404, detail="Sprite not found")
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error updating sprite: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to update sprite: {str(e)}")

@app.put("/audio")
async def update_audio(audio_id: str, file: UploadFile = File(...), db=Depends(get_database)):
    """
    A simple PUT endpoint which updates the audio file in the database.
    It throws an error if the audio file is not found.

    :param audio_id: The ID of the audio file to be updated.
    :param file: The new audio file to be uploaded. It must be MP3, WAV or OGG, else the endpoint will return a 400 error.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the message and the ID of the updated audio file.
    """
    if not file.filename.endswith(('.mp3', '.wav', '.ogg')):
        raise HTTPException(status_code=400, detail="Invalid file type. File must be an audio file!")
    try:
        if not ObjectId.is_valid(audio_id):
            raise HTTPException(status_code=400, detail="Invalid Id")

        content = await file.read()
        result = await db.audio.update_one({"_id": ObjectId(audio_id)}, {"$set": {"filename": file.filename, "content": content}})
        if result.modified_count == 1: # Checks if mongo successfully updated the file
            return {"message": "Audio updated", "id": audio_id}
        else:
            raise HTTPException(status_code=404, detail="Audio not found")
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error updating audio: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to update audio: {str(e)}")

# DELETE endpoints

@app.delete("/audio")
async def delete_audio(audio_id: str, db=Depends(get_database)):
    """
    A simple DELETE endpoint which deletes an audio file from the database using a unique ID.
    It throws an error if the audio file is not found.

    :param audio_id: The ID of the audio file to be deleted.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the message and the ID of the deleted audio file.
    """
    try:
        if not ObjectId.is_valid(audio_id):
            raise HTTPException(status_code=400, detail="Invalid Id")

        result = await db.audio.delete_one({"_id": ObjectId(audio_id)})
        if result.deleted_count == 1:
            return {"message": "Audio deleted", "id": audio_id}
        else:
            raise HTTPException(status_code=404, detail="Audio not found")
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error deleting audio: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to delete audio: {str(e)}")

@app.delete("/sprite")
async def delete_sprite(sprite_id: str, db=Depends(get_database)):
    """
    A simple DELETE endpoint which deletes a sprite from the database using a unique ID.
    It throws an error if the sprite is not found.

    :param sprite_id: The ID of the sprite to be deleted.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the message and the ID of the deleted sprite.
    """
    try:
        if not ObjectId.is_valid(sprite_id):
            raise HTTPException(status_code=400, detail="Invalid Id")

        result = await db.sprites.delete_one({"_id": ObjectId(sprite_id)})
        if result.deleted_count == 1:
            return {"message": "Sprite deleted", "id": sprite_id}
        else:
            raise HTTPException(status_code=404, detail="Sprite not found")
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error deleting sprite: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to delete sprite: {str(e)}")

@app.delete("/player_score")
async def delete_player_score(player_id: str, db=Depends(get_database)):
    """
    A simple DELETE endpoint which deletes a player score from the database using a unique ID.
    It throws an error if the player score is not found.

    :param player_id: The ID of the player score to be deleted.
    :param db: The database connection is passed as a dependency.
    :return: A dictionary containing the message and the ID of the deleted player score.
    """
    try:
        if not ObjectId.is_valid(player_id):
            raise HTTPException(status_code=400, detail="Invalid Id")

        result = await db.scores.delete_one({"_id": ObjectId(player_id)})
        if result.deleted_count == 1:
            return {"message": "Player score deleted", "id": player_id}
        else:
            raise HTTPException(status_code=404, detail="Player score not found")
    except Exception as e:
        # Log the specific error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error deleting player score: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to delete player score: {str(e)}")

