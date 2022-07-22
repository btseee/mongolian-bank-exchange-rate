import ssl
from dotenv import load_dotenv
import os, requests
from bs4 import BeautifulSoup
import pandas as pd
from dateutil import parser
import datetime
from requests.structures import CaseInsensitiveDict
load_dotenv()

def Khanbank(request):
    URL = os.environ.get("KHANBANK_URI")
    x = parser.parse(request["date"])

    params = {
        "lang":"en",
        "site":"personal",
        "date":str(x.year)+"-"+str(x.month)+"-"+str(x.day)
    }
    re = requests.get(URL, params=params).json()
    for x in re['data']:
        if(x['code'] == request['currency']):
            return {
                'non_cash': {
                    'sell': {
                        'value': x['sell'],
                        'currency': 'MNT'
                    },
                    'buy': {
                        'value': x['buy'],
                        'currency': 'MNT'
                    }
                },
                'in_cash': {
                    'sell': {
                        'value': x['sell_cash'],
                        'currency': 'MNT'
                    },
                    'buy': {
                        'value': x['buy_cash'],
                        'currency': 'MNT'
                    }
                },
            }
def Tdbm(request):
    URL = os.environ.get("TDBM_URI")
    page = requests.get(URL,params={"dt":request['date']})
    soup = BeautifulSoup(page.text.encode("utf-8"), "html.parser")
    div = soup.find("div", id = os.environ.get("TDBM_TABLE_ID"))
    table = div.find("table")

    df = pd.read_html(str(table))[0]
    
    del df['Mongol Bank']
    del df[('Currency', 'Currency.1')]

    select = df.loc[df[('Currency', 'Currency')] == request['currency']]
    
    return {
        'non_cash': {
            'sell': {
                'value': select.iloc[0][('In non cash', 'SELL')],
                'currency': 'MNT'
            },
            'buy': {
                'value': select.iloc[0][('In non cash', 'BUY')],
                'currency': 'MNT'
            }
        },
        'in_cash': {
            'sell': {
                'value': select.iloc[0][('In cash', 'SELL')],
                'currency': 'MNT'
            },
            'buy': {
                'value': select.iloc[0][('In cash', 'BUY')],
                'currency': 'MNT'
            }
        },
    }
def Golomtbank(request):
    URL = os.environ.get("GOLOMT_URI")
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    x = parser.parse(request["date"])
    date = (x.year*10000)+(x.month*100)+x.day
    re = requests.get(URL, params={"date":date}).json()
    select = re['result'][request['currency']]
    return {
        'non_cash': {
            'sell': {
                'value': select['non_cash_sell']['cvalue'],
                'currency': select['varcurcode']
            },
            'buy': {
                'value': select['non_cash_buy']['cvalue'],
                'currency': select['fixcurcode']
            }
        },
        'in_cash': {
            'sell': {
                'value': select['cash_sell']['cvalue'],
                'currency': select['varcurcode']
            },
            'buy': {
                'value': select['cash_buy']['cvalue'],
                'currency': select['fixcurcode']
            }
        },
    }
def Xacbank(request):
    date = datetime.datetime.today().strftime("%Y.%m.%d")
    URL = os.environ.get("XACBANK_URI")
    page = requests.get(URL,params={"lang":"en"})
    soup = BeautifulSoup(page.text.encode("utf-8"), "html.parser")
    table = soup.findAll("table", id = os.environ.get("XACBANK_TABLE_ID"))
    df = pd.read_html(str(table))[0]

    del df[(str(date),'Mongol Bank')]

    select = df.loc[df[(str(date), 'Currency')] == request['currency']]
    return {
        'non_cash': {
            'sell': {
                'value': select.iloc[0][('In non-cash', 'Sell')],
                'currency': 'MNT'
            },
            'buy': {
                'value': select.iloc[0][('In non-cash', 'Buy')],
                'currency': 'MNT'
            }
        },
        'in_cash': {
            'sell': {
                'value': select.iloc[0][('In cash', 'Sell')],
                'currency': 'MNT'
            },
            'buy': {
                'value': select.iloc[0][('In cash', 'Buy')],
                'currency': 'MNT'
            }
        },
    }
