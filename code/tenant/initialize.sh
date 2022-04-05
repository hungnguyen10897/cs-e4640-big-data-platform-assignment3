docker-compose -f kafka-docker-compose.yml up 

bin/kafka-topics.sh --list --bootstrap-server localhost:29092

docker-compose -f mysimbdp-streamingestmanager-docker-compose.yaml up -b
