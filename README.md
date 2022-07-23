# mongolian-bank-exchange-rate

Монгол банкуудын ханш татдаг BACK-END

[ Production дээр туршаагүй байгаа болно]


### Ажлуулах
```
uvicorn main:app --reload
```

### Params сонголтууд
```
"bank" сонголтууд:
    OK: khanbank,tdbm,golomtbank,bogdbank,statebank,mongolbank,
    Өдөр сонгох боломжгүй: xacbank,arigbank,
    Дуусаагүй: capitronbank

"currency" сонголтууд:
    Зөвхөн томоор бичнэ шүү

"date" сонголтууд:
    {жил}/{сар}/{өдөр} гэсэн форматтай илгээнэ үү
```

### Request явуулах:

```
{
    "bank":"tdbm",
    "currency": "USD",
    "date":"2022/07/21"
}
```
### Response:

```
{
    "non_cash": {
        "sell": {
            "value": 3158.0,
            "currency": "MNT"
        },
        "buy": {
            "value": 3148.0,
            "currency": "MNT"
        }
    },
    "in_cash": {
        "sell": {
            "value": 3174.0,
            "currency": "MNT"
        },
        "buy": {
            "value": 3148.0,
            "currency": "MNT"
        }
    }
}
```
