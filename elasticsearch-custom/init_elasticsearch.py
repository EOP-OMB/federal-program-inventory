import time
import sys
import logging
from elasticsearch import Elasticsearch
from index_programs import delete_index, create_index_with_mapping, load_data, verify_index

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_elasticsearch():
    """Wait for Elasticsearch to be ready"""
    es = Elasticsearch(hosts=["http://localhost:9200"])
    max_retries = 60
    retry_interval = 5
    
    logger.info("Waiting for Elasticsearch to be ready...")
    for i in range(max_retries):
        try:
            if es.ping():
                logger.info("Successfully connected to Elasticsearch")
                return True
            logger.info(f"Attempt {i+1}/{max_retries} - Elasticsearch not ready yet, waiting {retry_interval} seconds...")
        except Exception as e:
            logger.info(f"Attempt {i+1}/{max_retries} - Elasticsearch not ready yet: {str(e)}")
        time.sleep(retry_interval)
    
    logger.error("Could not connect to Elasticsearch after maximum retries")
    sys.exit(1)

if __name__ == "__main__":
    try:
        # Wait for Elasticsearch to be ready
        wait_for_elasticsearch()
        
        # Run indexing process
        index_name = "programs"
        json_file_path = '/usr/local/data/programs-table.json'
        
        delete_index(index_name)
        create_index_with_mapping(index_name)
        doc_count = load_data(json_file_path, index_name)
        final_count = verify_index(index_name)
        
        if final_count > 0:
            logger.info(f"Successfully indexed {final_count} documents")
        else:
            logger.error("No documents were indexed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)