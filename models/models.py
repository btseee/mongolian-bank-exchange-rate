class ExchangeRequest:
    bank: str
    currency: str
    date: str

    def __init__(self, bank: str, currency: str, date: str) -> None:
        self.bank = bank
        self.currency = currency
        self.date = date

class Buy:
    def __init__(self, value: float, currency: str) -> None:
        self.value = value
        self.currency = currency


class isCash:
    def __init__(self, sell: Buy, buy: Buy) -> None:
        super().__init__(sell)
        super().__init__(buy)


class ExchangeResponse:
    def __init__(self, non_cash: isCash, in_cash: isCash) -> None:
        super().__init__(non_cash)
        super().__init__(in_cash)


obj1 = isCash(1,"MNT",2,"USD")
print(obj1.__dict__)