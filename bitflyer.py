import requests
import time
from time import sleep

url = "https://api.bitflyer.com/v1/ticker?product_code=BTC_USD"

while True:
    sleep(0) #1 or less is right number
    response = requests.request("GET", url)
    print(response.text)
