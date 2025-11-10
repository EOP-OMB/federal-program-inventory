from elasticsearch import Elasticsearch
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from app.models.programTable import ProgramTableWithFacets, SearchFacets, CategoryFacet, AgencyFacet, FacetBucket, SearchRequest
from app.dependencies import get_elasticsearch

router = APIRouter(
    prefix="/api",
    tags=["Search"]
)

# Constants
INDEX_NAME = "programs"
SEARCH_FIELDS = {
    "title": {"boost": 2},
    "objectives": {"boost": 1},
    "cfda": {"boost": 1},
    "popularName": {"boost": 1},
    "gwo": {"boost": 1},
    "pons": {"boost": 1}
}
VALID_SORT_FIELDS = {
    "cfda": "cfda.keyword",
    "title": "title.keyword",
    "objectives": "objectives.keyword",
    "popularName": "popularName.keyword",
    "obligations": "obligations"
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
    """
    Build agency filter query from list of agency strings.
    Handles special cases including:
    - "Unspecified" matches both null subagency AND subagency matching parent
    - "Other agencies" special handling
    - Regular agency + subagency pairs
    """
    if not agency_strings:
        return {}
    
    agency_conditions = []
    for agency_string in agency_strings:
        agency, subagency = parse_parent_child(agency_string)
        
        # Special handling for "Other agencies"
        if agency.startswith("Other agencies"):
            if subagency:
                agency_conditions.append({
                    "nested": {
                        "path": "agency",
                        "query": {
                            "term": {
                                "agency.title.keyword": subagency
                            }
                        }
                    }
                })
            continue

        # Regular agency handling
        if subagency:
            if subagency == "Unspecified":
                # For "Unspecified", match either:
                # 1. No subagency exists, OR
                # 2. Subagency title matches parent agency
                # 3. Subagency is "N/A"
                agency_conditions.append({
                    "nested": {
                        "path": "agency",
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {"agency.title.keyword": agency}}
                                ],
                                "should": [
                                    # Either no subagency exists
                                    {
                                        "bool": {
                                            "must_not": [
                                                {"nested": {
                                                    "path": "agency.subAgency",
                                                    "query": {
                                                        "exists": {
                                                            "field": "agency.subAgency.title"
                                                        }
                                                    }
                                                }}
                                            ]
                                        }
                                    },
                                    # OR subagency matches parent agency
                                    {
                                        "nested": {
                                            "path": "agency.subAgency",
                                            "query": {
                                                "term": {
                                                    "agency.subAgency.title.keyword": agency
                                                }
                                            }
                                        }
                                    },
                                    # OR subagency is "N/A"
                                    {
                                        "nested": {
                                            "path": "agency.subAgency",
                                            "query": {
                                                "term": {
                                                    "agency.subAgency.title.keyword": "N/A"
                                                }
                                            }
                                        }
                                    }
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    }
                })
            else:
                # Regular agency + subagency match
                agency_conditions.append({
                    "nested": {
                        "path": "agency",
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {"agency.title.keyword": agency}},
                                    {"nested": {
                                        "path": "agency.subAgency",
                                        "query": {"term": {"agency.subAgency.title.keyword": subagency}}
                                    }}
                                ]
                            }
                        }
                    }
                })
        else:
            # Just agency match (any subagency is fine)
            agency_conditions.append({
                "nested": {
                    "path": "agency",
                    "query": {
                        "term": {"agency.title.keyword": agency}
                    }
                }
            })
    
    return {
        "bool": {
            "should": agency_conditions,
            "minimum_should_match": 1
        }
    }

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
        "global_totals": {
            "global": {},  # This makes the aggregation ignore query/filters
            "aggs": {
                "total_obligations": {"sum": {"field": "obligations"}},
                "program_count": {"value_count": {"field": "cfda.keyword"}}
            }
        },
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

@router.post("/search/programsTable", response_model=ProgramTableWithFacets)
def search_programs(
    request: SearchRequest,
    es: Elasticsearch = Depends(get_elasticsearch)
) -> ProgramTableWithFacets:
    """
    Search programs with faceted filters and pagination.
    """
    query = request.query
    agencySubAgency = request.agencySubAgency
    categorySubcategory = request.categorySubcategory
    assistanceTypes = request.assistanceTypes
    applicantTypes = request.applicantTypes
    page = request.page
    page_size = request.page_size
    sort_field = request.sort_field
    sort_order = request.sort_order

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

        # Get global totals
        global_totals = response["aggregations"]["global_totals"]
        global_total_obligations = global_totals["total_obligations"]["value"]
        global_program_count = global_totals["program_count"]["value"]

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
            global_total_obligations=global_total_obligations,
            global_program_count=global_program_count,
            page=page,
            page_size=page_size,
            facets=facets
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")