from fastapi import FastAPI, Request
from rates.rates import BankSwitch
from tools.tools import requestCheck
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API is working fine bro!"}

@app.get("/rates")
async def rates(request: Request):
    check = await requestCheck(request)
    if(check):
        request_json = await request.json()
        return BankSwitch(request_json)
    else:
        return check
                