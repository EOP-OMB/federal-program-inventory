from pydantic import BaseModel
from typing import Optional

class ProgramTable(BaseModel):
    title: str
    agency: str
    cfda: Optional[str] = None