from elasticsearch import Elasticsearch, helpers
import json
import os

# Elasticsearch client connected to the service
es = Elasticsearch(hosts=["http://elasticsearch:9200"])

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
                # Updated nested agency structure
                "agency": {
                    "type": "nested",
                    "properties": {
                        "title": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "subAgency": {
                            "type": "nested",
                            "properties": {
                                "title": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                }
                            }
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
                    "type": "keyword"
                },
                "applicantTypes": {
                    "type": "keyword"
                },
                # Updated nested categories structure
                "categories": {
                    "type": "nested",
                    "properties": {
                        "title": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "subCategory": {
                            "type": "nested",
                            "properties": {
                                "title": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                }
                            }
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

    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=mapping)
        print(f"Index '{index_name}' created with custom mapping.")
    else:
        print(f"Index '{index_name}' already exists.")

def load_data(json_file, index_name):
    with open(json_file, 'r') as f:
        programs = json.load(f)

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