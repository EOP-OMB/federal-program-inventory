from elasticsearch import Elasticsearch
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.dependencies import get_elasticsearch
from app.models.programTable import (
    Program, ProgramTable, ProgramTableWithFacets, 
    SearchFacets, CategoryFacet, AgencyFacet, FacetBucket
)

router = APIRouter()
INDEX_NAME = "programs"


@router.get("/search/programsTable", response_model=ProgramTableWithFacets)
def search_programs(
    query: Optional[str] = None,
    agency: Optional[str] = None,
    subAgency: Optional[str] = None,
    assistanceTypes: Optional[List[str]] = Query(None),
    applicantTypes: Optional[List[str]] = Query(None),
    categoryTitles: Optional[List[str]] = Query(None),
    subCategories: Optional[List[str]] = Query(None),
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
            "should": [],
            "minimum_should_match": 0
        }
    }
    
    # Search text query
    if query:
        search_query["bool"]["must"].append({
            "multi_match": {
                "query": query,
                "fields": ["title^2", "agency.title", "objectives"]
            }
        })

    # Handle nested agency/subagency filter
    if agency or subAgency:
        nested_agency_query = {
            "nested": {
                "path": "agency",
                "query": {
                    "bool": {
                        "must": []
                    }
                }
            }
        }
        
        if agency:
            nested_agency_query["nested"]["query"]["bool"]["must"].append({
                "term": {"agency.title.keyword": agency}
            })
        
        if subAgency:
            nested_agency_query["nested"]["query"]["bool"]["must"].append({
                "nested": {
                    "path": "agency.subAgency",
                    "query": {
                        "term": {"agency.subAgency.title.keyword": subAgency}
                    }
                }
            })
        
        search_query["bool"]["must"].append(nested_agency_query)

    # Handle nested category/subcategory filter
    if categoryTitles or subCategories:
        category_queries = []
        
        if categoryTitles:
            for category_title in categoryTitles:
                category_queries.append({
                    "nested": {
                        "path": "categories",
                        "query": {
                            "term": {"categories.title.keyword": category_title}
                        }
                    }
                })

        if subCategories:
            for subcategory in subCategories:
                category_queries.append({
                    "nested": {
                        "path": "categories",
                        "query": {
                            "nested": {
                                "path": "categories.subCategory",
                                "query": {
                                    "term": {"categories.subCategory.title.keyword": subcategory}
                                }
                            }
                        }
                    }
                })

        search_query["bool"]["should"].extend(category_queries)
        if category_queries:
            search_query["bool"]["minimum_should_match"] = 1

    # Regular filters for assistance types and applicant types
    if assistanceTypes:
        search_query["bool"]["should"].append({"terms": {"assistanceTypes": assistanceTypes}})
        search_query["bool"]["minimum_should_match"] = 1
    
    if applicantTypes:
        search_query["bool"]["should"].append({"terms": {"applicantTypes": applicantTypes}})
        search_query["bool"]["minimum_should_match"] = 1

    # Sorting
    sort_options = {
        "title": "title.keyword",
        "objectives": "objectives.keyword"
    }
    sort_field = sort_options.get(sort_field, "title.keyword")
    sort = [{sort_field: {"order": sort_order}}]

    # Aggregations for facets
    aggregations = {
        "total_obligations": {"sum": {"field": "obligations"}},
        "count": {"value_count": {"field": "cfda"}},
        # Nested aggregation for categories
        "categories": {
            "nested": {"path": "categories"},
            "aggs": {
                "category_titles": {
                    "terms": {"field": "categories.title.keyword", "size": 100},
                    "aggs": {
                        "subcategories": {
                            "nested": {"path": "categories.subCategory"},
                            "aggs": {
                                "subcategory_titles": {
                                    "terms": {"field": "categories.subCategory.title.keyword", "size": 100}
                                }
                            }
                        }
                    }
                }
            }
        },
        # Nested aggregation for agencies
        "agencies": {
            "nested": {"path": "agency"},
            "aggs": {
                "agency_names": {
                    "terms": {"field": "agency.title.keyword", "size": 100},
                    "aggs": {
                        "subagencies": {
                            "nested": {"path": "agency.subAgency"},
                            "aggs": {
                                "subagency_names": {
                                    "terms": {"field": "agency.subAgency.title.keyword", "size": 100}
                                }
                            }
                        }
                    }
                }
            }
        },
        # Regular aggregations for assistance and applicant types
        "assistance_types": {
            "terms": {"field": "assistanceTypes", "size": 100}
        },
        "applicant_types": {
            "terms": {"field": "applicantTypes", "size": 100}
        }
    }

    # Full Elasticsearch query
    es_query = {
        "query": search_query,
        "sort": sort,
        "from": (page - 1) * page_size,
        "size": page_size,
        "aggs": aggregations
    }

    # Execute search
    response = es.search(index=INDEX_NAME, body=es_query)

    # Parse results
    hits = response["hits"]["hits"]
    programs = [hit["_source"] for hit in hits]
    total_obligations = response["aggregations"]["total_obligations"]["value"]
    total_count = response["hits"]["total"]["value"]

    # Process facets
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

    # Prepare response
    result = ProgramTableWithFacets(
        programs=programs,
        total_obligations=total_obligations,
        count=total_count,
        page=page,
        page_size=page_size,
        facets=facets
    )

    return result