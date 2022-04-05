from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from pyspark.sql.functions import *

spark = SparkSession \
    .builder \
    .appName("streamingApp") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

schema = StructType([ \
    StructField("marketplace",StringType(),True), \
    StructField("customer_id",StringType(),True), \
    StructField("review_id",StringType(),True), \
    StructField("product_id",StringType(),True), \
    StructField("product_parent", StringType(), True), \
    StructField("product_title", StringType(), True), \
    StructField("product_category", StringType(), True), \
    StructField("star_rating", IntegerType(), True), \
    StructField("helpful_votes", IntegerType(), True), \
    StructField("total_votes", IntegerType(), True), \
    StructField("vine", StringType(), True), \
    StructField("verified_purchase", StringType(), True), \
    StructField("review_headline", StringType(), True), \
    StructField("review_body", StringType(), True), \
    StructField("review_date", StringType(), True)
  ])

df = spark \
    .readStream \
    .schema(schema) \
    .format("csv") \
    .option("delimiter", "\t") \
    .load("./staging")

df.printSchema()

groupDF = df.select("product_id", "star_rating", "helpful_votes", "total_votes", "review_date") \
        .groupBy("product_id", "review_date") \
        .agg( 
          avg("star_rating").alias("avg_star_rating"),
          sum("helpful_votes").alias("sum_helpful_votes"),
          sum("total_votes").alias("sum_total_votes"),
          count("star_rating").alias("number_of_reviews")
        ) \
        # .where("number_of_reviews > 1")

groupDF.printSchema()

groupDF.writeStream \
  .format("console") \
  .outputMode("update") \
  .start() \
  .awaitTermination() 

