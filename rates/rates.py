from .bank_rates import Arigbank,Bogdbank,Capitronbank,Golomtbank,Khanbank,Mongolbank,Statebank,Tdbm,Xacbank

def BankSwitch(request):
    switcher = {
        "khanbank": Khanbank(),
        "tdbm": Tdbm(request),
        "golomtbank": Golomtbank(),
        "xacbank": Xacbank(),
        "arigbank": Arigbank(),
        "bogdbank": Bogdbank(),
        "statebank": Statebank(),
        "mongolbank": Mongolbank(),
        "capitronbank": Capitronbank()
    }

    return switcher.get(request['bank'], "Bank not found!")