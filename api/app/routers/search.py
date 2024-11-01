from elasticsearch import Elasticsearch
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from app.models.programTable import ProgramTableWithFacets, SearchFacets, CategoryFacet, AgencyFacet, FacetBucket
from app.dependencies import get_elasticsearch

router = APIRouter(
    prefix="/api",
    tags=["Search"]
)

# Constants
INDEX_NAME = "programs"
DEFAULT_PAGE_SIZE = 10
SEARCH_FIELDS = {
    "title": {"boost": 2},
    "objectives": {"boost": 1},
    "cfda": {"boost": 1},
    "popularName": {"boost": 1}
}
VALID_SORT_FIELDS = {
    "cfda": "cfda.keyword",
    "title": "title.keyword",
    "objectives": "objectives.keyword",
    "popularName": "popularName.keyword",
    "obligations": "obligations.keyword"
}

def build_multi_match_query(query: str) -> Dict[str, Any]:
    """Build elasticsearch multi-match query with field boosts."""
    return {
        "multi_match": {
            "query": query,
            "fields": [f"{field}^{config['boost']}" for field, config in SEARCH_FIELDS.items()],
            "type": "best_fields",
            "operator": "and",
            "fuzziness": "AUTO"
        }
    }

def build_nested_filter(path: str, conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a nested filter query with multiple conditions."""
    if not conditions:
        return {}
    return {
        "bool": {
            "should": [
                {"nested": {"path": path, "query": condition}}
                for condition in conditions
            ],
            "minimum_should_match": 1
        }
    }

def build_agency_filter(agency_strings: List[str]) -> Dict[str, Any]:
    """Build agency filter query from list of agency strings."""
    if not agency_strings:
        return {}
    
    agency_conditions = []
    for agency_string in agency_strings:
        agency, subagency = parse_parent_child(agency_string)
        if subagency:
            agency_conditions.append({
                "bool": {
                    "must": [
                        {"term": {"agency.title.keyword": agency}},
                        {"nested": {
                            "path": "agency.subAgency",
                            "query": {"term": {"agency.subAgency.title.keyword": subagency}}
                        }}
                    ]
                }
            })
        else:
            agency_conditions.append({"term": {"agency.title.keyword": agency}})
    return build_nested_filter("agency", agency_conditions)

def build_category_filter(category_strings: List[str]) -> Dict[str, Any]:
    """Build category filter query from list of category strings."""
    if not category_strings:
        return {}
    
    category_conditions = []
    for category_string in category_strings:
        category, subcategory = parse_parent_child(category_string)
        if subcategory:
            category_conditions.append({
                "bool": {
                    "must": [
                        {"term": {"categories.title.keyword": category}},
                        {"nested": {
                            "path": "categories.subCategory",
                            "query": {"term": {"categories.subCategory.title.keyword": subcategory}}
                        }}
                    ]
                }
            })
        else:
            category_conditions.append({"term": {"categories.title.keyword": category}})
    return build_nested_filter("categories", category_conditions)

def build_aggregations() -> Dict[str, Any]:
    """Build aggregations for faceted search."""
    return {
        "total_obligations": {"sum": {"field": "obligations"}},
        "categories": {
            "nested": {"path": "categories"},
            "aggs": {
                "category_titles": {
                    "terms": {"field": "categories.title.keyword", "size": 1000},
                    "aggs": {
                        "subcategories": {
                            "nested": {"path": "categories.subCategory"},
                            "aggs": {
                                "subcategory_titles": {
                                    "terms": {"field": "categories.subCategory.title.keyword", "size": 1000}
                                }
                            }
                        }
                    }
                }
            }
        },
        "agencies": {
            "nested": {"path": "agency"},
            "aggs": {
                "agency_names": {
                    "terms": {"field": "agency.title.keyword", "size": 1000},
                    "aggs": {
                        "subagencies": {
                            "nested": {"path": "agency.subAgency"},
                            "aggs": {
                                "subagency_names": {
                                    "terms": {"field": "agency.subAgency.title.keyword", "size": 1000}
                                }
                            }
                        }
                    }
                }
            }
        },
        "assistance_types": {"terms": {"field": "assistanceTypes", "size": 1000}},
        "applicant_types": {"terms": {"field": "applicantTypes", "size": 1000}}
    }

def parse_parent_child(value_string: str) -> tuple[str, Optional[str]]:
    """Parse a string to get parent and optional child values."""
    if not value_string:
        return "", None
    parts = value_string.split(" - ", 1)
    return parts[0], parts[1] if len(parts) > 1 else None

@router.get("/search/programsTable", response_model=ProgramTableWithFacets)
def search_programs(
    query: Optional[str] = None,
    agencySubAgency: Optional[List[str]] = Query(None),
    categorySubcategory: Optional[List[str]] = Query(None),
    assistanceTypes: Optional[List[str]] = Query(None),
    applicantTypes: Optional[List[str]] = Query(None),
    page: int = Query(1, gt=0),
    page_size: int = Query(DEFAULT_PAGE_SIZE, gt=0),
    sort_field: str = "title",
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    es: Elasticsearch = Depends(get_elasticsearch)
) -> ProgramTableWithFacets:
    """
    Search programs with faceted filters and pagination.
    """
    try:
        # Validate sort field
        if sort_field not in VALID_SORT_FIELDS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid sort field. Valid options are: {list(VALID_SORT_FIELDS.keys())}"
            )

        # Build base query
        search_query = {
            "bool": {
                "must": [build_multi_match_query(query) if query else {"match_all": {}}],
                "filter": []
            }
        }

        # Add filters
        filter_conditions = []
        
        agency_filter = build_agency_filter(agencySubAgency or [])
        if agency_filter:
            filter_conditions.append(agency_filter)
            
        category_filter = build_category_filter(categorySubcategory or [])
        if category_filter:
            filter_conditions.append(category_filter)
            
        if assistanceTypes:
            filter_conditions.append({"terms": {"assistanceTypes": assistanceTypes}})
        if applicantTypes:
            filter_conditions.append({"terms": {"applicantTypes": applicantTypes}})
        
        if filter_conditions:
            search_query["bool"]["filter"] = filter_conditions

        # Build complete elasticsearch query
        es_query = {
            "query": search_query,
            "sort": [{VALID_SORT_FIELDS[sort_field]: {"order": sort_order}}],
            "from": (page - 1) * page_size,
            "size": page_size,
            "aggs": build_aggregations()
        }

        # Execute search
        try:
            response = es.search(index=INDEX_NAME, body=es_query)
        except Exception as es_error:
            raise HTTPException(
                status_code=500,
                detail=f"Search service error: {str(es_error)}"
            )
        
        # Process results
        hits = response["hits"]["hits"]
        programs = [hit["_source"] for hit in hits]
        total_obligations = response["aggregations"]["total_obligations"]["value"]
        total_count = response["hits"]["total"]["value"]

        # Build facets
        facets = SearchFacets(
            categories=[
                CategoryFacet(
                    title=bucket["key"],
                    doc_count=bucket["doc_count"],
                    subcategories=[
                        FacetBucket(key=sub["key"], doc_count=sub["doc_count"])
                        for sub in bucket["subcategories"]["subcategory_titles"]["buckets"]
                    ]
                )
                for bucket in response["aggregations"]["categories"]["category_titles"]["buckets"]
            ],
            agencies=[
                AgencyFacet(
                    title=bucket["key"],
                    doc_count=bucket["doc_count"],
                    subagencies=[
                        FacetBucket(key=sub["key"], doc_count=sub["doc_count"])
                        for sub in bucket["subagencies"]["subagency_names"]["buckets"]
                    ]
                )
                for bucket in response["aggregations"]["agencies"]["agency_names"]["buckets"]
            ],
            assistance_types=[
                FacetBucket(key=bucket["key"], doc_count=bucket["doc_count"])
                for bucket in response["aggregations"]["assistance_types"]["buckets"]
            ],
            applicant_types=[
                FacetBucket(key=bucket["key"], doc_count=bucket["doc_count"])
                for bucket in response["aggregations"]["applicant_types"]["buckets"]
            ]
        )

        return ProgramTableWithFacets(
            programs=programs,
            total_obligations=total_obligations,
            count=total_count,
            page=page,
            page_size=page_size,
            facets=facets
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")