from app.routers import search
from app.dependencies import get_elasticsearch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Elasticsearch dependency injection
app.dependency_overrides[get_elasticsearch] = get_elasticsearch

# Include search router (additional routers can be added here)
app.include_router(search.router)


@app.get("/", tags=["Health Check"])
def health_check():
    return {"message": "API is running"}
