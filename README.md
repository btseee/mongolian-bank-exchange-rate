# mongolian-bank-exchange-rate

Монгол банкуудын ханш - Exchange rates of Mongolian banks

### TDBM -рүү request явуулах:

```
{
    "bank":"tdbm",
    "currency": "USD",
    "date":"2022/07/21"
}
```
### TDBM -н response:

```
{
    "non_cash": {
        "sell": {
            "value": 3158.0,
            "currency": "USD"
        },
        "buy": {
            "value": 3148.0,
            "currency": "USD"
        }
    },
    "in_cash": {
        "sell": {
            "value": 3174.0,
            "currency": "USD"
        },
        "buy": {
            "value": 3148.0,
            "currency": "USD"
        }
    }
}
```
