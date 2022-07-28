class ExchangeRequest:
    def __init__(self, bank: str, currency: str, date: str) -> None:
        if(currency):
            self.currency = currency.upper().strip()
        self.bank = bank.lower().strip()
        self.date = date
    def show(self):
        print(self.bank, self.currency, self.date)
class ExchangeResponse:
    def __init__(self,currency: str, noncash_sell_value: float, noncash_buy_value: float, cash_sell_value: float,cash_buy_value: float) -> None:
        self.exrate = {
            'non_cash': {
                'sell': {
                    'value': noncash_sell_value,
                    'currency': currency.upper().strip(),
                },
                'buy': {
                    'value': noncash_buy_value,
                    'currency': currency.upper().strip(),
                }
            },
            'in_cash': {
                'sell': {
                    'value': cash_sell_value,
                    'currency': currency.upper().strip(),
                },
                'buy': {
                    'value': cash_buy_value,
                    'currency': currency.upper().strip(),
                }
            },
        }


obj1 = ExchangeResponse("mnt", 1,2,3,4)

obj2 = ExchangeRequest("tdb,","mnt","2020/5/5")

obj2.show()
