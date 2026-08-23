import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.evidence import EvidencePartyEnum, EvidenceStatusEnum


class EvidenceCreate(BaseModel):
    title: str = Field(..., example="Rental Agreement dated 01 July 2024")
    party: EvidencePartyEnum = Field(default=EvidencePartyEnum.PLAINTIFF)
    document_type: str = Field(..., example="CONTRACT")
    source: str = Field(default="UPLOAD", example="UPLOAD")


class EvidenceChunkResponse(BaseModel):
    id: uuid.UUID
    chunk_index: int
    chunk_text: str
    metadata_json: Dict[str, Any]

    class Config:
        from_attributes = True


class EvidenceResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    party: EvidencePartyEnum
    title: str
    document_type: str
    source: str
    verification_status: EvidenceStatusEnum
    file_hash: str
    file_path: Optional[str]
    mime_type: Optional[str]
    file_size: Optional[int]
    extraction_metadata: Dict[str, Any]
    extracted_text: Optional[str]
    chunks: Optional[List[EvidenceChunkResponse]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimelineEventResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    event_date: Optional[datetime]
    date_raw_str: str
    title: str
    description: str
    party: str
    source_evidence_id: Optional[uuid.UUID]
    conflict_flag: bool
    conflict_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # PARTY, CLAIM, EVIDENCE, EVENT, LEGAL_ISSUE
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str  # SUPPORTS, CONTRADICTS, CLAIMS, TENDERS, OCCURRED_ON
    properties: Dict[str, Any] = Field(default_factory=dict)


class EvidenceGraphResponse(BaseModel):
    case_id: uuid.UUID
    nodes: List[GraphNode]
    edges: List[GraphEdge]
