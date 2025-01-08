FROM docker.elastic.co/elasticsearch/elasticsearch:8.15.0

# Set environment variables
ENV discovery.type=single-node
ENV xpack.security.enabled=false

# Define healthcheck to ensure container is running
HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-interval=40s \
    CMD curl -f http://localhost:9200/_cluster/health || exit 1

# Expose port 9200
EXPOSE 9200

# Install Python and dependencies
USER root
RUN apt-get update && \
    apt-get install -y python3 python3-pip dos2unix && \
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
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
    dos2unix /usr/local/bin/docker-entrypoint.sh

# Now switch to elasticsearch user after all setup is done
USER elasticsearch

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

