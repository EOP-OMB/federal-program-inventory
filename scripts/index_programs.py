from elasticsearch import Elasticsearch, helpers
import json
import os

#Elasticsearch client connected to elasticsearch service in Docker
es = Elasticsearch(hosts=["http://elasticsearch:9200"])

# Function to create an index with the custom mapping
def create_index_with_mapping(index_name):
    mapping = {
        "mappings": {
            "properties": {
                "cfda": { "type": "text" },
                "title": { "type": "text" },
                "agency": { "type": "text" },
                "obligations": { "type": "float" },
                "objectives": { "type": "text" },
                "popularName": { "type": "text" },
                "permalink": {
                    "type": "text",
                    "index": False  # Store, but do not index permalink
                }
            }
        }
    }

    # Create the index with the provided mapping
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=mapping)
        print(f"Index '{index_name}' created with custom mapping.")
    else:
        print(f"Index '{index_name}' already exists.")

# Function to load data into Elasticsearch
def load_data(json_file, index_name):
    with open(json_file, 'r') as f:
        programs = json.load(f)

    # Prepare data for bulk upload
    actions = [
        {
            "_index": index_name,
            "_source": program
        }
        for program in programs
    ]

    helpers.bulk(es, actions)
    print(f"Loaded {len(actions)} documents into Elasticsearch index '{index_name}'")

if __name__ == "__main__":
    index_name = "programs"
    
    # Create the index with the custom mapping
    create_index_with_mapping(index_name)

    # Path to your programs-table.json file
    json_file_path = os.path.join('/app/data', 'programs-table.json')
    
    # Load the JSON data into Elasticsearch
    load_data(json_file_path, index_name)
