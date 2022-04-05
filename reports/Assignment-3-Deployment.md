# This is a deployment/installation guide

<br>
<br>

Prerequisites:
- A running Cassandra cluster from Assignment 1, username and password for authentication to this cluster (follow instructions from Assignment 1)
- Docker and docker-compose

Some parts of the system require to be run by Python 3.8. To install dependencies, run

```
pip install -r code/batch/requirements.txt
```

<br>
<br>

## Part 1 - Batch Data Ingestion

- New tenant addition is described in **Assignment-2-Report.md** file.

- Configure tenant, update contents of `code/batch/<TENANT>/clientbatchingestapp.cfg` file with
desired values, at least `KAFKA username and password`

- Start **clientbatchingestapp**, at `code/batch/` run:

```
python mysimbdp-batchingestmanager.py
```

<br>
<br>

## Part 2 - Stream Data Ingestion

- Start **mysimbdp-messagingsystem**, at `code/stream` run:

```
docker-compose -f kafka-docker-compose.yml up 
```

- New tenant addition is described in **Assignment-2-Report.md** file.

- Configure tenant, update contents of `code/stream/<TENANT>/clientbatchingestapp.cfg` file with
desired values, at least `KAFKA username and password`

- Start **mysimbdp-streamingestmanager**, at `code/stream` run:
```
docker-compose -f mysimbdp-streamingestmanager-docker-compose.yaml up
```

- Start producer to generate messages, at `code/stream` run:
```
python producer.py
```
