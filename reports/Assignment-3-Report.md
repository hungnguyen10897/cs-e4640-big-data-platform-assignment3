# This your assignment report

<br>
<br>

## Part 1 - Batch data ingestion

<br>
<br>

1. The ingestion will be applied to files of data. Design a set of constraints for files that **mysimbdp** will support for ingestion.
Design a set of constraints for the tenant service profile w.r.t. ingestion (e.g., maximum number of files and amount of data).
Explain why you as a platform provider decide such constraints. Implement these constraints into simple configuration files
and provide examples (e.g., JSON or YAML).

We need such constraints for each tenant service profie to control the amount of data ingested to the platform from each tenant.
We'll need to scale down one tenant's throughput if we have too many tenants in the platform. In the current platform, each tenant's 
directory (e.g `code/batch/tenants/gift_card`) contains `clientbatchingestapp.cfg` file which is the configurations file for the `clientingestapp`,
sample:

```
[INGEST]
file_num=2                        # Max Number of files in a batch
file_size_mb=100                  # File size limit in MB
file_extension=tsv                # File extension to include in batch

[CASSANDRA]                       # Cassandra related configs
host=localhost
username=k8ssandra-superuser
password=L8AqSx3E7kZofZ00Pash
keyspace=mysimbdp
```

<br>
<br>

2. Each tenant will put the tenant's data files to be ingested into a directory, **client-staging-input-directory** within **mysimbdp**.
Each tenant provides ingestion programs/pipelines, **clientbatchingestapp**, which will take the tenant's files as input, in
**client-staging-input-directory**, and ingest the files into **mysimbdp-coredms**. Any **clientbatchingestapp** must perform at
least one type of data wrangling. As a tenant, explain the design of **clientbatchingestapp** and provide one implementation.
Note that **clientbatchingestapp** follows the guideline of **mysimbdp** given in the next Point 3.

Each tenant will have its directory at `code/batch/tenants/<TENANT_NAME>`, e.g `code/batch/tenants/gift_card/`, the directory contains:

- `clientbatchingestapp.cfg`: configuration of the `clientbatchingestapp`
- `clientbatchingestapp.py`: `clientbatchingestapp` ingestion program
- `staging`: staging data directory

New coming tenants need to give only those 3 components.

<br>
<br>

3. As the **mysimbdp** provider, design and implement a component **mysimbdp-batchingestmanager** that invokes tenant's
**clientbatchingestapp** to perform the ingestion for available files in **client-staging-input-directory**. **mysimbdp** imposes the
model that **clientbatchingestapp** has to follow but **clientbatchingestapp** is, in principle, a blackbox to **mysimbdpbatchingestmanager**.
Explain how **mysimbdp-batchingestmanager** decides/schedules the execution of **clientbatchingestapp** for tenants. 


**mysimbdp-batchingestmanager** is located at `code/batch/mysimbdp-batchingestmanager.py`, this program essentially registers tenants for batch ingestion.
Registration of new tenant happens as follow: create new directory under `code/batch/tenants` with new tenant's name, e.g: `code/batch/tenants/toys`. In that directory,
give tenant's configuration in `clientbatchingestapp.cfg`, its data in `staging` and data wrangling function under `clientbatchingestapp.app`. Then in the file
`code/batch/mysimbdp-batchingestmanager.cfg`, add tenant's name into the list. After these 2 steps, the tenant is registered for batch ingestion. Under the hood,
create a `Tenant` object using the components defined in the tenant's directory. **mysimbdp-batchingestmanager** is then able to call the `Tenant` object's
`batch_ingest` method to start the batch ingestion, it does this one tenant at a time until all of registered tenants have finished ingestion.


`mysimbdp-batchingestmanager.cfg` content:
```
[DEFAULT]
tenants=[
    "gift_card",
    "toy"
  ]
```

<br>
<br>

4. Explain your design for the multi-tenancy model in mysimbdp: which parts of mysimbdp will be shared for all tenants,
which parts will be dedicated for individual tenants so that you as a platform provider can add and remove tenants based on
the principle of pay-per-use. Develop test programs (clientbatchingestapp), test data, and test constraints of files, and test
service profiles for tenants according your deployment. Show the performance of ingestion tests, including failures and
exceptions, for at least 2 different tenants in your test environment and constraints. What is the maximum amount of data
per second you can ingest in your tests?


