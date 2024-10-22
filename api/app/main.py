from fastapi import FastAPI
from app.routers import search
from app.dependencies import get_elasticsearch

app = FastAPI()

# Elasticsearch dependency injection
app.dependency_overrides[get_elasticsearch] = get_elasticsearch

# Include search router (additional routers can be added here)
app.include_router(search.router)

@app.get("/", tags=["Health Check"])
def health_check():
    return {"message": "API is running"}
