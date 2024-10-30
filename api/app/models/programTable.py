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

class Program(BaseModel):
    cfda: str
    title: str
    permalink: str
    agency: Agency
    obligations: Optional[float]
    objectives: Optional[str]
    popularName: Optional[str]
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
    page: int
    page_size: int
    facets: SearchFacets