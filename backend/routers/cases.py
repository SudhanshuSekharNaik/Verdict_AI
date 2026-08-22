import datetime
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from models.schemas import (
    CaseCreateRequest,
    CaseDetail,
    CaseStatus,
    EvidenceCreateRequest,
    EvidenceItem,
    NextTurnResponse,
    ObjectionRequest,
    PartyStatementsRequest,
    SingleStatementRequest,
    WitnessCreateRequest,
    WitnessItem,
)
from orchestration import trial_orchestrator
from services import database, law_service

router = APIRouter(tags=["cases"])


def validate_case_payload(payload: CaseCreateRequest):
    if not payload.title or len(payload.title.strip()) < 3:
        raise HTTPException(
            status_code=422,
            detail="Case title is required and must be at least 3 characters.",
        )
    if not payload.facts or len(payload.facts.strip()) < 30:
        raise HTTPException(
            status_code=422,
            detail="Fact pattern is too limited to conduct a meaningful courtroom simulation. Please add more factual details (at least 30 characters).",
        )
    if not payload.charge_or_dispute or len(payload.charge_or_dispute.strip()) < 3:
        raise HTTPException(
            status_code=422,
            detail="Charge or dispute is required.",
        )
    filing_id = payload.counsel_filing_id or "agent_02"
    opposing_id = payload.counsel_opposing_id or "agent_01"
    if filing_id == opposing_id:
        raise HTTPException(
            status_code=422,
            detail="Filing counsel and Opposing counsel cannot be the same agent. Please select two distinct specialists.",
        )


from agents import lawyer_roster

# --- Counsel Roster Endpoint ---
@router.get("/counsel/roster")
@router.get("/api/counsel/roster")
def get_lawyer_roster(category: Optional[str] = Query(None)):
    """Returns the 14 specialist lawyer profiles, with recommendations for the given category."""
    roster = lawyer_roster.list_all_counsel()
    recommended = lawyer_roster.get_recommended_counsel(category) if category else {"filing": "agent_02", "opposing": "agent_01"}
    return {
        "roster": roster,
        "recommended": recommended,
        "total_specialists": len(roster),
    }


# --- Case Creation & Management ---
@router.post("/cases", response_model=CaseDetail)
@router.post("/api/cases", response_model=CaseDetail)
def create_case(payload: CaseCreateRequest):
    validate_case_payload(payload)
    case = database.create_case_record(
        title=payload.title.strip(),
        facts=payload.facts.strip(),
        charge_or_dispute=payload.charge_or_dispute.strip(),
        case_category=payload.case_category or "criminal",
        counsel_filing_id=payload.counsel_filing_id or "agent_02",
        counsel_opposing_id=payload.counsel_opposing_id or "agent_01",
        simulation_type=payload.simulation_type or "standard",
        jurisdiction=payload.jurisdiction or "Sessions Court, Bhubaneswar",
        total_rounds=payload.total_rounds or 3,
        case_type=payload.case_type or "user",
        custom_id=payload.custom_id,
        legal_issues=payload.legal_issues,
    )
    return case


@router.get("/cases/demo", response_model=CaseDetail)
@router.get("/api/cases/demo", response_model=CaseDetail)
def get_demo_case():
    """Returns the stable, single demo case without creating duplicates."""
    return database.get_or_create_demo_case()


@router.get("/cases", response_model=List[CaseDetail])
@router.get("/api/cases", response_model=List[CaseDetail])
def list_cases(
    status: Optional[str] = Query(None, description="Filter by status: all, active, resolved, deliberation, archived"),
    case_type: Optional[str] = Query(None, description="Filter by case_type: user, demo, benchmark"),
    sort_by: str = Query("updated_at", description="Sort by: updated_at, created_at, status"),
):
    return database.list_all_cases(status_filter=status, case_type_filter=case_type, sort_by=sort_by)


@router.get("/cases/dashboard")
@router.get("/api/cases/dashboard")
def dashboard_metrics(include_benchmarks: bool = Query(False)):
    return database.get_dashboard_metrics(include_benchmarks=include_benchmarks)


@router.get("/cases/{case_id}", response_model=CaseDetail)
@router.get("/api/cases/{case_id}", response_model=CaseDetail)
def get_case(case_id: str):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


# --- Evidence Register Endpoints ---
@router.post("/cases/{case_id}/evidence", response_model=EvidenceItem)
@router.post("/api/cases/{case_id}/evidence", response_model=EvidenceItem)
def register_evidence(case_id: str, payload: EvidenceCreateRequest):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    item = database.add_case_evidence(case_id, payload.model_dump())
    database.save_courtroom_event(
        case_id=case_id,
        stage="pre_trial_evidence",
        event_type="EVIDENCE_SUBMITTED",
        speaker=payload.submitted_by,
        content=f"Exhibit {item.id} ('{item.title}') registered by {payload.submitted_by.upper()}.",
        evidence_id=item.id,
    )
    return item