General tenant structure: In this platform, I assume that the tenants will mostly share the same data, the data is reviews data,
each tenant will focus on a specific type of products, e.g gift cards, digital video games... Therefore, I decide the abstract the tenant
into a generic class at `code/batch/tenant.py`. This class dictates how tenants are supposed to read and use their configurations, do logging, 
split staging data files into batches, read data and write data in batch. The main difference of tenants is in how they do data wrangling on
the staging data. This data wrangling is defined as a function on a Pandas Dataframe of staging data (`def process_batch(batch_df)`), located in the module 
`code/batch/tenants/<TENANT>/clientbatchingingestapp.py` (e.g `code/batch/tenants/gift_card/clientbatchingingestapp.py`). 

To unregister a tenant, simply remove its name from `code/batch/mysimbdp-batchingestmanager.cfg`, or its directory.

Performance statistics from Grafana
![](/reports/images/batch_performance.png)

<br>
<br>

5. Implement and provide logging features for capturing successful/failed ingestion as well as metrics about ingestion time,
data size, etc., for files which have been ingested into **mysimbdp**. Logging information must be stored in separate files,
databases or a monitoring system for analytics of ingestion. Show and explain simple statistical data extracted from logs for
individual tenants and for the whole platform with your tests.

Logging is implemented via the `logging` library of Python. Each tenant produces a `clientbatchngingestapp.log` file in the tenant directory
after the **mysimbdp-batchingestmanager** calls data ingestion for that tenant. This log outputs the number of batches, number of rows of data 
for each batch and time taken for ingesting of that batch.

Sample of tenant log:
```
2022-03-15 17:23:27,034 - gift_card - INFO - Start Batch Ingestion for: gift_card to Keyspace: mysimbdp
2022-03-15 17:23:27,043 - gift_card - INFO - Number of Batches: 1
2022-03-15 17:36:57,371 - gift_card - INFO - 	Batch 0: Ingested 148310 rows, took 810.3277261257172 seconds
```

Beside the tenants' logs, **mysimbdp-batchingestmanager** also produces logs available at `code/batch/platform.log`, after execution of **mysimbdp-batchingestmanager**
has started.

Sample of platform log:
```
2022-03-15 17:23:26,711 - root - INFO - Tenants Present in the platform: ['gift_card', 'digital_video_games']
2022-03-15 17:23:26,711 - root - INFO - Tenants Registered in the platform: ['gift_card', 'digital_video_games']
2022-03-15 17:23:26,718 - cassandra.cluster - WARNING - Cluster.__init__ called with contact_points specified, but no load_balancing_policy. In the next major version, this will raise an error; please specify a load-balancing policy. (contact_points = ['localhost'], lbp = None)
2022-03-15 17:23:26,734 - cassandra.cluster - WARNING - Downgrading core protocol version from 66 to 65 for ::1:9042. To avoid this, it is best practice to explicitly set Cluster(protocol_version) to the version supported by your cluster. http://datastax.github.io/python-driver/api/cassandra/cluster.html#cassandra.cluster.Cluster.protocol_version
2022-03-15 17:23:26,752 - cassandra.cluster - WARNING - Downgrading core protocol version from 65 to 5 for ::1:9042. To avoid this, it is best practice to explicitly set Cluster(protocol_version) to the version supported by your cluster. http://datastax.github.io/python-driver/api/cassandra/cluster.html#cassandra.cluster.Cluster.protocol_version
2022-03-15 17:23:26,772 - cassandra.connection - ERROR - Closing connection <AsyncoreConnection(4552363984) ::1:9042> due to protocol error: Error from server: code=000a [Protocol error] message="Beta version of the protocol used (5/v5-beta), but USE_BETA flag is unset"
2022-03-15 17:23:26,773 - cassandra.cluster - WARNING - Downgrading core protocol version from 5 to 4 for ::1:9042. To avoid this, it is best practice to explicitly set Cluster(protocol_version) to the version supported by your cluster. http://datastax.github.io/python-driver/api/cassandra/cluster.html#cassandra.cluster.Cluster.protocol_version
2022-03-15 17:23:26,893 - cassandra.policies - INFO - Using datacenter 'dc1' for DCAwareRoundRobinPolicy (via host '::1:9042'); if incorrect, please specify a local_dc to the constructor, or limit contact points to local cluster nodes
2022-03-15 17:23:26,893 - cassandra.cluster - INFO - Cassandra host 127.0.0.1:9042 removed
2022-03-15 17:23:27,034 - gift_card - INFO - Start Batch Ingestion for: gift_card to Keyspace: mysimbdp
2022-03-15 17:23:27,043 - gift_card - INFO - Number of Batches: 1
2022-03-15 17:36:57,371 - gift_card - INFO - 	Batch 0: Ingested 148310 rows, took 810.3277261257172 seconds
2022-03-15 17:36:57,395 - cassandra.cluster - WARNING - Cluster.__init__ called with contact_points specified, but no load_balancing_policy. In the next major version, this will raise an error; please specify a load-balancing policy. (contact_points = ['localhost'], lbp = None)
2022-03-15 17:36:57,417 - cassandra.cluster - WARNING - Downgrading core protocol version from 66 to 65 for 127.0.0.1:9042. To avoid this, it is best practice to explicitly set Cluster(protocol_version) to the version supported by your cluster. http://datastax.github.io/python-driver/api/cassandra/cluster.html#cassandra.cluster.Cluster.protocol_version
2022-03-15 17:36:57,432 - cassandra.cluster - WARNING - Downgrading core protocol version from 65 to 5 for 127.0.0.1:9042. To avoid this, it is best practice to explicitly set Cluster(protocol_version) to the version supported by your cluster. http://datastax.github.io/python-driver/api/cassandra/cluster.html#cassandra.cluster.Cluster.protocol_version
2022-03-15 17:36:57,448 - cassandra.connection - ERROR - Closing connection <AsyncoreConnection(4606309280) 127.0.0.1:9042> due to protocol error: Error from server: code=000a [Protocol error] message="Beta version of the protocol used (5/v5-beta), but USE_BETA flag is unset"
2022-03-15 17:36:57,448 - cassandra.cluster - WARNING - Downgrading core protocol version from 5 to 4 for 127.0.0.1:9042. To avoid this, it is best practice to explicitly set Cluster(protocol_version) to the version supported by your cluster. http://datastax.github.io/python-driver/api/cassandra/cluster.html#cassandra.cluster.Cluster.protocol_version
2022-03-15 17:36:57,590 - cassandra.policies - INFO - Using datacenter 'dc1' for DCAwareRoundRobinPolicy (via host '127.0.0.1:9042'); if incorrect, please specify a local_dc to the constructor, or limit contact points to local cluster nodes
2022-03-15 17:36:57,590 - cassandra.cluster - INFO - Cassandra host ::1:9042 removed
2022-03-15 17:36:57,789 - digital_video_games - INFO - Start Batch Ingestion for: digital_video_games to Keyspace: mysimbdp
2022-03-15 17:36:57,797 - digital_video_games - INFO - Number of Batches: 1
```

