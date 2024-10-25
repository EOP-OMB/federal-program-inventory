from fastapi import APIRouter, Depends, HTTPException
from elasticsearch import Elasticsearch, NotFoundError
from app.models.programTable import SearchResponse, ProgramTable
from app.dependencies import get_elasticsearch

router = APIRouter(
    prefix="/api",
    tags=["Search"]
)

@router.get("/search/", response_model=SearchResponse)
async def search_programs(query: str = None, es: Elasticsearch = Depends(get_elasticsearch)):
    try:
        if query:
            # If query is provided, perform multi-match search
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"title": {"query": query, "operator": "and"}}},
                            {"match": {"objectives": {"query": query, "operator": "and"}}},
                            {"term": {"cfda": query}},
                            {"match": {"popularName": {"query": query, "operator": "and"}}}
                        ]
                    }
                }
            }
        else:
            # If no query is provided, return all programs
            search_body = {
                "query": {
                    "match_all": {}
                }
            }

        response = es.search(index="programs", body=search_body)
        
        # Extract program data
        programs = [ProgramTable(**hit["_source"]) for hit in response["hits"]["hits"]]
        return SearchResponse(programs=programs)

    except NotFoundError:
        raise HTTPException(status_code=404, detail="Index not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
