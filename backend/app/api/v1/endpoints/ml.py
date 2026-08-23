from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.schemas.response import APIResponse
from ml import get_ml_registry

router = APIRouter()


class NERRequest(BaseModel):
    text: str = Field(..., example="Rahul Kumar filed a petition under Section 73 of the Indian Contract Act in the Delhi High Court.")


class ClassificationRequest(BaseModel):
    text: str = Field(..., example="Tenant seeking return of security deposit amounting to ₹50,000.")


class SentenceClassificationRequest(BaseModel):
    sentences: List[str] = Field(..., example=["On 01 July 2024, the agreement was executed.", "Plaintiff demands full refund of deposit."])


class NLIRequest(BaseModel):
    claim: str = Field(..., example="The vehicle was 100% accident free.")
    evidence: str = Field(..., example="WhatsApp chat: 'I had an accident in 2023 but repaired it.'")


class GroundingRequest(BaseModel):
    claim: str = Field(..., example="Tenant left property in damaged state.")
    evidence_passages: List[str] = Field(..., example=["Inspection report shows severe wall stains and broken fixtures."])


@router.post("/ner", response_model=APIResponse[List[Dict[str, Any]]])
async def run_legal_ner(req: NERRequest):
    ner = get_ml_registry().get_ner()
    entities = ner.extract_entities(req.text)
    return APIResponse(success=True, data=entities)


@router.post("/classify/case", response_model=APIResponse[Dict[str, Any]])
async def run_case_classification(req: ClassificationRequest):
    classifier = get_ml_registry().get_classifier()
    result = classifier.classify_case(req.text)
    return APIResponse(success=True, data=result)


@router.post("/classify/document", response_model=APIResponse[Dict[str, Any]])
async def run_document_classification(req: ClassificationRequest):
    classifier = get_ml_registry().get_classifier()
    result = classifier.classify_document(req.text)
    return APIResponse(success=True, data=result)


@router.post("/classify/sentences", response_model=APIResponse[List[Dict[str, Any]]])
async def run_sentence_classification(req: SentenceClassificationRequest):
    classifier = get_ml_registry().get_sentence_classifier()
    results = classifier.classify_sentences(req.sentences)
    return APIResponse(success=True, data=results)


@router.post("/nli", response_model=APIResponse[Dict[str, Any]])
async def run_nli_analysis(req: NLIRequest):
    engine = get_ml_registry().get_nli()
    result = engine.analyze_claim_vs_evidence(claim=req.claim, evidence=req.evidence)
    return APIResponse(success=True, data=result)


@router.post("/grounding", response_model=APIResponse[Dict[str, Any]])
async def run_claim_grounding(req: GroundingRequest):
    engine = get_ml_registry().get_nli()
    result = engine.verify_grounding(claim=req.claim, evidence_passages=req.evidence_passages)
    return APIResponse(success=True, data=result)
