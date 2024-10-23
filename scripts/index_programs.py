from elasticsearch import Elasticsearch
import json
import os

# Elasticsearch client connected to elasticsearch service in Docker
es = Elasticsearch(hosts=["http://elasticsearch:9200"])

# Path to your programs-table.json file
json_file_path = os.path.join('/app/data', 'programs-table.json')

# Load the JSON data
with open(json_file_path, 'r') as json_file:
    programs_data = json.load(json_file)

# Index the programs data into Elasticsearch
for program in programs_data:
    es.index(index="programs-index", document=program)

print("Programs data successfully indexed into Elasticsearch.")
