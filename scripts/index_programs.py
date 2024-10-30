from elasticsearch import Elasticsearch, helpers
import json
import os

# Elasticsearch client connected to the service
es = Elasticsearch(hosts=["http://elasticsearch:9200"])

# Function to create an index with the custom mapping
def create_index_with_mapping(index_name):
    mapping = {
        "mappings": {
            "properties": {
                "cfda": { "type": "keyword" },
                "title": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                },
                "agency": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                },
                "agencySubAgency": {
                    "type": "keyword",
                    "fields": {
                        "parent": {
                            "type": "keyword"
                        }
                    }
                },
                "obligations": { "type": "float" },
                "objectives": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                },
                "popularName": { "type": "text" },
                "permalink": {
                    "type": "text",
                    "index": False
                },
                "assistanceTypes": {
                    "type": "keyword",
                    "fields": {
                        "parent": {
                            "type": "keyword"
                        }
                    }
                },
                "applicantTypes": {
                    "type": "keyword"
                },
                "categories": {
                    "type": "keyword",
                    "fields": {
                        "parent": {
                            "type": "keyword"
                        }
                    }
                }
            }
        },
        "settings": {
            "analysis": {
                "analyzer": {
                    "keyword_lowercase": {
                        "type": "custom",
                        "tokenizer": "keyword",
                        "filter": ["lowercase"]
                    }
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
            "_op_type": "update",
            "_id": program['cfda'],
            "_index": index_name,
            "doc": program,
            "doc_as_upsert": True
        }
        for program in programs
    ]

    helpers.bulk(es, actions)
    print(f"Loaded {len(actions)} documents into Elasticsearch index '{index_name}'")

def delete_index(index_name):
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print(f"Index '{index_name}' deleted.")
    else:
        print(f"Index '{index_name}' does not exist.")

if __name__ == "__main__":
    index_name = "programs"
    # Uncomment to delete the existing index if necessary
    delete_index(index_name)
    
    # Create the index with the custom mapping
    create_index_with_mapping(index_name)

    # Path to your programs-table.json file
    json_file_path = os.path.join('/app/data', 'programs-table.json')
    
    # Load the JSON data into Elasticsearch
    load_data(json_file_path, index_name)
