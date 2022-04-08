# This your assignment report

<br>
<br>

## Part 1 - Design for Streaming Analytics

<br>
<br>

1. As a tenant, select a dataset suitable for streaming data analytics as a running scenario. Explain the dataset and why the
dataset is suitable for streaming data analytics in your scenario. As a tenant, present at least two different analytics in the
interest of the tenant: (i) a streaming analytics (tenantstreamapp) which analyzes streaming data from the tenant and (ii) a
batch analytics which analyzes historical results outputted by the streaming analytics. The explanation should be at a high
level to allow us to understand the data and possible analytics so that, later on, you can implement and use them in
answering other questions.

The dataset chosen for this assignment is available at: https://www.kaggle.com/cynthiarempel/amazon-us-customer-reviews-dataset

Dataset Schema:
```
  marketplace TEXT,
  customer_id TEXT,
  review_id TEXT,
  product_id TEXT,
  product_parent TEXT,
  product_title TEXT,
  product_category TEXT,
  star_rating INT,          # 1-5 as given by the reviewer
  helpful_votes INT,        # number of votes by other users
  total_votes INT,          # number of helpful votes for this review from other users
  vine TEXT,
  verified_purchase TEXT,
  review_headline TEXT,
  review_body TEXT,
  review_date DATE,
```

This is reviews data from Amazon US, each row is one review for a particular product with corresponding `star_rating`, `helpful_votes`,
`total_votes`...

This dataset is suitalbe for streaming because:

- Each review is an event, there can be thousand or millions of events coming in from the source systems.
- Not too critical data. If several events/reviews are missed by the stream, this does not severely affect the platform's integrity
- Only the aggregation of the part of data is meaningful (average of `star_rating`, sum of `helpful_votes` and `total_votes`). After aggregations,
the data can be stored in cold storage.

Stream Analytics:

The stream of reviews will aggregate to get the average `star_rating`, sum of `helpful_votes` and sum of `total_votes` grouping by `product_id`, and a 
window of time (1 day) based on `review_date`. As a result of stream analytics, we will have running average `star_rating`, sum of `helpful_votes` and sum of `total_votes`
for a particular product day by day.


Batch Analytics:

- Aggreating all data to get all time `star_rating`, sum of `helpful_votes` and sum of `total_votes` for any product
- Group the result of Stream Analytics by product and window of 1 year, analyze which time of the year a particular product is more favored (has higher `star_rating`,
more `votes` from users)

<br>
<br>

2. The tenant will send data through a messaging system, which provides stream data sources. Discuss and explain the
following aspects for the streaming analytics: (i) should the analytics handle keyed or non-keyed data streams for the tenant
data, and (ii) which types of delivery guarantees should be suitable for the stream analytics and why. 

i. The analytics should be keyed data streams for tenant data although this is not supported by Apache Spark. The main logic
of stream analytics is to aggregate grouping by `product_id`, so it would be great to have keyed data streams partitioned by
`product_id` to avoid shuffling of data across worker instances.

ii. `at-most-once` should be ideal. As mentioned previously, missing some events wouldn't be too serious, so `at-least-once` is not absolutely needed, and  `exactly-once` 
is not too necessary. `at-most-once` prevents having too many duplicate of the same records which can damage integrity of the analytics.

<br>
<br>

3. Given streaming data from the tenant (selected before). Explain the following issues: (i) which types of time should be
associated with stream data sources for the analytics and be considered in stream processing (if the data sources have no
timestamps associated with events, then what would be your solution), (ii) which types of windows should be developed for
the analytics (if no window, then why), (iii) what could cause out-of-order data/records with your selected data in your
running example, and (iv) will watermarks be needed or not, explain why. Explain these aspects and give examples.

i. `review_date` is used as the time for the event, although this is of DATE type, ideally it would be of TIMESTAMP type 
to capture the exact time of review. In real-world system, this time value should be as close as possible to the time it reaches 
the stream analytics system because events that are too late (time_at_stream - time_of_review > watermark) will be dropped by Spark
Streaming. Setting watermark too big can cause performance issue due to state data kept in memory.

ii. I use a time window of 1 day. Since the main time column (`review_date`) of the dataset is of type DATE, it's not possible
to distinguish among reviews of in the same day.

iii. If an event arrives at the stream system too late (time_at_stream - time_of_review > watermark), it will be dropped out of 
the aggregation. Besides, the aboslute order among events are not important.

