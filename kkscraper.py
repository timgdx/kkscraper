#import requests
import signal
import cloudscraper
from prettytable import PrettyTable
import time
import json
import os
import datetime

##############
ANSI_SUPPORT = True
MIN_PRICE = 200
MAX_PRICE = 1000
TARGET_PRODUCTS = ["3080","3070 Ti","6800","4070 Ti"]
OPTIMAL_PRICE = [550,400,550,750]
OPTIMAL_ONLY = False
LOOP = 60*5 # 0 - run once; > 0 - run every X seconds
URL = "https://www.kuantokusta.pt"
TARGET_URL = "https://api.kuantokusta.pt/products?family_id=957&category_id=21&_=1675799440706&sort=3&price={0}-{1}&pag={2}"
##############

OPTIMAL_COLOR = "\033[38;5;35m"
MORE_COLOR = "\033[38;5;196m"
LESS_COLOR = "\033[38;5;40m"
REFURBISHED_COLOR = "\033[38;5;11m"
RESET_COLOR = "\033[0m"
HISTORY_FILENAME = "history.json"

def main():
    # exit gracefully
    signal.signal(signal.SIGINT, exitGracefully)
    signal.signal(signal.SIGTERM, exitGracefully)
    # history
    historyFile = None
    try:
        historyFile = open(HISTORY_FILENAME,"r+")
    except:
        historyFile = open(HISTORY_FILENAME,"w+")
    history = None
    try:
        history = json.load(historyFile)
    except:
        history = {}
    historyOld = dict(history)
    # scraper
    scraper = cloudscraper.create_scraper()
    pt = PrettyTable()
    pt.field_names = ["Price","Name","Link"]
    pt.align["Price"] = "r"
    while True:
        historyChanged = False
        currentPage = 1
        productsFound = 0
        products = []
        while True:
            data = None
            try:
                response = scraper.get(TARGET_URL.format(MIN_PRICE,MAX_PRICE,currentPage)).text
                data = json.loads(response)
                data = data["productsGroup"]
                if len(data["products"]) == 0:
                    break
            except:
                print("Something went wrong.")
                break
            productsFound += len(data["products"])
            for product in data["products"]:
                if any(x in product["name"] for x in TARGET_PRODUCTS):
                    price = float(product["priceMin"])
                    saveName = product["name"]
                    historyPrice = history.get(saveName)
                    # save to history
                    if historyPrice:
                        if price < historyPrice:
                            historyChanged = True
                            history[saveName] = price
                    else:
                        historyChanged = True
                        history[saveName] = price
                    # price delta - uses data from the program start
                    historyPriceOld = historyOld.get(saveName)
                    priceDeltaStr = ""
                    if historyPriceOld:
                        priceDelta = price-historyPriceOld
                        if priceDelta > 0:
                            priceDeltaStr = colorString(f"(+{priceDelta:.2f})",MORE_COLOR)
                        elif priceDelta < 0:
                            priceDeltaStr = colorString(f"({priceDelta:.2f})",LESS_COLOR)
                    #
                    if [price-OPTIMAL_PRICE[x] for x in range(len(TARGET_PRODUCTS)) if TARGET_PRODUCTS[x] in product["name"]][0] > 0:
                        if not OPTIMAL_ONLY:
                            products.append([priceDeltaStr+str(price),product["name"],link(URL+product["productUrl"],"Link")])
                    else: # optimal price
                        products.append([priceDeltaStr+colorString(str(price),OPTIMAL_COLOR),colorString(product["name"],OPTIMAL_COLOR),colorString(link(URL+product["productUrl"],"Link"),OPTIMAL_COLOR)])
                        print('\007') # sound alert
            currentPage += 1
        print(f"Filtered through {productsFound} products")
        for p in products:
            pt.add_row(p)
        print(pt)
        print("Last update:", datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
        # save history if changed
        if historyChanged:
            historyFile.seek(0)
            json.dump(history,historyFile,indent=4)
            historyChanged = False
        if LOOP > 0:
            pt.clear_rows()
            time.sleep(LOOP)
            os.system('cls' if os.name=='nt' else 'clear')
        else:
            break

def exitGracefully(x,y):
    exit()

def colorString(str,color):
    return color+str+RESET_COLOR if ANSI_SUPPORT else str

# https://stackoverflow.com/a/71309268
def link(url, label=None): # doesn't work with cmd
    if not ANSI_SUPPORT:
        return url
    if label is None: 
        label = url
    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST 
    #escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'
    #return escape_mask.format(parameters, uri, label)
    return f"\x1b]8;;{url}\a{label}\x1b]8;;\a"

main()