@router.get("/cases/{case_id}/evidence", response_model=List[EvidenceItem])
@router.get("/api/cases/{case_id}/evidence", response_model=List[EvidenceItem])
def get_case_evidence(case_id: str):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return database.get_case_evidence(case_id)


@router.patch("/cases/{case_id}/evidence/{evidence_id}/status")
@router.patch("/api/cases/{case_id}/evidence/{evidence_id}/status")
def update_evidence_status(case_id: str, evidence_id: str, status: str = Query(...)):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    database.update_evidence_status(evidence_id, status)
    return {"evidence_id": evidence_id, "status": status}


# --- Witness Register Endpoints ---
@router.post("/cases/{case_id}/witnesses", response_model=WitnessItem)
@router.post("/api/cases/{case_id}/witnesses", response_model=WitnessItem)
def register_witness(case_id: str, payload: WitnessCreateRequest):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    w_prefix = "PW" if payload.called_by == "prosecution" else "DW"
    count = len([w for w in case.witnesses_list if w.called_by == payload.called_by]) + 1
    w_id = payload.id if payload.id else f"{w_prefix}-0{count}"
    
    w_data = payload.model_dump()
    w_data["id"] = w_id
    item = database.add_case_witness(case_id, w_data)
    database.save_courtroom_event(
        case_id=case_id,
        stage="pre_trial_witnesses",
        event_type="WITNESS_ADDED",
        speaker=payload.called_by,
        content=f"Witness {item.name} ({item.id}) cited by {payload.called_by.upper()}.",
        witness_id=item.id,
    )
    return item


@router.get("/cases/{case_id}/witnesses", response_model=List[WitnessItem])
@router.get("/api/cases/{case_id}/witnesses", response_model=List[WitnessItem])
def get_case_witnesses(case_id: str):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return database.get_case_witnesses(case_id)


# --- Pre-Trial Party Statements Endpoints ---
@router.post("/cases/{case_id}/statements", response_model=CaseDetail)
@router.post("/api/cases/{case_id}/statements", response_model=CaseDetail)
def record_party_statements(case_id: str, payload: PartyStatementsRequest):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    database.save_single_party_statement(
        case_id=case_id,
        speaker="prosecution",
        incident_account=payload.prosecution_statement.strip(),
        key_allegations=payload.prosecution_allegations or [],
        what_is_disputed=payload.prosecution_disputed or "",
        theory_of_case=payload.prosecution_theory or "",
        desired_outcome=payload.prosecution_outcome or "",
        facts_relied_upon=payload.prosecution_facts_relied or [],
    )
    database.save_single_party_statement(
        case_id=case_id,
        speaker="defense",
        incident_account=payload.defense_statement.strip(),
        key_allegations=payload.defense_disputes or [],
        what_is_disputed=payload.defense_disputed or "",
        theory_of_case=payload.defense_theory or "",
        desired_outcome=payload.defense_outcome or "",
        facts_relied_upon=payload.defense_facts_relied or [],
    )
    return database.get_case_by_id(case_id)


@router.post("/cases/{case_id}/statement/single", response_model=CaseDetail)
@router.post("/api/cases/{case_id}/statement/single", response_model=CaseDetail)
def record_single_statement(case_id: str, payload: SingleStatementRequest):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    updated_case = database.save_single_party_statement(
        case_id=case_id,
        speaker=payload.speaker.lower(),
        incident_account=payload.incident_account.strip(),
        key_allegations=payload.key_allegations or [],
        what_is_disputed=payload.what_is_disputed or "",
        theory_of_case=payload.theory_of_case or "",
        desired_outcome=payload.desired_outcome or "",
        facts_relied_upon=payload.facts_relied_upon or [],
        evidence_relied_upon=payload.evidence_relied_upon or [],
        witnesses_relied_upon=payload.witnesses_relied_upon or [],
    )
    return updated_case


@router.get("/cases/{case_id}/legal-analysis")
@router.get("/api/cases/{case_id}/legal-analysis")
def get_case_legal_analysis(case_id: str):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return {
        "case_id": case.id,
        "title": case.title,
        "charge": case.charge_or_dispute,
        "legal_issues": case.legal_issues,
        "applicable_laws": case.applicable_laws,
        "statements_recorded": bool(case.statements),
        "statements": case.statements,
    }


