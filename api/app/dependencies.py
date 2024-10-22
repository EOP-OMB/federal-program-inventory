from elasticsearch import Elasticsearch

def get_elasticsearch():
    es = Elasticsearch([{'host': 'elasticsearch', 'port': 9200}])
    return es
