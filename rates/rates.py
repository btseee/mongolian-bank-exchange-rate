from .bank_rates import Arigbank,Bogdbank,Capitronbank,Golomtbank,Khanbank,Mongolbank,Statebank,Tdbm,Xacbank

class RatesSwitch():
    def bank(self,bank):
        default = {"message":"Bank not found!"}
        return getattr(self, 'case_'+str(bank), lambda: default)()

    def case_khanbank(self):
        return Khanbank()
    def case_tdbm(self):
        return Tdbm()
    def case_golomtbank(self):
        return Golomtbank()
    def case_xacbank(self):
        return Xacbank()
    def case_arigbank(self):
        return Arigbank()
    def case_bogdbank(self):
        return Bogdbank()
    def case_statebank(self):
        return Statebank()
    def case_mongolbank(self):
        return Mongolbank()
    def case_capitronbank(self):
        return Capitronbank