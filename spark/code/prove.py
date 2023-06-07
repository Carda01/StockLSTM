from __future__ import print_function
from os import truncate

import time
import sys

from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.streaming import StreamingContext
from pyspark.sql.functions import from_json, col
import pyspark.sql.types as tp
from pyspark.sql.dataframe import DataFrame
from pyspark.ml.regression import LinearRegressionModel
from pyspark.ml.feature import VectorAssembler

# Elastic Search
from elasticsearch import Elasticsearch
elastic_host="http://elasticsearch:9200"
elastic_index="taptweet"

es_mapping = {
    "mappings": {
        "properties": 
            {
                "created_at": {"type": "date","format": "yyyy-MM-ddTHH:mm:ss.SSSZ"},
                "content": {"type": "text","fielddata": True}
            }
    }
}

es = Elasticsearch(hosts=elastic_host)

# make an API call to the Elasticsearch cluster
# and have it return a response:
response = es.indices.create(
    index=elastic_index,
    body=es_mapping,
    ignore=400 # ignore 400 already exists code
)

if 'acknowledged' in response:
    if response['acknowledged'] == True:
        print ("INDEX MAPPING SUCCESS FOR INDEX:", response['index'])

# Define Training Set Structure
tweetKafka = tp.StructType([
    tp.StructField(name= '@timestamp', dataType= tp.LongType(),  nullable= True),
    tp.StructField(name= 'close', dataType= tp.DoubleType(),  nullable= True),
    tp.StructField(name= 'symbol', dataType= tp.StringType(),  nullable= True)
])

def elaborate(batch_df: DataFrame, batch_id: int):
  batch_df.show(truncate=False)

sc = SparkContext(appName="PythonStructuredStreamsKafka")
spark = SparkSession(sc)
sc.setLogLevel("WARN")

stockKafka = tp.StructType([
    tp.StructField(name= '@timestamp', dataType= tp.DoubleType(), nullable= False), 
    tp.StructField(name= 'open', dataType= tp.StringType(),  nullable= False),
    tp.StructField(name= 'high', dataType= tp.StringType(),  nullable= False),
    tp.StructField(name= 'low', dataType= tp.StringType(),  nullable= False),
    tp.StructField(name= 'close', dataType= tp.StringType(),  nullable= False),
    tp.StructField(name= 'volume', dataType= tp.StringType(),  nullable= False),
    tp.StructField(name= 'symbol', dataType= tp.StringType(),  nullable=False),
])

kafkaServer="broker1:9092"
topic = "stock_prices"

# Streaming Query

df = spark \
  .readStream \
  .format("kafka") \
  .option("kafka.bootstrap.servers", kafkaServer) \
  .option("subscribe", topic) \
  .load()

df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json("value", stockKafka).alias("data")) \
    .select("data.*")

df = df.withColumn("open", df.open.cast("double")) \
       .withColumn("high", df.high.cast("double")) \
       .withColumn("low", df.low.cast("double")) \
       .withColumn("close", df.close.cast("double")) \
       .withColumn("volume", df.volume.cast("int")) \
       .withColumn("@timestamp", col("@timestamp").cast(tp.LongType()))

model = LinearRegressionModel.load("/opt/tap/mlmodels/model")

def process_streaming_data(streaming_df):
    assembler = VectorAssembler(inputCols=["open", "high", "low", "close"], outputCol="features")
    assembled_data = assembler.transform(streaming_df)

    predictions = model.transform(assembled_data)

    return predictions

processed_data = df.transform(process_streaming_data) \
        .select("@timestamp", "close", "symbol", "prediction")
# df.writeStream \
#   .foreachBatch(elaborate) \
#   .start() \
#   .awaitTermination()

# processed_data.writeStream \
#   .format("console") \
#   .start() \
#   .awaitTermination()

processed_data.writeStream \
        .option("checkpointLocation", "/save/location") \
        .format("es") \
        .start(elastic_index) \
        .awaitTermination()
