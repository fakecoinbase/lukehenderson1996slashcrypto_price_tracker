#Luke Henderson
#Version 1.0
#Solely for BaseFEX use
import requests, json
import time
from time import sleep, localtime, strftime
import sys
import os
from parse import * #pip install parse (or pip3 install parse)
#from basefex api
# from datetime import datetime # don't use, just use time.time()
# import hashlib
# import hmac
# from urllib.parse import urlparse
# import json
#from https://www.jokecamp.com/blog/examples-of-creating-base64-hashes-using-hmac-sha256-in-different-languages/#python3
import hashlib
import hmac
import base64
#for logging
from logger_auto_trader import *

#make text look unique
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



#POST order buy/sell
def placeOrder(size, type, side):
    http_method = 'POST'
    path = '/orders'
    url = 'https://api.basefex.com' + path
    timestamp = time.time()
    expires = int(round(timestamp) + 5)
    # data = {
    #     "size": 5,
    #     "symbol": "BTCUSD",
    #     "type": "MARKET",
    #     "side": "BUY"
    #     }
    data = {
        "size": size,
        "symbol": "BTCUSD",
        "type": type,
        "side": side
        }
    logDataObj = logData()
    logDataObj.request_type = side
    logDataObj = execute_request(http_method, url, path, expires, data, logDataObj)
    print(bcolors.OKBLUE  + side + " order executed" + bcolors.ENDC)
    upLogs(logDataObj)
    return logDataObj

#GET last price
def getLastPrice():
    http_method = 'GET'
    path = '/depth@BTCUSD/snapshot'
    url = 'https://api.basefex.com' + path
    timestamp = time.time()
    expires = int(round(timestamp) + 5)
    data = '' # empty request body
    logDataObj = logData()
    logDataObj.request_type = "getLastPrice"
    logDataObj = execute_request(http_method, url, path, expires, data, logDataObj)
    logDataObj.lastBaseFEX = getPriceFloat(logDataObj.serverResponseJSON, 'lastPrice')
    # print(bcolors.ENDC  + "Last price: " + str(logDataObj.lastBaseFEX) + bcolors.ENDC)
    upLogs(logDataObj)
    return logDataObj

#GET account info
def getAccountInfo():
    http_method = 'GET'
    path = '/accounts'
    url = 'https://api.basefex.com' + path
    timestamp = time.time()
    expires = int(round(timestamp) + 5)
    data = '' # empty request body
    logDataObj = logData()
    logDataObj.request_type = "getAccountInfo"
    logDataObj = execute_request(http_method, url, path, expires, data, logDataObj)
    logDataObj.positionContracts = json.loads(logDataObj.serverResponseJSON.text)[0]['positions'][4]['size'] #BTC position
    print(bcolors.OKBLUE  + "Number of position contracts: " + str(logDataObj.positionContracts) + bcolors.ENDC)
    upLogs(logDataObj)
    return logDataObj

#assumes static apiSecret, apiKey
def execute_request(http_method, url, path, expires, data, logDataObj):
    #groom data
    if not len(data) == 0:
        strData = json.dumps(data)
    else:
        strData = data

    #display request
    tokenString = http_method + path + str(expires) + strData


    #create signature
    signature = generate_signature(apiSecret, http_method, path, expires, strData)
    auth_token = signature
    # print("String: " + tokenString)
    # print("signature: " + signature)
    #create header
    hed = {'api-expires':str(expires),'api-key':apiKey,'api-signature':str(auth_token)}

    #fulfill server request
    if http_method == 'GET':
        response = requests.get(url, headers=hed)
    elif http_method == 'POST':
        response = requests.post(url, headers=hed, json=data)
    parsedJSON = json.loads(response.text) #whole JSON object
    # print(bcolors.OKBLUE  + "Server response: " + bcolors.ENDC)
    # print(json.dumps(parsedJSON, indent=4, sort_keys=True))
    #log handling
    logDataObj.timestamp = time.time()
    logDataObj.string = tokenString
    logDataObj.signature = signature
    logDataObj.server_response = json.dumps(parsedJSON, indent=4, sort_keys=True)
    logDataObj.serverResponseJSON = response
    return logDataObj

