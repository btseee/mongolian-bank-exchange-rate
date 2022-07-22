import requests

class RatesSwitch():
    def bank(self,bank):
        default = "Bank is not found!"

        return getattr(self, 'case_'+str(bank), lambda: default)()

    
    def case_khanbank(self):
        return 0
    def case_tdbm(self):
        return 1
    def case_golomtbank(self):
        return 2
    def case_xacbank(self):
        return 3
    def case_arigbank(self):
        return 4
    def case_bogdbank(self):
        return 5
    def case_statebank(self):
        return 6
    def case_mongolbank(self):
        return 7
    def case_capitronbank(self):
        return 8