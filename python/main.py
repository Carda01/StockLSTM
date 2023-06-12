"""
We want to keep track of 3 symbols:
    Microsoft (MSFT)
    Apple (AAPL)
    Google (GOOGL)
"""
from utilities import download_jsons, create_timeline, sendData

def main():
    SYMBOLS = ["MSFT", "AAPL", "GOOGL"]
    jsons = download_jsons(SYMBOLS)
    timeline = create_timeline(jsons, SYMBOLS)
    sendData(timeline)

if __name__ == "__main__":
    main()
