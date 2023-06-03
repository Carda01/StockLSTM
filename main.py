"""
We want to keep track of 3 symbols:
    Microsoft (MSFT)
    Apple (AAPL)
    Google (GOOGL)
"""
import requests, os, json

SYMBOLS = ["MSFT", "AAPL", "GOOGL"]



for SYMBOL in SYMBOLS:
    parameters_value = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": SYMBOL,
            "apikey": "Z7YNCEIQHZPQACP3",
            "interval": "5min"
            }

    url_parameters = []

    for item in parameters_value.items():
        url_parameters.append(f"{item[0]}={item[1]}")

    url = f"https://www.alphavantage.co/query?"
    for parameter in url_parameters:
        url += f"{parameter}&"

    url = url[:-1]
    print(url)

    r = requests.get(url)
    data = r.json()
    # json_formatted_str = json.dumps(data, indent=2)

    with open(f"{SYMBOL}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    #print(data)
