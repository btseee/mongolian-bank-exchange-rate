from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Server is working fine!"}

@app.get("/rates")
async def rates():
    return

@app.get("/exchange")
async def exchange():
    return