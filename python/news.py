import requests, os, json
import functools

SYMBOLS = ["MSFT", "AAPL", "GOOGL"]

parameters_value = {
        "function": "NEWS_SENTIMENT",
        "tickers": functools.reduce(lambda a, b: a + ',' + b, SYMBOLS),
        "apikey": os.environ.get("API_KEY"),
        "timeto": "20230524T1955"
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

with open(f"newsTotal.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

#print(data)
