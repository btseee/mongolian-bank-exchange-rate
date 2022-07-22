from locale import currency
from dotenv import load_dotenv
import os, requests,asyncio
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse

load_dotenv()

def Khanbank():
    URL = os.environ.get("KHANBANK_URI")
    return URL

def Tdbm(request):
    URL = os.environ.get("TDBM_URI")
    date = urllib.parse.quote_plus(str(request['date']))
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
                'currency': request['currency']
            },
            'buy': {
                'value': select.iloc[0][('In non cash', 'BUY')],
                'currency': request['currency']
            }
        },
        'in_cash': {
            'sell': {
                'value': select.iloc[0][('In cash', 'SELL')],
                'currency': request['currency']
            },
            'buy': {
                'value': select.iloc[0][('In cash', 'BUY')],
                'currency': request['currency']
            }
        },
    }
def Golomtbank():
    URL = os.environ.get("GOLOMT_URI")
    return URL
def Xacbank():
    URL = os.environ.get("XACBANK_URI")
    return URL
def Arigbank():
    URL = os.environ.get("ARIGBANK_URI")
    return URL
def Bogdbank():
    URL = os.environ.get("BOGDBANK_URI")
    return URL
def Statebank():
    URL = os.environ.get("STATEBANK_URI")
    return URL
def Mongolbank():
    URL = os.environ.get("MONGOLBANK_URI")
    return URL
def Capitronbank():
    URL = os.environ.get("CAPITRONBANK_URI")
    return URL