# --- Turn-Based Trial Endpoints ---
@router.post("/cases/{case_id}/trial/start", response_model=CaseDetail)
@router.post("/api/cases/{case_id}/trial/start", response_model=CaseDetail)
def start_trial(case_id: str):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    conn = database.get_db_connection()
    with conn:
        if case.status == CaseStatus.RESOLVED:
            conn.execute("DELETE FROM verdicts WHERE case_id = ?", (case_id,))
            conn.execute("DELETE FROM courtroom_events WHERE case_id = ?", (case_id,))
            conn.execute("DELETE FROM arguments WHERE case_id = ?", (case_id,))
            conn.execute(
                "UPDATE case_witnesses SET status = 'ready_to_call', testimony_turns = '[]' WHERE case_id = ?",
                (case_id,),
            )
            conn.execute(
                "UPDATE case_evidence SET status = 'ready_to_offer' WHERE case_id = ?",
                (case_id,),
            )

        conn.execute(
            "UPDATE cases SET status = ?, current_stage = 'court_opening', current_speaker = 'judge', current_witness_id = 'PW-01', updated_at = ? WHERE id = ?",
            (CaseStatus.TRIAL_IN_PROGRESS.value, datetime.datetime.utcnow().isoformat(), case_id),
        )
    conn.close()
    return database.get_case_by_id(case_id)


@router.post("/cases/{case_id}/trial/reset", response_model=CaseDetail)
@router.post("/api/cases/{case_id}/trial/reset", response_model=CaseDetail)
def reset_trial(case_id: str):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    conn = database.get_db_connection()
    with conn:
        conn.execute(
            "UPDATE cases SET status = ?, current_stage = 'court_opening', current_speaker = 'judge', current_witness_id = 'PW-01', updated_at = ? WHERE id = ?",
            (CaseStatus.TRIAL_IN_PROGRESS.value, datetime.datetime.utcnow().isoformat(), case_id),
        )
        conn.execute("DELETE FROM verdicts WHERE case_id = ?", (case_id,))
        conn.execute("DELETE FROM courtroom_events WHERE case_id = ?", (case_id,))
        conn.execute("DELETE FROM arguments WHERE case_id = ?", (case_id,))
        conn.execute(
            "UPDATE case_witnesses SET status = 'ready_to_call', testimony_turns = '[]' WHERE case_id = ?",
            (case_id,),
        )
        conn.execute(
            "UPDATE case_evidence SET status = 'ready_to_offer' WHERE case_id = ?",
            (case_id,),
        )
    conn.close()
    return database.get_case_by_id(case_id)


@router.post("/cases/{case_id}/trial/next-turn", response_model=NextTurnResponse)
@router.post("/api/cases/{case_id}/trial/next-turn", response_model=NextTurnResponse)
@router.post("/cases/{case_id}/trial/step", response_model=NextTurnResponse)
@router.post("/api/cases/{case_id}/trial/step", response_model=NextTurnResponse)
def trial_next_turn(case_id: str):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.status == CaseStatus.RESOLVED:
        return NextTurnResponse(
            case_id=case.id,
            status=case.status,
            current_stage=case.current_stage,
            current_speaker=None,
            current_witness_id=None,
            current_round=case.current_round,
            total_rounds=case.total_rounds,
            is_completed=True,
            verdict=case.verdict,
            next_action_prompt="Trial is resolved.",
            audit_event="TRIAL_RESOLVED",
        )

    try:
        response = trial_orchestrator.execute_next_turn(case_id)
        return response
    except Exception as e:
        database.save_courtroom_event(
            case_id=case_id,
            stage="error",
            event_type="TURN_EXECUTION_ERROR",
            content=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Agent turn generation failed: {str(e)}. You can retry this turn.",
        )


