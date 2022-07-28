from fastapi import Request
import os
import urllib, re


bank_list = ["khanbank","tdbm","golomtbank","bogdbank","statebank","mongolbank","xacbank","arigbank","capitronbank"]

async def requestCheck(request: Request):
    if(request.headers.get('Content-Type')):
        request_json = await request.json()
        if(request_json['bank'] and request_json['bank'] in bank_list):
            if(request_json['currency']):
                if(request_json['date']):
                    return True
                else:
                    return {"message": "No [date] field in request"}
            else: 
                return {"message": "No [currency] field in request"}
        else: 
            return {"message": "No [bank] field in request"}
    else:
        return {"message": "Empty request or request not JSON"}