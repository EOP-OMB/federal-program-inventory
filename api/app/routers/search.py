from elasticsearch import Elasticsearch
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models.programTable import ProgramTable
from app.dependencies import get_elasticsearch

router = APIRouter()
INDEX_NAME = "programs"

@router.get("/search/programsTable", response_model=ProgramTable)
def search_programs(
    query: Optional[str] = None,
    subAgency: Optional[str] = None,
    assistanceTypes: Optional[List[str]] = Query(None),
    applicantTypes: Optional[List[str]] = Query(None),
    categories: Optional[List[str]] = Query(None),
    page: int = 1,
    page_size: int = 10,
    sort_field: str = "title",
    sort_order: str = "asc",
    es: Elasticsearch = Depends(get_elasticsearch)
):
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="Page and page_size must be greater than 0")
    
    # Construct Elasticsearch query
    search_query = {
        "bool": {
            "must": [],
            "filter": []
        }
    }
    
    # Search text query
    if query:
        search_query["bool"]["must"].append({
            "multi_match": {
                "query": query,
                "fields": ["title^2", "agency", "objectives"]
            }
        })

    # Filtering conditions
    if subAgency:
        search_query["bool"]["filter"].append({"term": {"subAgency": subAgency}})
    if assistanceTypes:
        search_query["bool"]["filter"].append({"terms": {"assistanceTypes": assistanceTypes}})
    if applicantTypes:
        search_query["bool"]["filter"].append({"terms": {"applicantTypes": applicantTypes}})
    if categories:
        search_query["bool"]["filter"].append({"terms": {"categories": categories}})
    
    # Sorting
    sort_options = {
        "title": "title.keyword",
        "agency": "agency.keyword",
        "objectives": "objectives.keyword"
    }
    sort_field = sort_options.get(sort_field, "title.keyword")
    sort = [{sort_field: {"order": sort_order}}]
    
    # Aggregation for obligations
    aggregation = {
        "total_obligations": {"sum": {"field": "obligations"}},
        "count": {"value_count": {"field": "cfda"}}
    }
    
    # Full Elasticsearch query
    es_query = {
        "query": search_query,
        "sort": sort,
        "from": (page - 1) * page_size,
        "size": page_size,
        "aggs": aggregation
    }
    
    # Execute search
    response = es.search(index=INDEX_NAME, body=es_query)
    
    # Parse results
    hits = response["hits"]["hits"]
    programs = [hit["_source"] for hit in hits]
    total_obligations = response["aggregations"]["total_obligations"]["value"]
    total_count = response["aggregations"]["count"]["value"]

    # Prepare response model
    result = ProgramTable(
        programs=programs,
        total_obligations=total_obligations,
        count=total_count,
        page=page,
        page_size=page_size
    )
    
    return result
