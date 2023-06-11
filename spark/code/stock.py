from pyspark.conf import SparkConf
from pyspark import SparkContext

# Pyspark Sql

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, date_format, expr
import pyspark.sql.types as tp

# Spark MLlib
from pyspark.ml.regression import LinearRegressionModel
from pyspark.ml.feature import VectorAssembler

# Elastic Search
from elasticsearch import Elasticsearch

elastic_host="http://elasticsearch:9200"
elastic_index="stocks"
kafkaServer="broker1:9092"
topic = "stock_prices"

es_mapping = {
    "mappings": {
        "properties": 
            {
                "original_timestamp": {"type": "date", "format": "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"},
                "close": {"type": "double"},
                "symbol": {"type": "text"},
                "prediction": {"type": "double"},
                "@timestamp": {"type": "date", "format": "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"}
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

stockKafka = tp.StructType([
    tp.StructField(name= '@timestamp', dataType= tp.DoubleType(), nullable= False), 
    tp.StructField(name= 'open', dataType= tp.StringType(),  nullable= False),
    tp.StructField(name= 'high', dataType= tp.StringType(),  nullable= False),
    tp.StructField(name= 'low', dataType= tp.StringType(),  nullable= False),
    tp.StructField(name= 'close', dataType= tp.StringType(),  nullable= False),
    tp.StructField(name= 'volume', dataType= tp.StringType(),  nullable= False),
    tp.StructField(name= 'symbol', dataType= tp.StringType(),  nullable=False),
])


sparkConf = SparkConf() \
            .set("es.nodes", "elasticsearch") \
            .set("es.port", "9200")

sc = SparkContext(appName="StockRegression", conf=sparkConf)
spark = SparkSession(sc)
sc.setLogLevel("WARN")

# Streaming Query

input_df = spark \
  .readStream \
  .format("kafka") \
  .option("kafka.bootstrap.servers", kafkaServer) \
  .option("subscribe", topic) \
  .load()

input_df = input_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json("value", stockKafka).alias("data")) \
    .select("data.*")

input_df = input_df.withColumn("open", input_df.open.cast("double")) \
       .withColumn("high", input_df.high.cast("double")) \
       .withColumn("low", input_df.low.cast("double")) \
       .withColumn("close", input_df.close.cast("double")) \
       .withColumn("volume", input_df.volume.cast("int")) \
       .withColumn("@timestamp", col("@timestamp").cast(tp.TimestampType()))

model = LinearRegressionModel.load("/opt/spark/model")

def process_streaming_data(streaming_df):
    assembler = VectorAssembler(inputCols=["open", "high", "low", "close"], outputCol="features")
    assembled_data = assembler.transform(streaming_df)

    predictions = model.transform(assembled_data)

    return predictions

df = input_df.transform(process_streaming_data) \
                .select("@timestamp", "close", "symbol", "prediction")

df = df.withColumnRenamed("@timestamp", "original_timestamp")

predictions = df.select("original_timestamp", "prediction", "symbol")
df.drop("prediction")
predictions = predictions.withColumn("original_timestamp", col("original_timestamp") + expr("INTERVAL 5 minutes"))


df = df.withWatermark("original_timestamp", "10 minutes")
predictions = predictions.withWatermark("original_timestamp", "10 minutes")

cond = [df.symbol == predictions.symbol,
        df.original_timestamp == predictions.original_timestamp]

df = df.alias("df").join(predictions.alias("predictions"), cond, "leftOuter") \
       .select(col("df.original_timestamp"), col("df.close"), col("df.symbol"), col("predictions.prediction"))

df = df.withColumn("timestamp", current_timestamp()) 
df = df.withColumn("original_timestamp", date_format(df.original_timestamp,  "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"))
df = df.withColumn("@timestamp", date_format(df.timestamp,  "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"))
df = df.drop("timestamp")

apple = df.filter(df.symbol == "AAPL")
google = df.filter(df.symbol == "GOOGL")
microsoft = df.filter(df.symbol == "MSFT")

da = apple.union(google)
da = da.union(microsoft)

da.writeStream \
  .option("checkpointLocation", "/save/location") \
  .format("es") \
  .start(elastic_index) \
  .awaitTermination()