<br>
<br>

## Part 2 - Near-realtime data ingestion

All the code and configurations for this part is at `code/stream`.

<br>
<br>

1. Tenants will put their data into messages and send the messages to a messaging system, **mysimbdp-messagingsystem**
(provisioned by **mysimbdp**) and tenants will develop ingestion programs, **clientstreamingestapp**, which read data from the
messaging system and ingest the data into **mysimbdp-coredms**. For near-realtime ingestion, explain your design for the
multi-tenancy model in **mysimbdp**: which parts of the **mysimbdp** will be shared for all tenants, which parts will be dedicated
for individual tenants so that **mysimbdp** can add and remove tenants based on the principle of pay-per-use. Design and
explain a set of constraints for the tenant service profile w.r.t. data ingestion.


First of all, **mysimbdp-messagingsystem**, which is a Kafka cluster, is deployed by `docker-compose` and defined in `code/stream/kafka-docker-compose.yml`.
After the Kafka cluster is up, the script `code/stream/producer.py` can be executed to send messages to Kafka's Topic. The producer randomly sends messages
of either `gift_card` or `digital_video_games` tenant, the topic to be sent to depends on the tenant. The producer reads tsv data from `code/stream/data/` and
sends 1 row of tsv as a message at a time. The design is such that each tenant has its own topic in Kafka, e.g `gift_card` tenant has a `gift_card` topic.

Second, each tenant will have its own stream ingestion program **clientstreamingestapp** located at `code/stream/tenants/<TENANT>`, e.g `code/stream/tenants/gift_card`.
Within this directory, there are:

- clientstreamingestapp.py          # the ingestion program **clientstreamingestapp**
- clientstreamingestapp.cfg         # Configuration files for **clientstreamingestapp**

To remove a tenant, simply remove its directory from `code/stream/tenants`

<br>
<br>

2. Design and implement a component **mysimbdp-streamingestmanager**, which can start and stop **clientstreamingestapp**
instances on-demand. **mysimbdp** imposes the model that **clientstreamingestapp** has to follow so that **mysimbdpstreamingestmanager** 
can invoke **clientstreamingestapp** as a blackbox, explain the model.

**mysimbdp-streamingestmanager** is implemented as a `docker-compose` file `code/stream/mysimbdp-streamingestmanager-docker-compose.yaml`. 
Each tenant is created as a service. This service executes the **clientstreamingestapp** in the tenant's directory (mounted to the container).

