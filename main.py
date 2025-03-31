import os
import pymongo
from bson import ObjectId
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
from dotenv import load_dotenv
import motor.motor_asyncio

app = FastAPI()
load_dotenv()

# Database connection as a dependency
async def get_database():
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
    player_name: str
    score: int

# GET methods
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/player_score/")
async def get_player_score(player_id: str, db = Depends(get_database)):
    try:
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
async def get_sprite(sprite_id: str, db = Depends(get_database)):
    try:
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
async def get_audio(audio_id: str, db = Depends(get_database)):
    try:
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
async def upload_sprite(file: UploadFile = File(...), db = Depends(get_database)):
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
async def upload_audio(file: UploadFile = File(...), db = Depends(get_database)):
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


@app.post("/upload_player_score")
async def add_score(score: PlayerScore, db = Depends(get_database)):
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
