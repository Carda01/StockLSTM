# FROM python:3.11.3-slim
FROM python:alpine3.18
LABEL maintainer="Alfio Cardillo"

#Packages
RUN pip install requests 

ADD main.py main.py

CMD ["python", "./main.py"]

