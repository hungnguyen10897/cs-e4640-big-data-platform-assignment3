# Set Up Cassandra table that stores tenant data
./cqlsh-astra/bin/cqlsh  -u k8ssandra-superuser -p czFO48OolLkkmhoouAGe -f tenant-table.cql

# Run tenantstreamapp
spark-submit  \
--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.2 \
--packages com.datastax.spark:spark-cassandra-connector_2.12:3.0.1 \
--conf spark.sql.extensions=com.datastax.spark.connector.CassandraSparkExtensions \
tenantstreamapp.py

# There might be issues with maven or ivy caches, remove ~/.ivy2