@router.post("/cases/{case_id}/trial/objection")
@router.post("/api/cases/{case_id}/trial/objection")
def trial_objection(case_id: str, payload: ObjectionRequest):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        res = trial_orchestrator.handle_objection(
            case_id=case_id,
            raised_by=payload.raised_by,
            ground=payload.ground,
            question_text=payload.question_text,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Objection processing failed: {str(e)}")


@router.post("/cases/{case_id}/trial/introduce-evidence")
@router.post("/api/cases/{case_id}/trial/introduce-evidence")
def trial_introduce_evidence(case_id: str, evidence_id: str = Query(...)):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        res = trial_orchestrator.handle_introduce_evidence(case_id=case_id, evidence_id=evidence_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence introduction failed: {str(e)}")


@router.post("/cases/{case_id}/run", response_model=CaseDetail)
@router.post("/api/cases/{case_id}/run", response_model=CaseDetail)
def run_full_case(case_id: str):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.status == CaseStatus.RESOLVED:
        return case

    try:
        updated_case = trial_orchestrator.execute_full_case_sync(case_id)
        return updated_case or case
    except Exception as e:
        rec = database.get_case_by_id(case_id)
        if rec:
            return rec
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


# --- Final Case Report & Export Endpoint ---
@router.get("/cases/{case_id}/report")
@router.get("/api/cases/{case_id}/report")
def get_final_case_report(case_id: str):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {
        "case_summary": {
            "docket_number": case.docket_number,
            "title": case.title,
            "charge": case.charge_or_dispute,
            "jurisdiction": case.jurisdiction,
            "category": case.case_category,
            "simulation_type": case.simulation_type,
            "status": case.status.value,
            "created_at": case.created_at,
            "resolved_at": case.updated_at,
        },
        "case_facts": [f.content for f in case.facts_list],
        "evidence_register": case.evidence_list,
        "witness_register": case.witnesses_list,
        "party_statements": case.statements,
        "applicable_laws": case.applicable_laws,
        "legal_issues": case.legal_issues,
        "courtroom_events": case.courtroom_events,
        "arguments": case.arguments,
        "verdict": case.verdict,
        "ai_disclaimer": "AI-generated courtroom simulation for research and educational purposes. Not binding legal advice or real judicial judgment.",
    }


@router.post("/cases/{case_id}/export")
@router.post("/api/cases/{case_id}/export")
@router.get("/cases/{case_id}/export")
@router.get("/api/cases/{case_id}/export")
def export_case(case_id: str, format: str = Query("markdown", pattern="^(markdown|json|text)$")):
    case = database.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if format == "json":
        return case.model_dump()

    lines = [
        f"# {case.docket_number}: {case.title}",
        f"**Court / Jurisdiction:** {case.jurisdiction} | **Category:** {case.case_category.upper()}  ",
        f"**Charge / Dispute:** {case.charge_or_dispute}  ",
        f"**Status:** {case.status.value.upper()}  ",
        f"**Date:** {case.created_at}  ",
        "",
        "> [!NOTE]",
        "> AI-generated courtroom simulation for research and educational purposes inspired by BNSS & BSA frameworks.",
        "",
        "## 1. Canonical Case Facts (Authoritative Record)",
        case.facts,
        "",
        "### Indexed Fact Statements",
    ]

    for f in case.facts_list:
        lines.append(f"- **[Fact #{f.fact_index}]**: {f.content}")

    lines.append("\n## 2. Evidence Register & Exhibits\n")
    for ev in case.evidence_list:
        hash_info = f" | Hash: `{ev.file_hash}`" if ev.file_hash != "NOT PROVIDED" else ""
        lines.append(f"- **[{ev.id}] {ev.title}** ({ev.evidence_type}) — Status: `{ev.status.upper()}`{hash_info}")
        lines.append(f"  *Description:* {ev.description}")
        lines.append(f"  *Source:* {ev.source} | *Submitted by:* {ev.submitted_by.upper()}")

    lines.append("\n## 3. Witness Register\n")
    for w in case.witnesses_list:
        lines.append(f"- **[{w.id}] {w.name}** ({w.role}) — Called by: `{w.called_by.upper()}` | Status: `{w.status.upper()}`")
        lines.append(f"  *Scope:* {w.expected_testimony}")

    if case.statements:
        lines.append("\n## 4. Pre-Trial Positions\n")
        if case.statements.prosecution:
            p = case.statements.prosecution
            lines.append("### 🔴 Prosecution Position")
            lines.append(f"**Theory:** {p.theory_of_case}\n")
            lines.append(f"**Account:** {p.incident_account}\n")
        if case.statements.defense:
            d = case.statements.defense
            lines.append("\n### 🔵 Defense Position")
            lines.append(f"**Theory:** {d.theory_of_case}\n")
            lines.append(f"**Account:** {d.incident_account}\n")

    lines.append("\n## 5. Applicable Legal Framework\n")
    for law in case.applicable_laws:
        lines.append(f"- **{law.act} ({law.section_or_article} — {law.title})**: {law.plain_explanation}")

    lines.append("\n## 6. Procedural Courtroom Events & Testimony\n")
    for evt in case.courtroom_events:
        lines.append(f"### `[{evt.stage.upper()}]` {evt.event_type} — {evt.speaker or 'COURT'}")
        lines.append(f"{evt.content}\n")

    if case.verdict:
        lines.append("## 7. Court's Final Judgment & Holdings\n")
        lines.append(f"**Holding:** {case.verdict.decision}  ")
        lines.append(f"**Outcome:** {case.verdict.winner.replace('_', ' ').title()}  ")
        lines.append(f"**Confidence:** {int(float(case.verdict.confidence)*100 if isinstance(case.verdict.confidence, (int, float)) else 85)}%  ")
        lines.append(f"**Decision Basis:** {case.verdict.decision_basis}\n")

        if case.verdict.issue_findings:
            lines.append("### Findings on Framed Issues:")
            for fnd in case.verdict.issue_findings:
                lines.append(f"- **{fnd.question}**: `{fnd.finding}` — {fnd.rationale}")

        if case.verdict.reasoning_summary:
            lines.append(f"\n### Full Judicial Opinion:\n{case.verdict.reasoning_summary}")

    md_content = "\n".join(lines)
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={case.id}_case_report.md"},
    )
