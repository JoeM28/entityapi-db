# Custom Kafka Connect image with the Couchbase source connector plugin installed.
# Based on Confluent's official connect image which includes confluent-hub CLI.
FROM confluentinc/cp-kafka-connect:7.6.0

# Install the Couchbase Kafka Connector from Confluent Hub.
# --no-prompt accepts the license automatically (required for non-interactive Docker builds).
RUN confluent-hub install --no-prompt couchbase/kafka-connect-couchbase:4.1.12
