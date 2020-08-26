import mechanize
import pyodbc
import re
import os
from datetime import date
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

data_hoje = date.today().strftime('%d-%m-%Y')
data_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

url = "https://platform.converja.com/converja/index.php?r=Cdr/external"
pageForm = "https://platform.converja.com/converja/index.php?r=cdr%2Fexternal&LogExtern%5Bdate_start%5D=" + data_hoje + "&LogExtern%5Btime1%5D=00%3A00&LogExtern%5Bdate_end%5D=" + data_hoje + "&LogExtern%5Btime2%5D=23%3A59&LogExtern%5Bsrc_group_search%5D=2&LogExtern%5Bsrc%5D=&LogExtern%5Bcard_id%5D=&LogExtern%5Bcalledstation%5D=&LogExtern%5Breal_sessiontime%5D=&LogExtern%5Bterminatecauseid%5D=1&yt1=Gerar+Relatorio&tab=2"

load_dotenv()

user = os.environ.get('user')
password = os.environ.get('password')

driver = os.environ.get('driver')
server = os.environ.get('server')
database = os.environ.get('database')
uid = os.environ.get('uid')
pwd = os.environ.get('pwd')

def main():
    browser = configBrowser()
    responseLogin = siteLogin(browser, url,user,password, pageForm)
    formatedData = bringColuns(responseLogin)

    con = connection()
    executeProc(formatedData, con)

def getDbDriver():
    drivers = [item for item in pyodbc.drivers()]
    driver = drivers[-1]
    return driver

def configBrowser():
    browser = mechanize.Browser()

    # browser.set_handle_equiv(True)
    # browser.set_handle_gzip(False)
    # browser.set_handle_redirect(True)
    # browser.set_handle_referer(True)
    browser.set_handle_robots(False)
    # browser.set_handle_refresh(False)

    cookies = mechanize.CookieJar()
    browser.set_cookiejar(cookies)

    browser.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.7 '
    '(KHTML, like Gecko) Chrome/7.0.517.41 Safari/534.7')]

    return browser


def connection():
        return pyodbc.connect(
            driver = getDbDriver(),
            server = server,
            database = database,
            uid = uid,
            pwd = pwd
        )


def executeProc(procParams, con):
    try:
        cursorTest = con.cursor()
        cursorTest.execute("EXEC PROC_Processa_Parametros_Vulcanet ?", [procParams])
        con.commit()
        print("Dados Vulcanet inseridos com sucesso!! " + data_hora)
        print(procParams)
    except Exception as e:
        print(e)
    finally:
        con.close()


def siteLogin(site, loginLink, login, acess, page):
    site.open(loginLink)

    site.select_form(nr=0)

    site.form["LoginForm[username]"] = login
    site.form["LoginForm[password]"] = acess
    site.submit()

    response = site.open(page)
    parsedResponse = BeautifulSoup(response, "html.parser")

    return parsedResponse


def bringColuns(parsed):
    names = []
    calls = []
    time = []

    elements = parsed.select(".grid-view > table > tbody > tr > td")
    parsedElements = [x.text for x in elements]

    for x in range(len(parsedElements)):
        if len(parsedElements[x].split()) == 2:
            try:
                parsedElements[x].index('$')
                pass    
            except:
                names.append(parsedElements[x])
        elif len(parsedElements[x].split()) == 1:
            try:
                float(parsedElements[x])
                calls.append(parsedElements[x])
                time.append(parsedElements[x + 1])  
            except:
                pass
        else:
            pass

    return formatColuns(names,calls,timeToSec(time))
  

def formatColuns(vetName, vetCall, vetTime):
    readyColuns = []
    tam = 0

    while tam < len(vetName):
        readyColuns.append([vetName[tam], vetCall[tam], str(vetTime[tam])])
        tam += 1

    return readyColuns


def timeToSec(times):
    arraySec = []

    for t in range(len(times)):
        timeSec = 0
        timeArray = times[t].split(':')

        for x in range(len(timeArray)):
            if x == (len(timeArray) - 1):
                timeSec = timeSec + int(timeArray[x])
            else:
                timeSec = (timeSec + int(timeArray[x])) * 60 
        arraySec.append(timeSec)

    return arraySec


if __name__ == "__main__":
    main()

