FROM apache/spark:3.4.0-python3
LABEL mainatiner="Alfio Cardillo"

ENV HADOOP_VERSION=hadoop3
ENV SPARK_DIR=/opt/spark
ENV PATH $SPARK_DIR/bin:$PATH

RUN pip install pyspark elasticsearch numpy

COPY code/* ${SPARK_DIR}/
COPY mlmodels ${SPARK_DIR}/

ENTRYPOINT [ "/opt/spark/bin/spark-submit" , "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.elasticsearch:elasticsearch-spark-30_2.12:8.7.1", "/opt/spark/stock.py"]


