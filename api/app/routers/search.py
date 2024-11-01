from elasticsearch import Elasticsearch
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models.programTable import ProgramTableWithFacets, SearchFacets, CategoryFacet, AgencyFacet, FacetBucket
from app.dependencies import get_elasticsearch

router = APIRouter(
    prefix="/api",
    tags=["Search"]
)
INDEX_NAME = "programs"

def parse_parent_child(value_string: str) -> tuple[str, Optional[str]]:
    """Parse a string to get parent and optional child values."""
    parts = value_string.split(" - ", 1)
    return parts[0], parts[1] if len(parts) > 1 else None

@router.get("/search/programsTable", response_model=ProgramTableWithFacets)
def search_programs(
    query: Optional[str] = None,
    agencySubAgency: Optional[List[str]] = Query(None),
    categorySubcategory: Optional[List[str]] = Query(None),
    assistanceTypes: Optional[List[str]] = Query(None),
    applicantTypes: Optional[List[str]] = Query(None),
    page: int = 1,
    page_size: int = 10,
    sort_field: str = "title",
    sort_order: str = "asc",
    es: Elasticsearch = Depends(get_elasticsearch)
):
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="Page and page_size must be greater than 0")
    
    # Initialize the compound query
    search_query = {
        "bool": {
            "must": [{"match_all": {}}],  # Default to match all
            "filter": []
        }
    }
    
    # Fuzzy search with explicitly specified fields
    if query:
        search_query["bool"]["must"] = [{
            "multi_match": {
                "query": query,
                "fields": [
                    "title^2",  # Boosted field
                    "objectives",
                    "cfda",
                    "popularName"
                ],
                "type": "best_fields",
                "operator": "and",
                "fuzziness": "AUTO"  # Added fuzzy matching
            }
        }]

    filter_conditions = []

    # Handle agency/subagency filters
    if agencySubAgency:
        agency_conditions = []
        for agency_string in agencySubAgency:
            agency, subagency = parse_parent_child(agency_string)
            if subagency:
                agency_conditions.append({
                    "nested": {
                        "path": "agency",
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {"agency.title.keyword": agency}},
                                    {
                                        "nested": {
                                            "path": "agency.subAgency",
                                            "query": {
                                                "term": {"agency.subAgency.title.keyword": subagency}
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                })
            else:
                agency_conditions.append({
                    "nested": {
                        "path": "agency",
                        "query": {
                            "term": {"agency.title.keyword": agency}
                        }
                    }
                })
        
        if agency_conditions:
            filter_conditions.append({
                "bool": {
                    "should": agency_conditions,
                    "minimum_should_match": 1
                }
            })

    # Handle category/subcategory filters
    if categorySubcategory:
        category_conditions = []
        for category_string in categorySubcategory:
            category, subcategory = parse_parent_child(category_string)
            if subcategory:
                category_conditions.append({
                    "nested": {
                        "path": "categories",
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {"categories.title.keyword": category}},
                                    {
                                        "nested": {
                                            "path": "categories.subCategory",
                                            "query": {
                                                "term": {"categories.subCategory.title.keyword": subcategory}
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                })
            else:
                category_conditions.append({
                    "nested": {
                        "path": "categories",
                        "query": {
                            "term": {"categories.title.keyword": category}
                        }
                    }
                })

        if category_conditions:
            filter_conditions.append({
                "bool": {
                    "should": category_conditions,
                    "minimum_should_match": 1
                }
            })

    # Add exact match filters
    if assistanceTypes:
        filter_conditions.append({"terms": {"assistanceTypes": assistanceTypes}})
    
    if applicantTypes:
        filter_conditions.append({"terms": {"applicantTypes": applicantTypes}})

    # Add all filters to the filter context
    if filter_conditions:
        search_query["bool"]["filter"] = filter_conditions

    # Sorting
    sort_options = {
        "title": "title.keyword",
        "objectives": "objectives.keyword"
    }
    sort_field = sort_options.get(sort_field, "title.keyword")
    sort = [{sort_field: {"order": sort_order}}]

    # Aggregations
    aggregations = {
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
        "assistance_types": {
            "terms": {"field": "assistanceTypes", "size": 1000}
        },
        "applicant_types": {
            "terms": {"field": "applicantTypes", "size": 1000}
        }
    }

    es_query = {
        "query": search_query,
        "sort": sort,
        "from": (page - 1) * page_size,
        "size": page_size,
        "aggs": aggregations
    }

    try:
        response = es.search(index=INDEX_NAME, body=es_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Search service is currently unavailable.")
    
    hits = response["hits"]["hits"]
    programs = [hit["_source"] for hit in hits]
    total_obligations = response["aggregations"]["total_obligations"]["value"]
    total_count = response["hits"]["total"]["value"]

    facets = SearchFacets(
        categories=[
            CategoryFacet(
                title=bucket["key"],
                doc_count=bucket["doc_count"],
                subcategories=[
                    FacetBucket(
                        key=sub_bucket["key"],
                        doc_count=sub_bucket["doc_count"]
                    )
                    for sub_bucket in bucket["subcategories"]["subcategory_titles"]["buckets"]
                ]
            )
            for bucket in response["aggregations"]["categories"]["category_titles"]["buckets"]
        ],
        agencies=[
            AgencyFacet(
                title=bucket["key"],
                doc_count=bucket["doc_count"],
                subagencies=[
                    FacetBucket(
                        key=sub_bucket["key"],
                        doc_count=sub_bucket["doc_count"]
                    )
                    for sub_bucket in bucket["subagencies"]["subagency_names"]["buckets"]
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
