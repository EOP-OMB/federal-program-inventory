from fastapi import APIRouter, Depends, HTTPException
from elasticsearch import Elasticsearch, NotFoundError
from app.models.programTable import SearchResponse, ProgramTable
from app.dependencies import get_elasticsearch

router = APIRouter(
    prefix="/api",
    tags=["Search"]
)

@router.get("/search/", response_model=SearchResponse)
async def search_programs(query: str, es: Elasticsearch = Depends(get_elasticsearch)):
    try:
        response = es.search(index="programs", body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "agency", "cfda"]
                }
            }
        })
        # Extract program data
        programs = [Program(**hit["_source"]) for hit in response["hits"]["hits"]]
        return SearchResponse(programs=programs)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Index not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))