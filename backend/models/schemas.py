import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field


class CaseStatus(str, Enum):
    DRAFT = "draft"
    FILED = "filed"
    PRE_TRIAL = "pre_trial"
    STATEMENTS_PENDING = "statements_pending"
    EVIDENCE_PENDING = "evidence_pending"
    WITNESSES_PENDING = "witnesses_pending"
    READY_FOR_HEARING = "ready_for_hearing"
    HEARING_IN_PROGRESS = "hearing_in_progress"
    TRIAL_IN_PROGRESS = "trial_in_progress"  # synonym
    LEGAL_ANALYSIS = "legal_analysis"        # synonym
    DELIBERATION = "deliberation"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class Speaker(str, Enum):
    PROSECUTION = "prosecution"
    DEFENSE = "defense"
    JUDGE = "judge"
    WITNESS = "witness"
    SYSTEM = "system"


class CaseFact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    case_id: str
    fact_index: int
    content: str


class EvidenceStatus(str, Enum):
    SUBMITTED = "submitted"
    OFFERED = "offered"
    MARKED = "marked"
    ADMITTED = "admitted"
    DISPUTED = "disputed"
    EXCLUDED = "excluded"
    WITHDRAWN = "withdrawn"


class EvidenceType(str, Enum):
    DOCUMENT = "document"
    DIGITAL_RECORD = "digital_record"
    PHOTOGRAPH = "photograph"
    VIDEO = "video"
    AUDIO = "audio"
    PHYSICAL_OBJECT = "physical_object"
    FINANCIAL_RECORD = "financial_record"
    MEDICAL_RECORD = "medical_record"
    FORENSIC_REPORT = "forensic_report"
    EXPERT_REPORT = "expert_report"
    OTHER = "other"


class EvidenceItem(BaseModel):
    id: str = Field(default_factory=lambda: f"EX-{str(uuid.uuid4())[:6].upper()}")
    case_id: str
    submitted_by: str = "prosecution"  # "prosecution" or "defense"
    title: str
    evidence_type: str = "document"
    description: str
    source: str = "Case Record"
    date: str = "August 2026"
    supports_facts: List[str] = []
    challenges_issues: List[str] = []
    status: str = "submitted"
    file_hash: Optional[str] = "NOT PROVIDED"
    chain_of_custody: Optional[str] = "NOT PROVIDED"
    device_source: Optional[str] = "NOT PROVIDED"
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class WitnessRole(str, Enum):
    EMPLOYEE = "employee"
    EYEWITNESS = "eyewitness"
    INVESTIGATING_OFFICER = "investigating_officer"
    EXPERT = "expert"
    FORENSIC_ANALYST = "forensic_analyst"
    DOCTOR = "doctor"
    COMPLAINANT = "complainant"
    BANK_OFFICER = "bank_officer"
    OTHER = "other"


class WitnessStatus(str, Enum):
    NOT_CALLED = "not_called"
    ON_STAND = "on_stand"
    EXAMINED = "examined"
    CROSS_EXAMINED = "cross_examined"
    RE_EXAMINED = "re_examined"
    DISCHARGED = "discharged"


class WitnessItem(BaseModel):
    id: str = Field(default_factory=lambda: f"W-{str(uuid.uuid4())[:4].upper()}")
    case_id: str
    called_by: str = "prosecution"  # "prosecution" or "defense"
    name: str
    role: str = "eyewitness"
    connection_to_case: str
    expected_testimony: str
    linked_evidence_ids: List[str] = []
    linked_fact_indices: List[int] = []
    is_expert: bool = False
    status: str = "not_called"
    testimony_turns: List[Dict[str, Any]] = []
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class CourtroomEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{str(uuid.uuid4())[:8]}")
    case_id: str
    stage: str
    event_type: str
    speaker: Optional[str] = None
    witness_id: Optional[str] = None
    content: str
    question_turn: Optional[int] = None
    objection: Optional[Dict[str, Any]] = None
    evidence_id: Optional[str] = None
    evidence_action: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class PartyStatement(BaseModel):
    speaker: Speaker
    incident_account: str
    key_allegations: List[str] = []
    what_is_disputed: Optional[str] = ""
    theory_of_case: Optional[str] = ""
    desired_outcome: Optional[str] = ""
    facts_relied_upon: List[str] = []
    evidence_relied_upon: List[str] = []
    witnesses_relied_upon: List[str] = []
    is_submitted: bool = True
    position_details: Dict[str, Any] = {}
    updated_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class CaseStatements(BaseModel):
    case_id: str
    prosecution: Optional[PartyStatement] = None
    defense: Optional[PartyStatement] = None
    is_locked: bool = False


