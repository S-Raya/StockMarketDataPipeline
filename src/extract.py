import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime
import argparse
from utils import log_to_db

parser = argparse.ArgumentParser()
parser.add_argument("--daily", help="fetch daily time series data", action="store_true")
parser.add_argument("--overview", help="fetch overview data", action="store_true")
args = parser.parse_args()

time = datetime.now().strftime("%Y_%m_%d_%H_%M")

load_dotenv()

api_key = os.getenv("API_KEY")
symbol = os.getenv("SYMBOL")
url = os.getenv("API_URL")
function1 = os.getenv("FUNCTION1")
function2 = os.getenv("FUNCTION2")

param1 = {
    "function": function1,
    "symbol": symbol,
    "apikey": api_key
}
param2 = {
    "function": function2,
    "symbol": symbol,
    "apikey": api_key
}

def fetch_data(url, param):
    try:
        r = requests.get(url, params=param)    
        r.raise_for_status()
        data = r.json()
        with open(f"data/raw/data_{param["function"]}_{time}.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        print("Requested URL:", r.url)
        nProcessed = len(data["Time Series (Daily)"]) if "Time Series (Daily)" in data else 1
        log_to_db("Extract data", symbol, "Success", nProcessed, 0, 0, None)

    except requests.exceptions.RequestException as error:
        log_to_db("Extract data", symbol, "Failed", 0, 0, 0, str(error))
        print(f"An error occurred while calling the API: {error}")   


if (args.overview and args.daily) or (not args.overview and not args.daily):
    fetch_data(url, param1)
    fetch_data(url, param2)
elif args.daily:
    fetch_data(url, param1)
elif args.overview:
    fetch_data(url, param2)



