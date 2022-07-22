from fastapi import FastAPI, Request
from rates.rates import BankSwitch

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API is working fine bro!"}

@app.get("/rates")
async def rates(request: Request):
    if(request.headers.get('Content-Type')):
        request_json = await request.json()
        
        if(request_json['bank']):
            if(request_json['currency']):
                if(request_json['date']):
                    return BankSwitch(request_json)
                else:
                    return {"message": "No date field in request"}
            else: 
                return {"message": "No currency field in request"}
        else: 
            return {"message": "Request not valid"}
    else:
        return {"message": "Empty request or request not JSON"}