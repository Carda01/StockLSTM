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


# I/O config

ELASTIC_HOST="http://elasticsearch:9200"
ELASTIC_INDEX="stocks"
KAFKA_SERVER="broker1:9092"
KAFKA_TOPIC = "stock_prices"

ES_MAPPING = {
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

def create_elastic_index():
    es = Elasticsearch(hosts=ELASTIC_HOST)

    response = es.indices.create(
        index=ELASTIC_INDEX,
        body=ES_MAPPING,
        ignore=400
    )

    if 'acknowledged' in response:
        if response['acknowledged'] == True:
            print ("INDEX MAPPING SUCCESS FOR INDEX:", response['index'])


def get_input_schema():
    return tp.StructType([
        tp.StructField(name= '@timestamp', dataType= tp.DoubleType(), nullable= False), 
        tp.StructField(name= 'open', dataType= tp.StringType(),  nullable= False),
        tp.StructField(name= 'high', dataType= tp.StringType(),  nullable= False),
        tp.StructField(name= 'low', dataType= tp.StringType(),  nullable= False),
        tp.StructField(name= 'close', dataType= tp.StringType(),  nullable= False),
        tp.StructField(name= 'volume', dataType= tp.StringType(),  nullable= False),
        tp.StructField(name= 'symbol', dataType= tp.StringType(),  nullable=False),
    ])


def get_input_stream(spark):
    return spark \
      .readStream \
      .format("kafka") \
      .option("kafka.bootstrap.servers", KAFKA_SERVER) \
      .option("subscribe", KAFKA_TOPIC) \
      .load()


def json_to_dataframe(input):
    input_df = input.selectExpr("CAST(value AS STRING)") \
        .select(from_json("value", get_input_schema()).alias("data")) \
        .select("data.*")

    return input_df.withColumn("open", input_df.open.cast("double")) \
           .withColumn("high", input_df.high.cast("double")) \
           .withColumn("low", input_df.low.cast("double")) \
           .withColumn("close", input_df.close.cast("double")) \
           .withColumn("volume", input_df.volume.cast("int")) \
           .withColumn("@timestamp", col("@timestamp").cast(tp.TimestampType()))


def process_streaming_data(streaming_df, model):
    assembler = VectorAssembler(inputCols=["open", "high", "low", "close"], outputCol="features")
    assembled_data = assembler.transform(streaming_df)
    predictions = model.transform(assembled_data)
    return predictions

def add_prediction_column(input_df, models):
    APPLE_MODEL = models[0]
    GOOGLE_MODEL = models[1]
    MICROSOFT_MODEL = models[2]

    apple = input_df.filter(input_df.symbol == "AAPL")
    google = input_df.filter(input_df.symbol == "GOOGL")
    microsoft = input_df.filter(input_df.symbol == "MSFT")

    apple = process_streaming_data(apple, APPLE_MODEL)
    microsoft = process_streaming_data(microsoft, MICROSOFT_MODEL)
    google = process_streaming_data(google, GOOGLE_MODEL)

    df = apple.union(google)
    df = df.union(microsoft)

    return df


def add_format_timestamps(input_df):
    input_df = input_df.withColumn("timestamp", current_timestamp()) 
    input_df = input_df.withColumn("original_timestamp", date_format(input_df.original_timestamp,  "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"))
    input_df = input_df.withColumn("@timestamp", date_format(input_df.timestamp,  "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"))
    input_df = input_df.drop("timestamp")

    return input_df


def write_to_elastic(output_df):
    output_df.writeStream \
      .option("checkpointLocation", "/save/location") \
      .format("es") \
      .start(ELASTIC_INDEX) \
      .awaitTermination()


def add_previous_prediction(input_df):
    predictions = input_df.select("original_timestamp", "prediction", "symbol")
    input_df.drop("prediction")
    predictions = predictions.withColumn("original_timestamp", col("original_timestamp") + expr("INTERVAL 5 minutes"))


    input_df = input_df.withWatermark("original_timestamp", "10 minutes")
    predictions = predictions.withWatermark("original_timestamp", "10 minutes")

    cond = [input_df.symbol == predictions.symbol,
            input_df.original_timestamp == predictions.original_timestamp]

    input_df = input_df.alias("input_df").join(predictions.alias("predictions"), cond, "leftOuter") \
           .select(col("input_df.original_timestamp"), col("input_df.close"), col("input_df.symbol"), col("predictions.prediction"))

    return input_df



def get_spark_session():
    sparkConf = SparkConf() \
                .set("es.nodes", "elasticsearch") \
                .set("es.port", "9200")

    sc = SparkContext(appName="StockRegression", conf=sparkConf)
    spark = SparkSession(sc)
    sc.setLogLevel("WARN")
    return spark


def load_models():
    APPLE_MODEL = LinearRegressionModel.load("/opt/spark/AAPLmodel")
    GOOGLE_MODEL = LinearRegressionModel.load("/opt/spark/GOOGLmodel")
    MICROSOFT_MODEL = LinearRegressionModel.load("/opt/spark/MSFTmodel")
    return [APPLE_MODEL, GOOGLE_MODEL, MICROSOFT_MODEL]