class LegalIssue(BaseModel):
    issue_id: str
    question: str
    prosecution_position: str = "Supports"
    defense_position: str = "Disputes"
    judge_finding: Optional[str] = "Pending deliberation"
    finding_rationale: Optional[str] = ""


class ApplicableLaw(BaseModel):
    id: str
    act: str
    act_code: str
    section_or_article: str
    type: str = "Section"
    title: str
    official_text: str
    plain_explanation: str
    case_relevance: str
    elements_to_establish: List[str] = []
    is_legacy: bool = False
    legacy_mapping: Optional[str] = None
    source_url: str
    effective_date: str = "1 July 2024"
    verified_date: str = "August 2026"
    applicability_status: str = "Potentially applicable"


class IssueFinding(BaseModel):
    issue_id: str
    question: str
    finding: str  # "Not established" | "Established" | "Potentially established"
    rationale: str
    linked_evidence: List[str] = []
    linked_witnesses: List[str] = []


class LawAssessment(BaseModel):
    provision: str  # e.g. "BNS §303 — Theft"
    status: str     # e.g. "Elements not sufficiently established"
    rationale: str


class Argument(BaseModel):
    id: str = Field(default_factory=lambda: f"arg_{str(uuid.uuid4())[:8]}")
    case_id: str
    round_number: int
    speaker: Speaker
    stage_type: str
    content: str
    argument_type: Optional[str] = "factual evidence"
    argument_strength: Optional[str] = "moderate"
    legal_basis: Optional[str] = "BNS §303 — Theft"
    party_statement_ref: Optional[str] = None
    evidence_references: List[str] = []
    responds_to_argument_id: Optional[str] = None
    is_contradiction_flagged: bool = False
    contradiction_note: Optional[str] = None
    is_unsupported_flagged: bool = False
    unsupported_note: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class TranscriptEntry(BaseModel):
    speaker: Speaker
    stage: str
    text: str
    argument_type: Optional[str] = None
    argument_strength: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class AffirmativeDefenseProng(BaseModel):
    element: str
    finding: str
    evaluation: str
    facts_cited: List[str] = []


class AffirmativeDefenseAnalysis(BaseModel):
    defense_name: str
    prong_1_gravity: Optional[AffirmativeDefenseProng] = None
    prong_2_suddenness_and_interval: Optional[AffirmativeDefenseProng] = None
    overall_determination: str = ""


class Verdict(BaseModel):
    id: str = Field(default_factory=lambda: f"vrd_{str(uuid.uuid4())[:8]}")
    case_id: Optional[str] = None
    winner: Optional[str] = "defense_prevailed"  # "defense_prevailed" | "prosecution_prevailed"
    decision: str                                # "NOT GUILTY" | "GUILTY"
    verdict_category: Optional[str] = "not_guilty"
    confidence: Any = 0.85                      # float or percentage
    decision_basis: Optional[str] = ""
    reasoning_summary: Optional[str] = ""
    issue_findings: List[IssueFinding] = []
    law_assessments: List[LawAssessment] = []
    affirmative_defense_analysis: Optional[Union[AffirmativeDefenseAnalysis, Dict[str, Any]]] = None
    prosecution_strengths: List[str] = []
    defense_strengths: List[str] = []
    key_factors: List[str] = []
    evidence_gaps: List[str] = []
    reasoning: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: f"log_{str(uuid.uuid4())[:8]}")
    case_id: str
    event_type: str
    description: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class CaseCreateRequest(BaseModel):
    title: str = Field(..., description="Case title, e.g. 'State v. Vikram Rao'")
    facts: str = Field(..., description="The fictional/hypothetical fact pattern for the case")
    charge_or_dispute: str = Field(..., description="The charge or civil dispute being adjudicated")
    case_category: str = Field(default="criminal", description="'criminal', 'civil', 'family', 'real_estate', 'corporate', 'cyber', 'intellectual_property', 'taxation', 'constitutional', 'employment', 'environmental', 'human_rights', 'banking'")
    counsel_filing_id: Optional[str] = Field(default="agent_02", description="Specialist counsel ID for filing / state / plaintiff side")
    counsel_opposing_id: Optional[str] = Field(default="agent_01", description="Specialist counsel ID for defense / accused / respondent side")
    simulation_type: str = Field(default="standard", description="'fast', 'standard', 'detailed'")
    jurisdiction: str = Field(default="Sessions Court, Bhubaneswar")
    total_rounds: int = Field(default=3, ge=2, le=5)
    case_type: str = Field(default="user", description="'user', 'demo', or 'benchmark'")
    custom_id: Optional[str] = None
    legal_issues: Optional[List[Dict[str, Any]]] = None


