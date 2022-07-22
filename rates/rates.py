from .bank_rates import Arigbank,Bogdbank,Capitronbank,Golomtbank,Khanbank,Mongolbank,Statebank,Tdbm,Xacbank

def BankSwitch(request):
    switcher = {
        "khanbank": Khanbank(request),
        "tdbm": Tdbm(request),
        "golomtbank": Golomtbank(request),
        "xacbank": Xacbank(request),
        "arigbank": Arigbank(request),
        "bogdbank": Bogdbank(request),
        "statebank": Statebank(request),
        "mongolbank": Mongolbank(request),
        "capitronbank": Capitronbank(request)
    }

    return switcher.get(request['bank'], "Bank not found!")