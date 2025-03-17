from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import motor.motor_asyncio
import traceback

MONGO_URI = "mongodb+srv://liam:OoNpDaWeRtRhnJyU@mcastcluster.hwo2c.mongodb.net/?retryWrites=true&w=majority&appName=MCASTCluster"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect on startup
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    app.mongodb_client = client
    app.mongodb = client.multimedia_db
    yield
    # Close connection on shutdown
    client.close()


# Create FastAPI app with lifespan manager
app = FastAPI(lifespan=lifespan)


class PlayerScore(BaseModel):
    player_name: str
    score: int


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...)):
    try:
        # In a real application, the file should be saved to a storage service
        content = await file.read()
        sprite_doc = {"filename": file.filename, "content": content}
        result = await app.mongodb.sprites.insert_one(sprite_doc)
        return {"message": "Sprite uploaded", "id": str(result.inserted_id)}
    except Exception as e:
        # Log the specific error
        error_details = traceback.format_exc()
        print(f"Error recording score: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to upload sprite: {str(e)}")


@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...)):
    try:
        content = await file.read()
        audio_doc = {"filename": file.filename, "content": content}
        result = await app.mongodb.audio.insert_one(audio_doc)
        return {"message": "Audio file uploaded", "id": str(result.inserted_id)}
    except Exception as e:
        # Log the specific error
        error_details = traceback.format_exc()
        print(f"Error recording score: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to upload audio: {str(e)}")


@app.post("/player_score")
async def add_score(score: PlayerScore):
    try:
        score_doc = score.model_dump()
        result = await app.mongodb.scores.insert_one(score_doc)
        return {"message": "Score recorded", "id": str(result.inserted_id)}
    except Exception as e:
        # Log the specific error
        error_details = traceback.format_exc()
        print(f"Error recording score: {str(e)}\n{error_details}")
        raise HTTPException(500, f"Failed to record score: {str(e)}")
