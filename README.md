# Documentation

## Setup

This project is a simple REST API built with Python using the FastAPI framework. Its purpose
is to manage player scores and media files (sprites and audio) for a game.
The virtual environment was created using venv and dependencies are managed with pip.

It's recommended to open the project folder in Pycharm so all dependencies are automatically installed through
requirements.txt, and it chooses the right Python interpreter. 

It's **important** to note that Pydantic is not in requirements.txt because it would cause a version conflict
with Vercel during the deployment process.

## API Routes

### GET /player_score

The `/player_score` route is used to retrieve the score of a player based on their ID in the database. It accepts a GET
request with the following parameters:

- `player_id` (required): The ID of the player whose score to retrieve.

This route returns the player name and the score.

### GET /sprite

The `/sprite` route is used to retrieve the sprite of a player based on their ID in the database. It accepts a GET
request with the following parameters:

- `sprite_id` (required): The ID of the sprite to retrieve.

This route returns the sprite's file name.

### GET /audio

The `/audio` route is used to retrieve the audio file of a player based on their ID in the database. It accepts a GET
request with the following parameters:

- `audio_id` (required): The ID of the audio file to retrieve.

This route returns the audio file's name.

### POST /upload_player_score

The `/upload_player_score` route is used to upload a player's score to the database. It accepts a POST request with the
following parameters as a **RAW JSON**:

- `player_name` (required): Sets the player's name.
- `score` (required): Sets the player's score.

```json
{
  "player_name": "John",
  "score": 2000
}
```

### POST /sprite

The `/sprite` route is used to upload a sprite file for a player. It accepts a POST request with the following
parameters:

- `file` (required): The sprite file to upload.

### POST /audio

The `/audio` route is used to upload an audio file for a player. It accepts a POST request with the following
parameters:

- `file` (required): The audio file to upload.

