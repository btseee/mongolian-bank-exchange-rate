from .bank_rates import Bank

def BankSwitch(request):
    match request['bank']:
        case "khanbank":
            return Bank.Khanbank(request)
        case "tdbm":
            return Bank.Tdbm(request),
        case "golomtbank":
            return Bank.Golomtbank(request),
        case "xacbank":
            return Bank.Xacbank(request),
        case "arigbank":
            return Bank.Arigbank(request),
        case "bogdbank":
            return Bank.Bogdbank(request),
        case "statebank":
            return Bank.Statebank(request),
        case "mongolbank":
            return Bank.Mongolbank(request),
        case "capitronbank":
            return Bank.Capitronbank(request)