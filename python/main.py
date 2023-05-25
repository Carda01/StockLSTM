import requests, os

parameters_value = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": "IBM",
        "apikey": os.environ.get("API_KEY"),
        "interval": "5min"
        }

print(os.environ.get("API_KEY"))

url_parameters = []

for item in parameters_value.items():
    url_parameters.append(f"{item[0]}={item[1]}")

url = f"https://www.alphavantage.co/query?"
for parameter in url_parameters:
    url += f"{parameter}&"

url = url[:-1]
print(url)

# r = requests.get(url)
# data = r.json()

# print(data)
