#!/bin/bash
set -e

# Start Elasticsearch in the background
/usr/share/elasticsearch/bin/elasticsearch -d

# Wait for Elasticsearch to be ready
until curl -s http://localhost:9200 >/dev/null; do
    echo 'Waiting for Elasticsearch to start...'
    sleep 5
done

echo "Elasticsearch is ready, running indexing script..."

# Run the indexing script
python3 /usr/local/elastic-setup/init_elasticsearch.py

echo "Indexing complete, keeping Elasticsearch running..."

# Keep the container running by starting Elasticsearch in the foreground
exec /usr/share/elasticsearch/bin/elasticsearch