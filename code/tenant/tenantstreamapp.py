from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from pyspark.sql.functions import *

TOPIC = "tenant"

spark = SparkSession \
    .builder \
    .appName("streamingApp") \
    .config("spark.cassandra.connection.host", "localhost") \
    .config("spark.cassandra.connection.port", "9042") \
    .config("spark.cassandra.auth.username", "k8ssandra-superuser") \
    .config("spark.cassandra.auth.password", "czFO48OolLkkmhoouAGe") \
    .config("spark.sql.extensions", "com.datastax.spark.connector.CassandraSparkExtensions") \
    .config("spark.sql.catalog.lh", "com.datastax.spark.connector.datasource.CassandraCatalog") \
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

rows = spark \
  .readStream \
  .format("kafka") \
  .option("kafka.bootstrap.servers", "localhost:29092") \
  .option("subscribe", TOPIC) \
  .load()

# Turn Kafka Message Values to normal Dataframe
df = rows \
  .selectExpr("CAST(value AS STRING)") \
  .withColumn("jsonData",from_json(col("value"),schema)) \
    .select("jsonData.*")

df = df.withColumn("review_date", to_timestamp("review_date"))

groupDF = df.select("product_id", "star_rating", "helpful_votes", "total_votes", "review_date") \
        .withWatermark("review_date", "2 days") \
        .groupBy(
          "product_id", 
          window("review_date", "1 day")
        ) \
        .agg( 
          avg("star_rating").alias("avg_star_rating"),
          sum("helpful_votes").alias("sum_helpful_votes"),
          sum("total_votes").alias("sum_total_votes"),
          count("star_rating").alias("number_of_reviews")
        )

resultDF = groupDF.withColumn("review_date", to_date(groupDF.window.start)).drop("window")

resultDF.printSchema()

resultDF.writeStream \
  .format("org.apache.spark.sql.cassandra") \
  .option("keyspace", "mysimbdp") \
  .option("table", "aggregated_reviews") \
  .option("checkpointLocation", "./checkpoint") \
  .outputMode("append") \
  .start() \
  .awaitTermination()
