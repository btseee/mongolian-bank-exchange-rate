from fastapi import FastAPI, Request
from dotenv import load_dotenv
import os
from rates.rates import RatesSwitch

load_dotenv()

app = FastAPI()
rates = RatesSwitch()
@app.get("/")
async def root():
    return {"message": "Server is working fine!"}

@app.get("/rates")
async def rates(request: Request):
    return request.bank

@app.get("/exchange")
async def exchange():
    return