from pydantic import BaseModel
from typing import List, Optional

class ProgramTable(BaseModel):
    cfda: Optional[str] = None
    title: str
    agency: str
    permalink: str
    agency: str
    obligations: float
    objectives: str
    popularName: str

class SearchResponse(BaseModel):
    programs: List[ProgramTable]