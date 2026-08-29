from pydantic import BaseModel
from typing import List,Dict,Any

class JDInput(BaseModel):
    job_description: str
    user_id: int

class AnalysisResponse(BaseModel):
    extracted_skills:List[str]
    identified_gaps:List[str]
    suggested_focus_area: List[str]
    readiness_score:int
