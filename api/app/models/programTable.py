from pydantic import BaseModel
from typing import List, Optional, Dict

# Models for nested structures
class SubAgency(BaseModel):
    title: str

class Agency(BaseModel):
    title: str
    subAgency: Optional[SubAgency] = None

class SubCategory(BaseModel):
    title: str

class Category(BaseModel):
    title: str
    subCategory: SubCategory

# Models for the program
class Program(BaseModel):
    cfda: str
    title: str
    permalink: str
    agency: Agency
    obligations: Optional[float]
    objectives: Optional[str]
    popularName: Optional[str]
    assistanceTypes: Optional[List[str]]
    applicantTypes: Optional[List[str]]
    categories: List[Category]

# Models for faceting
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

# Main response models
class ProgramTable(BaseModel):
    programs: List[Program]
    total_obligations: float
    count: int
    page: int
    page_size: int

class ProgramTableWithFacets(ProgramTable):
    facets: SearchFacets