iv. Watermark is needed, because not all events will arrive on time. I use watermark value of 2 days, meaning data late for less than
2 days is still considered for the aggregations. For instance, event happens at `2022-03-01 00:00:00` arrives at the stream system at
`2022-03-02 23:59:59` will be aggregated, but if it arrives at `2022-03-03 00:00:01` it will be dropped from the aggregations.

<br>
<br>

4. List performance metrics which would be important for the streaming analytics for your tenant cases. For each metric,
explain its definition, how to measure it in your analytics/platform and why it is important for the analytics of the tenant. (1
point)

Input Rate: The aggregate (across all sources) rate of data arriving.

Process Rate: The aggregate (across all sources) rate at which Spark is processing data.

Batch Duration: The duration of each batch.

Operation Duration: The amount of time taken to perform various operations in milliseconds.

Apache Spark offers an available Web UI to monitor all of these metrics and a lot more.

These metrics combined show how the current analytics workflow of the tenant is doing. It can shows if there is too much data coming in for the 
Spark cluster to process so we can scale the cluster accordingly.

<br>
<br>

5. Provide a design of your architecture for the streaming analytics service in which you clarify: tenant data sources,
mysimbdp messaging system, mysimbdp streaming computing service, tenant streaming analytics app, mysimbdpcoredms, and other components, if needed. 
Explain your choices of technologies for implementing your design and reusability of existing assignment works. Note that the result from tenantstreamapp 
will be sent back to the tenant in near real-time and to be ingested into mysimbdp-coredms


![](/reports/images/bdp.png)
Architecture

I use Spark Structured Streaming since it enables scalable, high-throughput, fault-tolerant stream processing. It also allows data processing
through the use of Data Frame API and SQL syntax, there are also windowing and watermarking features necessary for tenant's stream analytics in this case.

Beside Spark Streaming as a new component, other components in the architecture (Python producer, Kafka Streaming service, and Cassandra `mysimpbdp`)
are all reused from previous assignments. I also reused the same topic of the same tenant in Kafka Streaming Service, while in `mysimpbdp` a new table
that contains stream analytics results is created in the same Keyspace `mysimpbdp`.

<br>
<br>

## Part 2 - Implementation of Streaming Analytics

<br>
<br>

1. As a tenant, implement a tenantstreamapp. Explain (i) the structures of the input streaming data and the analytics output
result in your implementation, and (ii) the data serialization/deserialization, for the streaming analytics application
(tenantstreamapp)

i. Input for stream analytics are messages from Kafka, this Spark streaming app subscribes to the tenant's topic in Kafka, to which 
tenant's producer (`code/tenant/producer.py`) produces messages to. Each message has a schema as in Spark:

```
    StructField("marketplace",StringType(),True)
    StructField("customer_id",StringType(),True)
    StructField("review_id",StringType(),True)
    StructField("product_id",StringType(),False)
    StructField("product_parent", StringType(), True)
    StructField("product_title", StringType(), True)
    StructField("product_category", StringType(), True)
    StructField("star_rating", IntegerType(), True)
    StructField("helpful_votes", IntegerType(), True)
    StructField("total_votes", IntegerType(), True)
    StructField("vine", StringType(), True)
    StructField("verified_purchase", StringType(), True)
    StructField("review_headline", StringType(), True)
    StructField("review_body", StringType(), True)
    StructField("review_date", StringType(), True)
```

Output of the Streaming Analytics has schema:

```
    StructField("product_id",StringType(),False)
    StructField("avg_star_rating", IntegerType(), True)
    StructField("sum_helpful_votes", IntegerType(), True)
    StructField("sum_total_votes", IntegerType(), True)
    StructField("number_of_reviews", IntegerType(), True)
    StructField("review_date", DateType(), True)
```


ii. Each message from Kafka has a key and value. All necessary information is in the messages' value.
Messages' values are json-encoded to bytes and sent from Kafka. In Spark Streaming app, the values are
json-decoded into a Spark DataFrame with a schema defined previously.

<br>
<br>

2. Explain the key logic of functions for processing events/records in tenantstreamapp in your implementation. Explain under
which conditions/configurations and how the results are sent back to the tenant in a near real time manner and/or are stored
into mysimbdp-coredms as the final sink.

As new messages are read from Stream into DataFrame, they undergo these operations

- their `review_date` column are turn into a timestamp column through a cast
- All colmns except `product_id`, `star_rating`, `helpful_votes`, `total_votes` and `review_date` are dropped

After these transformations, they are aggregated grouping by the `product_id` and `review_date` window of 1 day. This
aggregation also defines a watermark on `review_date` column of 2 days. As previously explained, this means that data
late for less than 2 days is still considered for aggregation. 

