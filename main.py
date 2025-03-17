from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()
uri = "mongodb+srv://liam:OoNpDaWeRtRhnJyU@mcastcluster.hwo2c.mongodb.net/?retryWrites=true&w=majority&appName=MCASTCluster"

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

client = MongoClient(uri)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)