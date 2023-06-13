from utilities import *
def main():
    create_elastic_index()
    spark = get_spark_session()
    models = load_models()
    input_df = get_input_stream(spark)
    input_df = json_to_dataframe(input_df)
    df = add_prediction_column(input_df, models)\
            .select("@timestamp", "close", "symbol", "prediction")

    df = df.withColumnRenamed("@timestamp", "original_timestamp")
    df = add_previous_prediction(df)
    df = add_format_timestamps(df)
    write_to_elastic(df)
# Models

main()