def Arigbank(request):
    date = datetime.datetime.today().strftime("%Y-%m-%d")
    URL = os.environ.get("ARIGBANK_URI")
    page = requests.get(URL)
    soup = BeautifulSoup(page.text.encode("utf-8"), "html.parser")
    table = soup.findAll("table", class_ = os.environ.get("ARIGBANK_CLASS"))
    df = pd.read_html(str(table))[0]
    
    del df[(str(date),'Mongol bank')]
    select = df.loc[df[(str(date), 'Money')] == request['currency']]
    return {
        'non_cash': {
            'sell': {
                'value': select.iloc[0][('In non-cash', 'Sell')],
                'currency': 'MNT'
            },
            'buy': {
                'value': select.iloc[0][('In non-cash', 'Buy')],
                'currency': 'MNT'
            }
        },
        'in_cash': {
            'sell': {
                'value': select.iloc[0][('In cash', 'Sell')],
                'currency': 'MNT'
            },
            'buy': {
                'value': select.iloc[0][('In cash', 'Buy')],
                'currency': 'MNT'
            }
        },
    }
def Bogdbank(request):
    URL = os.environ.get("BOGDBANK_URI")
    x = parser.parse(request["date"])
    params = {
        "date":str(x.year)+"-"+str(x.month)+"-"+str(x.day)
    }
    page = requests.get(URL,params=params,verify=ssl.CERT_NONE)
    soup = BeautifulSoup(page.text.encode("utf-8"), "html.parser")
    table = soup.findAll("table")
    df = pd.read_html(str(table))[0]
    del df[('Монгол банк','Монгол банк')]

    select = df.loc[df[('Валют', 'Валют')] == request['currency']]
    return {
        'non_cash': {
            'sell': {
                'value': select.iloc[0][('Бэлэн бус', 'Зарах')],
                'currency': 'MNT'
            },
            'buy': {
                'value': select.iloc[0][('Бэлэн бус', 'Авах')],
                'currency': 'MNT'
            }
        },
        'in_cash': {
            'sell': {
                'value': select.iloc[0][('Бэлэн', 'Зарах')],
                'currency': 'MNT'
            },
            'buy': {
                'value': select.iloc[0][('Бэлэн', 'Авах')],
                'currency': 'MNT'
            }
        },
    }
def Statebank(request):
    URL = os.environ.get("STATEBANK_URI")

    params = {
        "date":datetime.datetime.strtime(request["date"],"%Y-%m-%d")
    }
    page = requests.get(URL,params=params)
    soup = BeautifulSoup(page.text.encode("utf-8"), "html.parser")
    table = soup.findAll("table", class_=os.environ.get("STATEBANK_CLASS"))
    df = pd.read_html(str(table))[0]

    print(df)
    # del df[('Монгол банк','Монгол банк')]

    # select = df.loc[df[('Валют', 'Валют')] == request['currency']]
    # return {
    #     'non_cash': {
    #         'sell': {
    #             'value': select.iloc[0][('Бэлэн бус', 'Зарах')],
    #             'currency': 'MNT'
    #         },
    #         'buy': {
    #             'value': select.iloc[0][('Бэлэн бус', 'Авах')],
    #             'currency': 'MNT'
    #         }
    #     },
    #     'in_cash': {
    #         'sell': {
    #             'value': select.iloc[0][('Бэлэн', 'Зарах')],
    #             'currency': 'MNT'
    #         },
    #         'buy': {
    #             'value': select.iloc[0][('Бэлэн', 'Авах')],
    #             'currency': 'MNT'
    #         }
    #     },
    # }
def Mongolbank():
    URL = os.environ.get("MONGOLBANK_URI")
    return URL
def Capitronbank():
    URL = os.environ.get("CAPITRONBANK_URI")
    return URL