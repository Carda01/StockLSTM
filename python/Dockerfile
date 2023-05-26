FROM python:3.11.3-slim
LABEL maintainer="Alfio Cardillo"

ADD parser.py main.py
ADD jsons/ ./jsons/

#Packages
RUN pip install requests 

CMD ["python", "./main.py"]

