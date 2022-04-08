# This is a deployment/installation guide

<br>
<br>

## Prerequisites:
- A running Cassandra cluster from Assignment 1, username and password for authentication to this cluster (follow instructions from Assignment 1)
- docker and docker-compose
- Running Apache Spark version 3.0.2 (Scala 2.12)

Some parts of the system require to be run by Python 3.8. To install dependencies, run

```
pip install -r code/tenant/requirements.txt
```

<br>
<br>

## Parts from Previous Assignments

There are some components available from previous assignments:

- `code/mysimpbdp/kafka-docker-compose.yml`: Docker compose file of Kafka Streaming Service
- `code/tenant/producer.py`: tenant's producer script that produce events to Kafka Streaming Service

<br>
<br>

## Deployment Steps

- Start Kafka Streaming Service, at `code/mysimpbdp` run:

```
docker-compose -f kafka-docker-compose.yml up 
```

<br>


- Create new table for Stream Analytics output in `mysimpbdp-coredms`, at `code/tenant` run:

```
./cqlsh-astra/bin/cqlsh  -u k8ssandra-superuser -p <PASSWORD> -f tenant-table.cql
```

Replace <PASSWORD> with Cassandra Authenticating user's password, (described in Assignment 1)

<br>

- Start tenant's producer, at `code/tenant/` run:

```
python producer.py
```

From this file, you can also change `TOPIC` and `MESSAGE_SPEED` at the head of the file.

<br>

- Start Spark Stream Analytics, at `code/tenant/` run:

```
spark-submit  \
--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.2 \
--packages com.datastax.spark:spark-cassandra-connector_2.12:3.0.1 \
--conf spark.sql.extensions=com.datastax.spark.connector.CassandraSparkExtensions \
tenantstreamapp.py
```

At the head of `tenantstreamapp.py` file, 

```
TOPIC = "tenant"

spark = SparkSession \
    .builder \
    .appName("streamingApp") \
    .config("spark.cassandra.connection.host", "localhost") \
    .config("spark.cassandra.connection.port", "9042") \
    .config("spark.cassandra.auth.username", "k8ssandra-superuser") \
    .config("spark.cassandra.auth.password", "<PASSWORD>") \
    .config("spark.sql.extensions", "com.datastax.spark.connector.CassandraSparkExtensions") \
    .config("spark.sql.catalog.lh", "com.datastax.spark.connector.datasource.CassandraCatalog") \
    .getOrCreate()
```

You can change the `TOPIC`, `spark.cassandra.auth.password` and other Kafka/Cassandra parameters.
