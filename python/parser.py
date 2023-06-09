import json, requests, os
from time import sleep

SECONDS = os.environ.get("SECONDS")
if SECONDS is None:
    SECONDS = 1
else:
    SECONDS = int(SECONDS)

url = "http://10.0.100.10:9880"

def stock_time_parser(date : str) -> int:
    return int(date[11:-3].replace(":", ""))

SYMBOLS = ["AAPL", "MSFT", "GOOGL"]
timeline = {}

for SYMBOL in SYMBOLS:
    path = f"jsons/{SYMBOL}.json"
    with open(path, 'r') as file:
        data = json.load(file)

    data = data["Time Series (5min)"]
    # print(json.dumps(data, indent=1))

    for entry in data.items():
        formatted_entry = entry[1]
        formatted_entry["symbol"] = f"{SYMBOL}"
        formatted_entry["event_time"] = entry[0]
        time = stock_time_parser(entry[0])
        if time in timeline:
            timeline[time].append(formatted_entry)
        else:
            timeline[time] = [formatted_entry]

timeline = dict(sorted(timeline.items(), key= lambda item: item[0]))

TIMELINE_LIST = list(timeline.keys())
min = TIMELINE_LIST[0]
max = TIMELINE_LIST[-1]

hour_step = int(str(min)[:2])
minute_step = int(str(min)[2:])
time_step = min
while time_step <= max:
    time_step = int(str(hour_step) + f"{minute_step:02d}")
    print(time_step)
    sleep(SECONDS)
    if time_step in TIMELINE_LIST:
        requests.post(url, json=timeline[time_step])
    minute_step += 1
    
    if minute_step == 60:
        minute_step = 0
        hour_step += 1
