#!/bin/sh
# set -euxo pipefail

# Make sure this script is only triggered on Acorn creation events
echo "event: ${ACORN_EVENT}"
if [ "${ACORN_EVENT}" = "delete" ]; then
   echo "ACORN_EVENT must be [create, update], currently is [${ACORN_EVENT}]"
   exit 0
fi

# Couple of variables to make local testing simpler
termination_log="/dev/termination-log"
acorn_output="/run/secrets/output"

# Target cassandra container
DB_HOST="cassandra"
DB_PORT=9042

# Wait for Cassandra to be ready
until cqlsh -u $DB_USER -p $DB_PASS -e "DESC KEYSPACES" -h $DB_HOST -C $DB_PORT > /dev/null 2>&1; do
  echo "Waiting for Cassandra to be ready..."
  sleep 2
done

echo "Cassandra is ready!"

# Create a keyspace
cqlsh -u $DB_USER -p $DB_PASS -e "CREATE KEYSPACE IF NOT EXISTS ${DB_KEYSPACE} WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};" $DB_HOST $DB_PORT

if [ $? -eq 0 ]; then
    echo "Database initialized."
else
    echo "Database initialization failed"
    exit 1
fi

# Define service
cat > $acorn_output<<EOF
services: db: {
	default:   true
	container: "cassandra"
	secrets: ["admin"]
	ports: "9042"
	data: keyspace: "${DB_KEYSPACE}"
}
EOF