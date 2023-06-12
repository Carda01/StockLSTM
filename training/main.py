from pyspark import SparkContext
from pyspark.sql import SparkSession
import pyspark.sql.types as tp
from pyspark.sql.dataframe import DataFrame
from pyspark.ml.regression import LinearRegression
from pyspark.sql.functions import unix_timestamp
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.evaluation import RegressionEvaluator

SYMBOLS = ["AAPL", "GOOGL", "MSFT"]

sc = SparkContext(appName="Pythontry")
spark = SparkSession(sc)
sc.setLogLevel("WARN")

schema = tp.StructType([
    tp.StructField(name= 'time', dataType=tp.StringType(), nullable= True),
    tp.StructField(name= 'open', dataType= tp.DoubleType(), nullable= True),
    tp.StructField(name= 'high', dataType= tp.DoubleType(), nullable= True),
    tp.StructField(name= 'low', dataType= tp.DoubleType(), nullable= True),
    tp.StructField(name= 'close', dataType= tp.DoubleType(), nullable= True),
    tp.StructField(name= 'volume', dataType= tp.IntegerType(), nullable= True),
    ])

for symbol in SYMBOLS:
    print("Reading training set...")
# read the dataset  
    df = spark.read.csv(f'{symbol}_history.csv',
                              schema=schema,
                              header=True,
                              sep=',')

    df = df.withColumn("time", unix_timestamp(df["time"], "yyyy-MM-dd HH:mm:ss"))
    print("Done.")


    windowSpec = Window.orderBy("time")  # Specify the column to define the order

    valueFromAnotherRow = F.lag(df["close"]).over(windowSpec)

    newdf = df.withColumn("next_close", valueFromAnotherRow)

    data = newdf.select("open", "high", "low", "close", "next_close")

    data = data.select(*(data[c].cast("double").alias(c) for c in data.columns))

    assembler = VectorAssembler(inputCols=["open", "high", "low", "close"], outputCol="features")

    data = assembler.transform(data).select("features", "next_close")
    data = data.na.drop()

    (trainingData, testData) = data.randomSplit([0.8, 0.2])


    rf = LinearRegression(maxIter=10, regParam=0.3, elasticNetParam=0.8, labelCol="next_close")

    model = rf.fit(trainingData)

    predictions = model.transform(testData)

    predictions.select("prediction", "next_close", "features").show(5)

    evaluator = RegressionEvaluator(
        labelCol="next_close", predictionCol="prediction", metricName="rmse")

    rmse = evaluator.evaluate(predictions)
    print("Root Mean Squared Error (RMSE) on test data = %g" % rmse)

    model.save(f"../spark/mlmodels/{symbol}model")