As new events arrive, if they are late within the period of 2 days, they are aggregated with the current group of `product_id` 
and `review_date` window, the new aggregation results are appended immediately to `mysimpbdp` as the `OutputMode` is `Append`.

<br>
<br>

3. Explain a test environment for testing tenantstreamapp, including how you emulate streaming data, configuration of
mysimbdp and other relevant parameters. Run tenantstreamapp and show the operation of the tenantstreamapp with
your test environments. Discuss the analytics and its performance observations when you increase/vary the speed of
streaming data.

Test environment:

- Streaming data is emulated by having a producer of a tenant, reading from raw CSV files of reviews and pushing data row by 
row to tenant's topic in Kafka Streaming service. As Spark Streaming App subscribes to tenant's Kafka topic, events from Kafka
will be sent to Spark in micro-batches.

- Spark Streaming Apps also authenticates and connects to `mysimpbdp` Cassandra cluster as a sink by specifying connection host, port,
authenticationg username, password and destination keyspace and table. It also needs to define `checkpointLocation` and `outputMode`
for the output stream.

<br>
<br>

## Part 3 - Extension

1. Assume that you have an external RESTful (micro) service which accepts a batch of data and performs a type of analytics
and returns the result (e.g., in case of a dynamic machine learning inference) in a near real time manner (like the stream
analytics app), how would you connect such a service into your current platform? Explain what the tenant must do in order to
use such a service.

<br>
<br>

2. Given the output of streaming analytics stored in mysimbdp-coredms for a long time. Explain a batch analytics (see also
Part 1, question 1) that could be used to analyze such historical data. How would you implement it?

In streaming app, we need to define a window on `review_date` column since it's impossible for Spark to store state data
for a particular `product_id` indefinitely, the window signals when the aggregation and related rows for a `product_id` and window
group can be dropped from memory. Therefore, we cannot have all time aggregation statistics for a product with streaming.

With batch, we can easily read all aggregation statistics for a particular `product_id` from stream outputs, and aggregate them once 
again to get all time statistics of average star rating, total votes and total helpful votes.

Implementation:

- Read all data from stream output table in `mysimpbdp-coredms` (`aggregated_reviews`)
- Put all read data into Pandas DataFrame
- Perform window function on that DataFrame, window of `product_id` and `review_date` order by `number_of_reviews`, to get the row
with most `number_of_reviews`. This is because for a particular `product_id` and `review_date`, there will be multiple entries from
the streaming app, as new events come, updated statistics will be appended to the output table. Therefore, we need to get the entry
with most `number_of_reviews` since it's the latest entry
- With these latest entries for `product_id`, `review_date` groups, Aggregate grouping by `product_id` to get all-time average of star rating,
total number of votes and helpful votes. Important to note, the average star rating need to be scaled by `number_of_reviews` to get the right all
time average.

<br>
<br>

3. Assume that the streaming analytics detects a critical condition (e.g., a very high rate of alerts) that should trigger the
execution of a batch analytics to analyze historical data. The result of the batch analytics will be shared into a cloud storage
and a user within the tenant will receive the information about the result. Explain how you will use workflow technologies to
coordinate these interactions and tasks (use a figure to explain your work).

In this scenario, I'd use Apache Airflow as workflow management service. First create a DAG with the needed tasks:

![](/reports/images/workflow.png)
Workflow

Tasks details:

- Batch Analytics: `PythonOperator` task implemented as previously mentioned, output of Batch Analytics will be stored locally as CSV files
- Upload Batch Analytics Results to Cloud Storage: `PythonOperator` task to upload CSV files to destination Cloud Storage
- Email Tenant User about the Results: `PythonOperator` task to inform about Batch Analytics and link to the Cloud Storage of these results

The triggering will be done from inside the Stream Analytics. Since it uses pyspark, essentially a Python script is submitted to Spark as a job.
From the script, we can have conditional checks, if the condition is met, just create an Airflow client and trigger the dag using that client:

```
from airflow.api.client.local_client import Client

c = Client(None, None)
c.trigger_dag(dag_id='test_dag_id', run_id='test_run_id', conf={})
```

<br>
<br>

4. If you want to scale your streaming analytics service for many tenants, many streaming apps, and data, which components
would you focus and which techniques you want to use?

Spark makes this easy, we only need to focus on scaling the Spark cluster size as needed. The streaming apps from tenants will share
the same Spark Cluster.
