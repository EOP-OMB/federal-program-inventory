from fastapi import APIRouter, Depends, HTTPException, Query
from elasticsearch import Elasticsearch, NotFoundError
from app.models.programTable import SearchResponse, ProgramTable
from app.dependencies import get_elasticsearch

router = APIRouter(
    prefix="/api",
    tags=["Search"]
)

@router.get("/search/", response_model=SearchResponse)
async def search_programs(
    query: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    sort_field: str = Query("title", regex="^(title|agency|obligations|objectives)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    es: Elasticsearch = Depends(get_elasticsearch)
):
    try:
        # Calculate pagination offset
        offset = (page - 1) * page_size
        
        # Determine the correct sort field (use .keyword for text fields)
        if sort_field in ["title", "agency", "objectives"]:
            sort_field += ".keyword"

        # Construct the search body with sorting and pagination
        search_body = {
            "from": offset,
            "size": page_size,
            "sort": [{sort_field: {"order": sort_order}}],
            "query": {
                "bool": {
                        "should": [
                            {"wildcard": {"title": f"*{query}*"}},
                            {"wildcard": {"objectives": f"*{query}*"}},
                            {"wildcard": {"cfda": f"*{query}*"}},
                            {"wildcard": {"popularName": f"*{query}*"}}
                        ]
                }
            } if query else {"match_all": {}}
        }

        # Execute the search request
        response = es.search(index="programs", body=search_body)
        
        # Extract the program data from the response
        programs = [ProgramTable(**hit["_source"]) for hit in response["hits"]["hits"]]
        
        # Return the paginated response
        return SearchResponse(
            programs=programs,
            total=response["hits"]["total"]["value"],
            page=page,
            page_size=page_size
        )

    except NotFoundError:
        raise HTTPException(status_code=404, detail="Index not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