# The algorithm is: hex(HMAC_SHA256(secret, http_method + path + expires + data))
# Upper-cased http_method, relative request path, unix timestamp expires.
# data is json string
def generate_signature(apiSecret, http_method, path, expires, strData):
    message = bytes(http_method + path + str(expires) + strData, 'utf-8')
    secret = bytes(apiSecret, 'utf-8')
    signature = hmac.new(secret, message, digestmod=hashlib.sha256).digest().hex()
    return signature


# takes JSON object priceResponse and returns keyed last price
def getPriceFloat(*args): #num of args will be 2 to 5 -> 0:JSON object, 1:Key0, 2:[Key1], 3:[Key2], 4:[Key3]
    try:
        if len(args) == 2:
            priceFloat = float(json.loads(args[0].text)[args[1]])
        elif len(args) == 3:
            priceFloat = float(json.loads(args[0].text)[args[1]][args[2]])
        elif len(args) == 4:
            priceFloat = float(json.loads(args[0].text)[args[1]][args[2]][args[3]])
        else:
            priceFloat = float(json.loads(args[0].text)[args[1]][args[2]][args[3]][args[4]])
        return priceFloat
    except KeyboardInterrupt:
        exit()
    except:
        print(bcolors.FAIL  + "Error: getPriceFloat error" + bcolors.ENDC)
        print(sys.exc_info())
        exit()

def verifyContracts(num):
    logDataObj = getAccountInfo()
    positionContracts = logDataObj.positionContracts
    if positionContracts != num:
        if positionContracts > num:
            logDataObj = placeOrder(positionContracts, "MARKET", "SELL")
        if positionContracts < num:
            logDataObj = placeOrder(-positionContracts, "MARKET", "BUY")


#init code
if os.path.exists('keys/keys.xml'): #file exists
    #read file for API keys
    keysFile = open("keys/keys.xml", "r")
    keysFileCont =keysFile.read()
    xmlKeys = search("<keys>{}</keys>", keysFileCont)[0]
    xmlBFKeys = search("<baseFEX>{}</baseFEX>", xmlKeys)[0]
    apiKey = search("<API_key>{}</API_key>", xmlBFKeys)[0] # id of api key
    apiSecret = search("<private_key>{}</private_key>", xmlBFKeys)[0] # api secret
    keysFile.close()
else:
    print(bcolors.FAIL  + "Error: API keys file does not exist" + bcolors.ENDC)

initLogs()



#main loop
while True:

    verifyContracts(0)
    #now contracts==0


    logDataObj = placeOrder(5, "MARKET", "BUY")
    verifyContracts(5)
    logDataObj = getLastPrice()
    buyPrice = logDataObj.lastBaseFEX

    trigger = False

    while trigger==False:
        sleep(2)
        logDataObj = getLastPrice()
        lastPrice = logDataObj.lastBaseFEX
        if lastPrice/buyPrice > 100.70/100:
            trigger = True
            print("lastPrice/buyPrice: " + str(lastPrice/buyPrice*100) + '%')
            logDataObj = logData()
            logDataObj.timestamp = time.time()
            logDataObj.request_type = "nonrequest, trigger"
            logDataObj.trigger = "greater"
            logDataObj.last_over_buy_ratio = str(lastPrice/buyPrice*100) + '%'
            upLogs(logDataObj)
        if lastPrice/buyPrice < 99.80/100:
            trigger = True
            print("lastPrice/buyPrice: " + str(lastPrice/buyPrice*100) + '%')
            logDataObj = logData()
            logDataObj.timestamp = time.time()
            logDataObj.request_type = "nonrequest, trigger"
            logDataObj.trigger = "lesser"
            logDataObj.last_over_buy_ratio = str(lastPrice/buyPrice*100) + '%'
            upLogs(logDataObj)


    logDataObj = placeOrder(5, "MARKET", "SELL")
    verifyContracts(0)

    sleep(30)




    # #get last price
    # logDataObj = getLastPrice()
    # # get num of contracts
    # logDataObj = getAccountInfo()



















#end
