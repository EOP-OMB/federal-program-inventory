from pydantic import BaseModel
from typing import List, Optional

class SubCategory(BaseModel):
    title: str

class Category(BaseModel):
    title: str
    subCategory: SubCategory

class SubAgency(BaseModel):
    title: Optional[str]

class Agency(BaseModel):
    title: str
    subAgency: Optional[SubAgency]

class SearchRequest(BaseModel):
    query: Optional[str] = None
    agencySubAgency: Optional[List[str]] = None
    categorySubcategory: Optional[List[str]] = None
    assistanceTypes: Optional[List[str]] = None
    applicantTypes: Optional[List[str]] = None
    page: int = 1
    page_size: int = 10
    sort_field: str = "title"
    sort_order: str = "asc"

class Program(BaseModel):
    cfda: str
    title: str
    permalink: str
    agency: Agency
    obligations: Optional[float]
    objectives: Optional[str]
    popularName: Optional[str]
    gwo: Optional[str]
    pons: Optional[str]
    assistanceTypes: List[str]
    applicantTypes: List[str]
    categories: List[Category]

class FacetBucket(BaseModel):
    key: str
    doc_count: int

class CategoryFacet(BaseModel):
    title: str
    doc_count: int
    subcategories: List[FacetBucket]

class AgencyFacet(BaseModel):
    title: str
    doc_count: int
    subagencies: List[FacetBucket]

class SearchFacets(BaseModel):
    categories: List[CategoryFacet]
    agencies: List[AgencyFacet]
    assistance_types: List[FacetBucket]
    applicant_types: List[FacetBucket]

class ProgramTableWithFacets(BaseModel):
    programs: List[Program]
    total_obligations: float
    count: int
    global_total_obligations: float
    global_program_count: int
    page: int
    page_size: int
    facets: SearchFacets