class EvidenceCreateRequest(BaseModel):
    id: Optional[str] = None
    title: str
    evidence_type: str = "document"
    description: str
    source: str = "Case Record"
    date: str = "August 2026"
    submitted_by: str = "prosecution"  # "prosecution" or "defense"
    supports_facts: List[str] = []
    challenges_issues: List[str] = []
    status: Optional[str] = "submitted"
    file_hash: Optional[str] = "NOT PROVIDED"
    chain_of_custody: Optional[str] = "NOT PROVIDED"
    device_source: Optional[str] = "NOT PROVIDED"


class WitnessCreateRequest(BaseModel):
    id: Optional[str] = None
    name: str
    role: str = "eyewitness"
    called_by: str = "prosecution"  # "prosecution" or "defense"
    connection_to_case: str
    expected_testimony: str
    linked_evidence_ids: List[str] = []
    linked_fact_indices: List[int] = []
    is_expert: bool = False
    status: Optional[str] = "not_called"


class ObjectionRequest(BaseModel):
    raised_by: str  # "defense" or "prosecution"
    ground: str     # "leading", "relevance", "speculation", "hearsay", "assumes_facts", "argumentative"
    question_text: str


class SingleStatementRequest(BaseModel):
    speaker: str = Field(..., description="'prosecution' or 'defense'")
    incident_account: str
    key_allegations: List[str] = []
    what_is_disputed: Optional[str] = ""
    theory_of_case: Optional[str] = ""
    desired_outcome: Optional[str] = ""
    facts_relied_upon: List[str] = []
    evidence_relied_upon: List[str] = []
    witnesses_relied_upon: List[str] = []


class PartyStatementsRequest(BaseModel):
    prosecution_statement: str
    prosecution_allegations: List[str] = []
    prosecution_disputed: Optional[str] = ""
    prosecution_theory: Optional[str] = ""
    prosecution_outcome: Optional[str] = ""
    prosecution_facts_relied: List[str] = []
    prosecution_position: Dict[str, Any] = {}

    defense_statement: str
    defense_disputes: List[str] = []
    defense_disputed: Optional[str] = ""
    defense_theory: Optional[str] = ""
    defense_outcome: Optional[str] = ""
    defense_facts_relied: List[str] = []
    defense_position: Dict[str, Any] = {}


class NextTurnResponse(BaseModel):
    case_id: str
    status: CaseStatus
    current_stage: str
    current_speaker: Optional[str] = None
    current_witness_id: Optional[str] = None
    current_round: int
    total_rounds: int
    is_completed: bool
    new_argument: Optional[Argument] = None
    courtroom_event: Optional[CourtroomEvent] = None
    verdict: Optional[Verdict] = None
    next_action_prompt: Optional[str] = None
    audit_event: Optional[str] = None


class CaseDetail(BaseModel):
    id: str
    docket_number: str
    title: str
    facts: str
    charge_or_dispute: str
    case_category: str = "criminal"
    counsel_filing_id: str = "agent_02"
    counsel_opposing_id: str = "agent_01"
    simulation_type: str = "standard"
    jurisdiction: str = "Sessions Court, Bhubaneswar"
    total_rounds: int = 3
    case_type: str = "user"
    status: CaseStatus = CaseStatus.FILED
    current_stage: str = "case_filed"
    current_speaker: Optional[str] = "prosecution"
    current_witness_id: Optional[str] = None
    current_round: int = 1
    facts_list: List[CaseFact] = []
    evidence_list: List[EvidenceItem] = []
    witnesses_list: List[WitnessItem] = []
    statements: Optional[CaseStatements] = None
    legal_issues: List[LegalIssue] = []
    applicable_laws: List[ApplicableLaw] = []
    arguments: List[Argument] = []
    courtroom_events: List[CourtroomEvent] = []
    transcript: List[TranscriptEntry] = []
    verdict: Optional[Verdict] = None
    audit_logs: List[AuditLog] = []
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


# Alias for backward compatibility
Case = CaseDetail
