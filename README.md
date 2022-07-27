# mongolian-bank-exchange-rate

Монгол банкуудын ханш татдаг BACK-END

Python 3.10+ дээш хувилбар дээр л ажиллана

[ Production дээр туршаагүй байгаа болно]


### Ажлуулах
```
uvicorn app:app --reload
```

### Params сонголтууд
```
"bank" сонголтууд:
    OK: khanbank,tdbm,golomtbank,bogdbank,statebank,mongolbank,
    Өдөр сонгох боломжгүй: xacbank,arigbank,capitronbank

"currency" сонголтууд:
    Зөвхөн томоор бичнэ шүү

"date" сонголтууд:
    {жил}/{сар}/{өдөр} гэсэн форматтай илгээнэ үү
```

### Хүсэлт явуулах HTTP
```
http://127.0.0.1:8000/rates
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
