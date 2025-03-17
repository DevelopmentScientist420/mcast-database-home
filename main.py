from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
import motor.motor_asyncio

app = FastAPI()

# Database connection as a dependency
async def get_database():
    # Create a new client for each request
    client = motor.motor_asyncio.AsyncIOMotorClient(
        "mongodb+srv://liam:OoNpDaWeRtRhnJyU@mcastcluster.hwo2c.mongodb.net/?retryWrites=true&w=majority&appName=MCASTCluster",
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


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...), db = Depends(get_database)):
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
