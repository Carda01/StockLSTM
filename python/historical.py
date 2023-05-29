import csv
import time
import os
import requests
import pandas as pd

SYMBOLS = ["MSFT", "AAPL", "GOOGL"]

for SYMBOL in SYMBOLS:
    df = pd.DataFrame()
    for year in range(1,3):
        for month in range(1, 13):
            print(f"{SYMBOL}-year{year}-month{month}")
            parameters_value = {
                    "function": "TIME_SERIES_INTRADAY_EXTENDED",
                    "symbol": SYMBOL,
                    "apikey": os.environ.get("API_KEY"),
                    "interval": "5min",
                    "slice": f"year{year}month{month}"
                    }

            url_parameters = []

            for item in parameters_value.items():
                url_parameters.append(f"{item[0]}={item[1]}")

            url = f"https://www.alphavantage.co/query?"
            for parameter in url_parameters:
                url += f"{parameter}&"

            url = url[:-1]
            
            df = pd.concat([df, pd.read_csv(url)], ignore_index=True)
            print(df)
            time.sleep(15)

    df.to_csv(f"{SYMBOL}_history.csv", index=False)
