FROM python:slim
ENV API_KEY "demo"

ADD main.py .

#Packages
RUN pip install requests

CMD ["python", "./main.py"]

