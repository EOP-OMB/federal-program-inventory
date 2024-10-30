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

@router.get("/search/programsTable", response_model=ProgramTableWithFacets)
def search_programs(
    query: Optional[str] = None,
    agencyTitles: Optional[List[str]] = Query(None),
    subAgencyTitles: Optional[List[str]] = Query(None),
    assistanceTypes: Optional[List[str]] = Query(None),
    applicantTypes: Optional[List[str]] = Query(None),
    categoryTitles: Optional[List[str]] = Query(None),
    subCategoryTitles: Optional[List[str]] = Query(None),
    page: int = 1,
    page_size: int = 10,
    sort_field: str = "title",
    sort_order: str = "asc",
    es: Elasticsearch = Depends(get_elasticsearch)
):
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="Page and page_size must be greater than 0")
    
    # Start with match_all query as default
    search_query = {
        "bool": {
            "must": [{"match_all": {}}],
            "filter": []
        }
    }
    
    # Search text query
    if query:
        search_query["bool"]["must"] = [{
            "multi_match": {
                "query": query,
                "fields": ["title^2", "agency.title", "objectives"]
            }
        }]

    filter_conditions = []

    # Handle agency/subagency filters
    if agencyTitles or subAgencyTitles:
        agency_conditions = []
        
        if agencyTitles:
            for agency in agencyTitles:
                agency_conditions.append({
                    "nested": {
                        "path": "agency",
                        "query": {
                            "term": {"agency.title.keyword": agency}
                        }
                    }
                })

        if subAgencyTitles:
            for subagency in subAgencyTitles:
                agency_conditions.append({
                    "nested": {
                        "path": "agency",
                        "query": {
                            "nested": {
                                "path": "agency.subAgency",
                                "query": {
                                    "term": {"agency.subAgency.title.keyword": subagency}
                                }
                            }
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
    if categoryTitles or subCategoryTitles:
        category_conditions = []
        
        if categoryTitles:
            for category in categoryTitles:
                category_conditions.append({
                    "nested": {
                        "path": "categories",
                        "query": {
                            "term": {"categories.title.keyword": category}
                        }
                    }
                })

        if subCategoryTitles:
            for subcategory in subCategoryTitles:
                category_conditions.append({
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

        if category_conditions:
            filter_conditions.append({
                "bool": {
                    "should": category_conditions,
                    "minimum_should_match": 1
                }
            })

    if assistanceTypes:
        filter_conditions.append({"terms": {"assistanceTypes": assistanceTypes}})
    
    if applicantTypes:
        filter_conditions.append({"terms": {"applicantTypes": applicantTypes}})

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
        "assistance_types": {
            "terms": {"field": "assistanceTypes", "size": 100}
        },
        "applicant_types": {
            "terms": {"field": "applicantTypes", "size": 100}
        }
    }

    es_query = {
        "query": search_query,
        "sort": sort,
        "from": (page - 1) * page_size,
        "size": page_size,
        "aggs": aggregations
    }

    response = es.search(index=INDEX_NAME, body=es_query)
    
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