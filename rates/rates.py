from .bank_rates import Bank

def BankSwitch(request):
    request['bank'] = str(request['bank']).lower().strip()
    request['currency'] = str(request['currency']).upper().strip()

    if request['bank'] == "khanbank":
        return Bank.Khanbank(request)
    elif request['bank'] == "tdbm":
        return Bank.Tdbm(request),
    elif request['bank'] == "golomtbank":
        return Bank.Golomtbank(request),
    elif request['bank'] == "xacbank":
        return Bank.Xacbank(request),
    elif request['bank'] == "arigbank":
        return Bank.Arigbank(request),
    elif request['bank'] == "bogdbank":
        return Bank.Bogdbank(request),
    elif request['bank'] == "statebank":
        return Bank.Statebank(request),
    elif request['bank'] == "mongolbank":
        return Bank.Mongolbank(request),
    elif request['bank'] == "capitronbank":
        return Bank.Capitronbank(request)
    else:
        return {"message": "Bank not found!"}
        