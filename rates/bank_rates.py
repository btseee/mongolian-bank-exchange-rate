from dotenv import load_dotenv
import os, requests,asyncio
from bs4 import BeautifulSoup

load_dotenv()

def Khanbank():
    URL = os.environ.get("KHANBANK_URI")
    return URL
def Tdbm():
    URL = os.environ.get("TDBM_URI")
    page = requests.get(URL)
    soup = BeautifulSoup(page.text.encode("utf-8"), "html.parser")
    div = soup.find("div", id = "exchange-table-result")
    table = div.find("table")

    headers = ['flag', 'name', 'mongol_bank', 'belen_bus_avah', 'belen_bus_zarah', 'belen_avah', 'belen_zarah']
    table_rows = [ row for row in table.find_all('tr')]

    result = [{headers[index]:cell.text.replace("\n", "").replace(" ","") for index,cell in enumerate(row.find_all("td")) } for row in table_rows]

    for i in result:  
        if 'name' in i:
            if i['name'] == 'АНУ-ындоллар': 
                print("TDBM")
                print(i)
    return URL
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