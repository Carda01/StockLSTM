# StockLSTM
A simulated-real-time stock predictor inside an event-driven data pipeline.

## Instructions
To run create a file called api.env where you put your API key for alpha vantage
and then compose up with docker
```
echo API_KEY=<your-key> > api.env
docker compose up
```