<br>
<br>

3. Develop test ingestion programs (**clientstreamingestapp**), test data, and test service profiles for tenants. Show the
performance of ingestion tests, including failures and exceptions, for at least 2 different tenants in your test environment.
What is the maximum throughput of the ingestion in your tests?

For 2 tenants:

Performance statistics from Grafana
![](/reports/images/stream_performance.png)

Total number of rows: ~150 000 rows, max throughput 150 rows/sec

<br>
<br>

4. **clientstreamingestapp** decides to report the its processing rate, including average ingestion time, total ingestion data size,
and number of messages to **mysimbdp-streamingestmonitor** within a pre-defined period of time. Design the report format
and explain possible components, flows and the mechanism for reporting.

Report sent from **clientstreamingestapp** can have a json format, to be analyzed and visualized by **mysimbdp-streamingestmonitor**.
```
{
  "tenant" : "gift_card",                 # tenant of the **clientstreamingestapp**
  "timestamp" : "2022-03-17 00:00:00,     # timestamp when the report is sent
  "duration" : 600,                       # number of seconds since started
  "average_speed" : 200,                  # average rows per second ingested
  "rows": 120000                          # number of rows ingested so far
}
```

After every pre-defined period, the report is composed by **clientstreamingestapp** based on tracked statistics and sent to **mysimbdp-streamingestmonitor**
via an exposed API.

<br>
<br>

5. Implement a feature in **mysimbdp-streamingestmonitor** to receive the report from **clientstreamingestapp**. Based on the
report from **clientstreamingestapp** and the tenant profile, when the performance is below a threshold, e.g., average
ingestion time is too low, **mysimbdp-streamingestmonitor** decides to inform **mysimbdp-streamingestmanager** about the
situation. Implementation a feature in **mysimbdp-streamingestmanager** to receive information informed by mysimbdpstreamingestmonitor.

SKIPPED

<br>
<br>

## Part 3: Integration and Extension

<br>
<br>

1. Produce an integrated architecture for the logging and monitoring of both batch and near-realtime ingestion features (Part 1,
Point 5 and Part 2, Points 4-5) so that you as a platform provider could know the amount of data ingested and existing
errors/performance for individual tenants.

Logging is done for Batch Ingestion. The same thing can be done similarly for Stream Ingestion by introducing `logging` library for each tenant, 
then logs neccesary statistics into log files at `code/stream/tenants/<TENANT>/clientstreamingestapp.cfg`. Monitoring can be enabled by sending
performance logs and statistics to a monitoring platform.

<br>
<br>

2. In the stream ingestion pipeline, assume that a tenant has to ingest the same data but to different sinks, e.g., **mybdpcoredms** for storage 
and a new **mybdp-streamdataprocessing** component, what features/solutions you can provide and recommend to your tenant?

Tenant can use asynchronous consumers API of Kafka

<br>
<br>

3. The tenant wants to protect the data during the ingestion using some encryption mechanisms, e.g., **clientbatchingestapp**
and **clientstreamingestapp** have to deal with encrypted data. Which features/solutions you recommend the tenants and
which services you might support them for this goal?

Tenant or we as a platform provider can expose a service to pseudonymize data (only sensitive column, e.g Personal ID,...), tenants
can process their data through this service and ingest as normal. Once they need raw data they can pass the processed data stored in
**mybdpcoredms** through an inverse of the service to get the raw unpseudonymized data. (This is how my team is doing at the moment)

<br>
<br>

4. In the case of batch ingestion, we want to (i) detect the quality of data to allow ingestion only for data with a pre-defined
quality of data condition and (ii) store metadata, including detected quality, into the platform, how you, as a platform provider,
and your tenants can work together?

A platform provider can implement filter function for **mybdpcoredms**, which filters in-coming data and only stores valid data. At the same time,
create a metadata store, which specifies the conditions and filters used. As for tenants, they can be instructed about how to implement the filter
and conditions to be met from their ingest app. This reduces the amount of data sent to the server saving network traffic.

<br>
<br>

5. If a tenant has multiple **clientbatchingestapp** and **clientstreamingestapp**, each is suitable for a type of data and has
different workloads (e.g., different CPUs, memory consumption and execution time), how would you extend your design and
implementation in Parts 1 & 2 (only explain the concept/design) to support this requirement?

Currently, this should be quite straightforward in Part 2 since the tenant are separate, it's also called and executed on separate container.
About workloads, the docker-compose services can be separated into Kubernetes Deployment to satisfy different needs. For part 1, there is a shared
interface between tenants. To enable varying needs, simply remove the shared interface, and put each tenant app into a separate program.
