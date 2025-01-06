FROM docker.elastic.co/elasticsearch/elasticsearch:8.15.0

# Install Python and dependencies
USER root
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create necessary directories
WORKDIR /usr/local/elastic-setup

# Create data directory
RUN mkdir -p /usr/local/data

# Copy your requirements file
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy your indexing scripts and data
COPY index_programs.py .
COPY init_elasticsearch.py .
COPY data/programs-table.json /usr/local/data/

# Copy and set permissions for entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Now switch to elasticsearch user after all setup is done
USER elasticsearch

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]