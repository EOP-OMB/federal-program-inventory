from pydantic import BaseModel
from typing import List, Optional

class Program(BaseModel):
    cfda: str
    title: str
    permalink: str
    agency: str
    subAgency: Optional[str]
    obligations: Optional[float]
    objectives: Optional[str]
    popularName: Optional[str]
    assistanceTypes: Optional[List[str]]
    applicantTypes: Optional[List[str]]
    categories: Optional[List[str]]

class ProgramTable(BaseModel):
    programs: List[Program]
    total_obligations: float
    count: int
    page: int
    page_size: int
