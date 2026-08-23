import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.case import CaseStatusEnum, CaseTypeEnum


class CaseBase(BaseModel):
    title: str = Field(..., example="Security Deposit Dispute - Kumar vs. Sharma")
    case_type: str = Field(default="CIVIL", example="CIVIL")
    jurisdiction: str = Field(..., example="Delhi State Consumer Disputes Redressal Commission")
    description: str = Field(..., example="Tenant seeking return of ₹50,000 security deposit withheld for alleged property damages.")
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CaseCreate(CaseBase):
    plaintiff_name: Optional[str] = Field(None, example="Rahul Kumar")
    defendant_name: Optional[str] = Field(None, example="Suresh Sharma")
    disputed_amount: Optional[float] = Field(None, example=50000.0)


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    case_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CaseStatusEnum] = None
    metadata_json: Optional[Dict[str, Any]] = None


class CaseResponse(BaseModel):
    id: uuid.UUID
    case_number: str
    title: str
    case_type: str
    jurisdiction: str
    description: str
    status: CaseStatusEnum
    metadata_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseIntakeRequest(BaseModel):
    narrative: str = Field(
        ...,
        description="Natural language description of the dispute or legal facts",
        example="I rented an apartment from Mr. Suresh Sharma in Delhi. I paid ₹50,000 security deposit on 1st July 2024. I vacated on 30th June 2025. He deducted ₹35,000 claiming wall damages, but I have move-out photos showing the property was in pristine condition.",
    )
    jurisdiction_hint: Optional[str] = Field(None, example="Delhi")


class CaseIntakeResponse(BaseModel):
    title: str
    case_type: str
    jurisdiction: str
    description: str
    plaintiff_name: Optional[str]
    defendant_name: Optional[str]
    disputed_amount: Optional[float]
    claims: List[Dict[str, Any]]
    counterclaims: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    disputed_facts: List[str]
    undisputed_facts: List[str]
    confidence_score: float
    analysis_notes: str