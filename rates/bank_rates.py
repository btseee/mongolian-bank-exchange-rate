import ssl
from dotenv import load_dotenv
import os, requests
from bs4 import BeautifulSoup
import pandas as pd
from dateutil import parser
import datetime
from requests.structures import CaseInsensitiveDict
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver import ActionChains
import time
load_dotenv()

class Bank():
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
        print(df)

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
        date = datetime.datetime.strptime(request["date"],"%Y/%m/%d").strftime("%Y.%m.%d")
        URL = os.environ.get("XACBANK_URI")

        browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())
        browser.get(URL)
        delay = 10 # seconds
        WebDriverWait(browser, delay)

        browser.find_element(By.ID, 'rate_date').clear()
        browser.find_element(By.ID, 'rate_date').send_keys(date)
        browser.find_element(By.ID, 'rate_show').click()

        
        soup = BeautifulSoup(browser.page_source, "html.parser")
        browser.close()
        table = soup.findAll("table", id = os.environ.get("XACBANK_TABLE_ID"))
        df = pd.read_html(str(table))[0]
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
        date = datetime.datetime.strptime(request["date"],"%Y/%m/%d").strftime("%Y-%m-%d")
        URL = os.environ.get("ARIGBANK_URI")

        browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())
        browser.get(URL)
        delay = 10 # seconds
        WebDriverWait(browser, delay)

        browser.find_element(By.ID, 'rate_datepicker').clear()
        browser.find_element(By.ID, 'rate_datepicker').send_keys(date)
        browser.find_element(By.ID, 'rate_datepicker').submit()

        time.sleep(delay)
        soup = BeautifulSoup(browser.page_source, "html.parser")
        browser.close()
        table = soup.findAll("table", class_ = os.environ.get("ARIGBANK_CLASS"))
        df = pd.read_html(str(table))[0]
        select = df.loc[df[(str(date), 'Валют')] == request['currency']]
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
            "date": datetime.datetime.strptime(request["date"],"%Y/%m/%d").strftime("%Y-%m-%d")
        }
        page = requests.get(URL,params=params)
        soup = BeautifulSoup(page.text.encode("utf-8"), "html.parser")
        table = soup.findAll("table", class_=os.environ.get("STATEBANK_CLASS"))
        df = pd.read_html(str(table))[0]

        select = df.loc[df[('Валют', 'Валют')] == request['currency']]
        print(select)
        return {
            'non_cash': {
                'sell': {
                    'value': select.iloc[0][('бэлэн бус', 'Зарах')],
                    'currency': 'MNT'
                },
                'buy': {
                    'value': select.iloc[0][('бэлэн бус', 'Авах')],
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
    def Mongolbank(request):
        URL = os.environ.get("MONGOLBANK_URI")
        date = datetime.datetime.strptime(request["date"],"%Y/%m/%d")
        params = {
            "vYear": date.year,
            "vMonth": date.month,
            "vDay": date.day
        }
        page = requests.get(URL, params=params)
        soup = BeautifulSoup(page.text.encode("utf-8"), "html.parser")
        table = soup.findAll("ul", class_=os.environ.get("MONGOLBANK_CLASS"))
        df = pd.read_html(str(table))
        for i in range(0, len(df)):
            if df[i].iloc[0][1] == request["currency"]:
                return {
                    'non_cash': {
                        'sell': {
                            'value': df[i].iloc[0][2],
                            'currency': 'MNT'
                        },
                        'buy': {
                            'value': df[i].iloc[0][2],
                            'currency': 'MNT'
                        }
                    },
                    'in_cash': {
                        'sell': {
                            'value': df[i].iloc[0][2],
                            'currency': 'MNT'
                        },
                        'buy': {
                            'value': df[i].iloc[0][2],
                            'currency': 'MNT'
                        }
                    },
                }
    def Capitronbank(request):
        URL = os.environ.get("CAPITRONBANK_URI")
        browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())
        browser.get(URL)
        delay = 10 # seconds
        WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME,'rs-modal-header-close')))
        browser.find_element(By.CLASS_NAME,'rs-modal-header-close').click()
        soup = BeautifulSoup(browser.page_source, "html.parser")
        browser.close()
        table = soup.findAll("table")
        df = pd.read_html(str(table))[0]
        date = datetime.datetime.today()
        select = df.loc[df[(date.strftime("%Y/%m/%d"), 'Currency')] == request['currency']]
        return {
            'non_cash': {
                'sell': {
                    'value': select.iloc[0][('In non cash', 'Sell')],
                    'currency': 'MNT'
                },
                'buy': {
                    'value': select.iloc[0][('In non cash', 'Buy')],
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