import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents.defence_agent import DefenceAgent
from agents.evidence_agent import EvidenceAgent
from agents.judge_assistant import JudgeAssistantAgent
from agents.plaintiff_agent import PlaintiffAgent
from agents.research_agent import LegalResearchAgent
from agents.validation_agent import ValidationAgent
from app.models.argument import Argument, AttackTypeEnum
from app.models.case import Case
from app.models.courtroom import CourtroomEvent, CourtroomRound, CourtroomStageEnum
from rag.citation_validator import CitationValidator


STAGE_PROGRESSION = [
    CourtroomStageEnum.CASE_OPENED,
    CourtroomStageEnum.CASE_PREPARATION,
    CourtroomStageEnum.EVIDENCE_SUBMISSION,
    CourtroomStageEnum.OPENING_ARGUMENTS,
    CourtroomStageEnum.PLAINTIFF_ARGUMENT,
    CourtroomStageEnum.DEFENCE_ARGUMENT,
    CourtroomStageEnum.CROSS_EXAMINATION,
    CourtroomStageEnum.PLAINTIFF_REBUTTAL,
    CourtroomStageEnum.DEFENCE_REBUTTAL,
    CourtroomStageEnum.FINAL_SUBMISSIONS,
    CourtroomStageEnum.JUDGE_QUESTIONS,
    CourtroomStageEnum.JUDGE_DELIBERATION,
    CourtroomStageEnum.VERDICT,
    CourtroomStageEnum.CASE_CLOSED,
]


def _make_turn_id(case_id: uuid.UUID, stage: CourtroomStageEnum) -> str:
    return hashlib.sha256(f"{case_id}:{stage.value}".encode()).hexdigest()[:16]


def _build_evidence_label(ev: Dict[str, Any], index: int, party_prefix: str) -> str:
    short_id = str(ev.get("id", ""))[:8]
    return f"{party_prefix}-{index:03d} [{short_id}]"


def _format_structured_argument(data: Dict[str, Any], confidence: Dict[str, float]) -> str:
    lines = []

    if data.get("claim"):
        lines.append(f"CLAIM:\n{data['claim']}")

    issues = data.get("issues", [])
    if issues:
        lines.append(f"\nISSUES FOR DETERMINATION:")
        for i, issue in enumerate(issues, 1):
            lines.append(f"  {i}. {issue}")

    legal_rules = data.get("legal_rules", [])
    if legal_rules:
        lines.append(f"\nAPPLICABLE LAW:")
        for rule in legal_rules:
            lines.append(f"  - {rule}")

    facts = data.get("material_facts", [])
    if facts:
        lines.append(f"\nMATERIAL FACTS:")
        for fact in facts:
            lines.append(f"  - {fact}")

    evidence = data.get("evidence_analysis", [])
    if evidence:
        lines.append(f"\nEVIDENCE ANALYSIS:")
        for ev in evidence:
            lines.append(f"  {ev['label']}: {ev['analysis']}")

    conflicts = data.get("conflicts", [])
    if conflicts:
        lines.append(f"\nCONFLICTS WITH OPPOSING CASE:")
        for c in conflicts:
            lines.append(f"  - {c}")

    application = data.get("application", "")
    if application:
        lines.append(f"\nAPPLICATION OF LAW TO FACTS:\n{application}")

    counterargs = data.get("counterarguments", [])
    if counterargs:
        lines.append(f"\nCOUNTERARGUMENTS ANTICIPATED:")
        for ca in counterargs:
            lines.append(f"  - {ca}")

    rebuttals = data.get("rebuttals", [])
    if rebuttals:
        lines.append(f"\nREBUTTAL:")
        for rb in rebuttals:
            lines.append(f"  - {rb}")

    relief = data.get("relief", "")
    if relief:
        lines.append(f"\nREQUESTED RELIEF:\n{relief}")

    lines.append(f"\nCONFIDENCE:")
    lines.append(f"  Legal proposition support: {confidence.get('legal', 0):.0%}")
    lines.append(f"  Evidence grounding: {confidence.get('evidence', 0):.0%}")
    lines.append(f"  Citation verification: {confidence.get('citations', 0):.0%}")
    lines.append(f"  Overall: {confidence.get('overall', 0):.0%}")

    return "\n".join(lines)


class CourtroomOrchestrator:
    """Multi-Agent Courtroom Orchestrator: adversarial, citation-verified, deduplicated."""

    @staticmethod
    async def run_courtroom_step(
        db: AsyncSession, case_id: uuid.UUID, target_stage: Optional[str] = None
    ) -> Dict[str, Any]:
        case_res = await db.execute(
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.parties),
                selectinload(Case.evidence_list),
                selectinload(Case.events),
                selectinload(Case.courtroom_rounds),
                selectinload(Case.claims),
            )
        )
        case = case_res.scalars().first()
        if not case:
            raise ValueError(f"Case {case_id} not found")

        p_evidence = await EvidenceAgent.get_party_admitted_evidence(db, case_id, "PLAINTIFF")
        d_evidence = await EvidenceAgent.get_party_admitted_evidence(db, case_id, "DEFENDANT")

        evidence_map = {}
        for i, ev in enumerate(p_evidence, 1):
            evidence_map[str(ev.get("id", ""))] = _build_evidence_label(ev, i, "P")
        for i, ev in enumerate(d_evidence, 1):
            evidence_map[str(ev.get("id", ""))] = _build_evidence_label(ev, i, "D")

        research_res = await LegalResearchAgent.research_issue(
            db=db, issue=case.case_type, case_facts=case.description, jurisdiction=case.jurisdiction
        )
        authorities = research_res.get("authorities", [])

        verified_authorities = []
        for auth in authorities:
            cit_str = auth.get("citation", "")
            if cit_str:
                val = await CitationValidator.validate_citation(
                    db=db, citation_str=cit_str, proposition=case.description
                )
                auth["verification"] = val
                if val["status"] in ("VERIFIED", "PARTIALLY_SUPPORTED"):
                    verified_authorities.append(auth)
            else:
                auth["verification"] = {"status": "UNVERIFIED", "confidence": 0.0}

        rounds = case.courtroom_rounds

        if target_stage:
            try:
                stage_enum = CourtroomStageEnum(target_stage)
            except ValueError:
                stage_enum = CourtroomStageEnum.OPENING_ARGUMENTS
        elif rounds:
            completed_stages = {r.stage for r in rounds if r.is_completed}
            stage_enum = CourtroomStageEnum.CASE_CLOSED
            for s in STAGE_PROGRESSION:
                if s not in completed_stages and s not in (
                    CourtroomStageEnum.CASE_OPENED,
                    CourtroomStageEnum.CASE_PREPARATION,
                    CourtroomStageEnum.EVIDENCE_SUBMISSION,
                ):
                    stage_enum = s
                    break
        else:
            stage_enum = CourtroomStageEnum.OPENING_ARGUMENTS

        turn_id = _make_turn_id(case_id, stage_enum)

        for r in rounds:
            if r.stage == stage_enum and r.is_completed:
                existing_events = [
                    {"id": str(e.id), "speaker": e.speaker, "event_type": e.event_type,
                     "content": e.content, "references": e.references,
                     "evidence_chips": (e.metadata_json or {}).get("evidence_labels", [])}
                    for e in r.events
                ]
                return {
                    "round_id": str(r.id), "round_number": r.round_number,
                    "stage": r.stage.value, "active_speaker": r.active_speaker,
                    "events": existing_events, "deduplicated": True, "turn_id": turn_id,
                }

        round_number = len(rounds) + 1
        db_round = CourtroomRound(
            case_id=case_id, round_number=round_number, stage=stage_enum,
            active_speaker=_active_speaker_for_stage(stage_enum),
            is_completed=True, metadata_json={"turn_id": turn_id},
        )
        db.add(db_round)
        await db.flush()

        existing_events = await _get_previous_opponent_events(db, case_id, stage_enum)

        events_generated: List[Dict[str, Any]] = []

        if stage_enum == CourtroomStageEnum.OPENING_ARGUMENTS:
            events_generated = await _generate_opening_statements(
                db, db_round, case_id, case, p_evidence, d_evidence,
                evidence_map, verified_authorities, turn_id,
            )
        elif stage_enum == CourtroomStageEnum.PLAINTIFF_ARGUMENT:
            events_generated = await _generate_plaintiff_argument(
                db, db_round, case_id, case, p_evidence, evidence_map,
                verified_authorities, turn_id,
            )
        elif stage_enum == CourtroomStageEnum.DEFENCE_ARGUMENT:
            events_generated = await _generate_defence_argument(
                db, db_round, case_id, case, d_evidence, evidence_map,
                verified_authorities, turn_id, existing_events,
            )
        elif stage_enum == CourtroomStageEnum.CROSS_EXAMINATION:
            events_generated = await _generate_cross_examination(
                db, db_round, case_id, case, p_evidence, d_evidence,
                evidence_map, existing_events, turn_id,
            )
        elif stage_enum == CourtroomStageEnum.PLAINTIFF_REBUTTAL:
            events_generated = await _generate_plaintiff_rebuttal(
                db, db_round, case_id, case, p_evidence, evidence_map,
                verified_authorities, turn_id, existing_events,
            )
        elif stage_enum == CourtroomStageEnum.DEFENCE_REBUTTAL:
            events_generated = await _generate_defence_rebuttal(
                db, db_round, case_id, case, d_evidence, evidence_map,
                verified_authorities, turn_id, existing_events,
            )
        elif stage_enum in (CourtroomStageEnum.FINAL_SUBMISSIONS, CourtroomStageEnum.JUDGE_DELIBERATION):
            events_generated = await _generate_judge_assistant_brief(
                db, db_round, case_id, turn_id
            )

        await db.commit()
        await db.refresh(db_round)

        return {
            "round_id": str(db_round.id), "round_number": db_round.round_number,
            "stage": db_round.stage.value, "active_speaker": db_round.active_speaker,
            "events": events_generated, "deduplicated": False, "turn_id": turn_id,
        }


async def _get_previous_opponent_events(db, case_id, current_stage):
    plaintiff_stages = {
        CourtroomStageEnum.PLAINTIFF_ARGUMENT, CourtroomStageEnum.PLAINTIFF_REBUTTAL,
    }
    defence_stages = {
        CourtroomStageEnum.DEFENCE_ARGUMENT, CourtroomStageEnum.DEFENCE_REBUTTAL,
    }

    if current_stage in plaintiff_stages:
        target_speakers = {"DEFENCE_AI"}
    elif current_stage in defence_stages:
        target_speakers = {"PLAINTIFF_AI"}
    else:
        return []

    round_res = await db.execute(
        select(CourtroomRound)
        .where(CourtroomRound.case_id == case_id, CourtroomRound.is_completed == True)
        .order_by(CourtroomRound.created_at.desc())
    )
    all_rounds = round_res.scalars().all()

    events = []
    for r in all_rounds:
        from app.models.courtroom import CourtroomEvent as CE
        ev_res = await db.execute(
            select(CE).where(CE.round_id == r.id)
        )
        for ev in ev_res.scalars().all():
            if ev.speaker in target_speakers:
                events.append({
                    "speaker": ev.speaker, "event_type": ev.event_type,
                    "content": ev.content, "references": ev.references or [],
                })
    return events


def _active_speaker_for_stage(stage: CourtroomStageEnum) -> str:
    if stage in (CourtroomStageEnum.OPENING_ARGUMENTS, CourtroomStageEnum.PLAINTIFF_ARGUMENT,
                 CourtroomStageEnum.PLAINTIFF_REBUTTAL):
        return "PLAINTIFF_AI"
    elif stage in (CourtroomStageEnum.DEFENCE_ARGUMENT, CourtroomStageEnum.DEFENCE_REBUTTAL):
        return "DEFENCE_AI"
    return "JUDGE_ASSISTANT"


async def _compute_confidence(claim, reasoning, evidence_passages, citation_strs, evidence_count, db):
    legal_conf = 0.70
    evidence_conf = 0.50
    citation_conf = 0.50

    if evidence_count >= 3:
        evidence_conf = 0.80
    elif evidence_count >= 1:
        evidence_conf = 0.65

    try:
        nli = get_ml_registry().get_nli()
        if evidence_passages:
            nli_res = nli.verify_grounding(claim=claim, evidence_passages=evidence_passages[:3])
            status = nli_res.get("grounding_status", "")
            if status == "SUPPORTED":
                evidence_conf = 0.90
            elif status == "PARTIALLY_SUPPORTED":
                evidence_conf = 0.70
            elif status == "CONTRADICTION":
                evidence_conf = 0.30
            else:
                evidence_conf = 0.55
    except Exception:
        pass

    verified_count = 0
    for cit_str in citation_strs[:3]:
        try:
            val = await CitationValidator.validate_citation(db=db, citation_str=cit_str, proposition=reasoning)
            if val["status"] == "VERIFIED":
                verified_count += 1
                citation_conf = max(citation_conf, val["confidence"])
            elif val["status"] == "PARTIALLY_SUPPORTED":
                verified_count += 0.5
                citation_conf = max(citation_conf, val["confidence"] * 0.8)
        except Exception:
            pass

    if citation_strs:
        citation_conf = min(0.5 + 0.5 * (verified_count / len(citation_strs)), 0.95)
    else:
        citation_conf = 0.60

    legal_conf = round(0.5 * evidence_conf + 0.5 * citation_conf, 2)
    overall = round(0.4 * evidence_conf + 0.3 * citation_conf + 0.3 * legal_conf, 2)

    return {
        "legal": legal_conf,
        "evidence": evidence_conf,
        "citations": citation_conf,
        "overall": overall,
    }


def _save_argument(db, case_id, db_round, agent, arg_data, confidence, turn_id, evidence_map, ev_ids, cit_ids):
    db_arg = Argument(
        case_id=case_id, round_id=db_round.id, agent=agent,
        claim=arg_data.get("claim", ""), reasoning=json.dumps(arg_data),
        attack_type=AttackTypeEnum.DIRECT_ARGUMENT, confidence=confidence["overall"],
        evidence_ids=ev_ids, citation_ids=cit_ids,
        metadata_json={"turn_id": turn_id, "structured_data": arg_data, "confidence": confidence},
    )
    db.add(db_arg)


async def _generate_opening_statements(
    db, db_round, case_id, case, p_evidence, d_evidence, evidence_map, authorities, turn_id
):
    p_data = await PlaintiffAgent.generate_opening_argument(
        case_title=case.title, case_description=case.description,
        plaintiff_evidence=p_evidence, authorities=authorities,
    )
    p_passages = [e.get("extracted_text", "") for e in p_evidence if e.get("extracted_text")]
    p_citations = [a.get("citation", "") for a in authorities if a.get("citation")]
    p_confidence = await _compute_confidence(
        p_data["claim"], p_data.get("reasoning", ""), p_passages, p_citations, len(p_evidence), db
    )

    _save_argument(db, case_id, db_round, "PLAINTIFF_AGENT", p_data, p_confidence,
                   turn_id, evidence_map, p_data.get("evidence_ids", []), p_data.get("citation_ids", []))

    ev_labels = [evidence_map.get(eid, eid) for eid in p_data.get("evidence_ids", [])]
    p_content = _format_structured_argument(p_data, p_confidence)
    p_content += f"\n\n[turn_id: {turn_id}]"

    ev_p = CourtroomEvent(
        round_id=db_round.id, speaker="PLAINTIFF_AI", event_type="OPENING",
        content=p_content, references=p_data.get("evidence_ids", []),
        metadata_json={"turn_id": turn_id, "evidence_labels": ev_labels,
                       "confidence": p_confidence, "structured_data": p_data},
    )
    db.add(ev_p)

    return [{"speaker": "PLAINTIFF_AI", "content": p_content,
             "references": ev_labels, "turn_id": turn_id, "evidence_chips": ev_labels}]


async def _generate_plaintiff_argument(
    db, db_round, case_id, case, p_evidence, evidence_map, authorities, turn_id
):
    p_data = await PlaintiffAgent.generate_opening_argument(
        case_title=case.title, case_description=case.description,
        plaintiff_evidence=p_evidence, authorities=authorities,
    )
    p_passages = [e.get("extracted_text", "") for e in p_evidence if e.get("extracted_text")]
    p_citations = [a.get("citation", "") for a in authorities if a.get("citation")]
    p_confidence = await _compute_confidence(
        p_data["claim"], p_data.get("reasoning", ""), p_passages, p_citations, len(p_evidence), db
    )

    _save_argument(db, case_id, db_round, "PLAINTIFF_AGENT", p_data, p_confidence,
                   turn_id, evidence_map, p_data.get("evidence_ids", []), p_data.get("citation_ids", []))

    ev_labels = [evidence_map.get(eid, eid) for eid in p_data.get("evidence_ids", [])]
    p_content = _format_structured_argument(p_data, p_confidence)
    p_content += f"\n\n[turn_id: {turn_id}]"

    ev_p = CourtroomEvent(
        round_id=db_round.id, speaker="PLAINTIFF_AI", event_type="ARGUMENT",
        content=p_content, references=p_data.get("evidence_ids", []),
        metadata_json={"turn_id": turn_id, "evidence_labels": ev_labels,
                       "confidence": p_confidence, "structured_data": p_data},
    )
    db.add(ev_p)

    return [{"speaker": "PLAINTIFF_AI", "content": p_content,
             "references": ev_labels, "turn_id": turn_id, "evidence_chips": ev_labels}]


async def _generate_defence_argument(
    db, db_round, case_id, case, d_evidence, evidence_map, authorities, turn_id, plaintiff_events
):
    p_arg_text = ""
    p_structured = None
    for evt in reversed(plaintiff_events):
        meta = {}
        if evt.get("speaker") == "PLAINTIFF_AI":
            p_arg_text = evt.get("content", "")
            break

    d_data = await DefenceAgent.attack_plaintiff_argument(
        target_claim=p_arg_text[:500] if p_arg_text else case.description,
        target_reasoning=p_arg_text,
        defence_evidence=d_evidence,
        authorities=authorities,
    )

    d_passages = [e.get("extracted_text", "") for e in d_evidence if e.get("extracted_text")]
    d_citations = [a.get("citation", "") for a in authorities if a.get("citation")]
    d_confidence = await _compute_confidence(
        d_data["claim"], d_data.get("reasoning", ""), d_passages, d_citations, len(d_evidence), db
    )

    _save_argument(db, case_id, db_round, "DEFENCE_AGENT", d_data, d_confidence,
                   turn_id, evidence_map, d_data.get("evidence_ids", []), d_data.get("citation_ids", []))

    ev_labels = [evidence_map.get(eid, eid) for eid in d_data.get("evidence_ids", [])]
    d_content = _format_structured_argument(d_data, d_confidence)
    d_content += f"\n\n[turn_id: {turn_id}]"

    ev_d = CourtroomEvent(
        round_id=db_round.id, speaker="DEFENCE_AI", event_type="COUNTER-ARGUMENT",
        content=d_content, references=d_data.get("evidence_ids", []),
        metadata_json={"turn_id": turn_id, "evidence_labels": ev_labels,
                       "confidence": d_confidence, "structured_data": d_data},
    )
    db.add(ev_d)

    return [{"speaker": "DEFENCE_AI", "content": d_content,
             "references": ev_labels, "turn_id": turn_id, "evidence_chips": ev_labels}]


async def _generate_plaintiff_rebuttal(
    db, db_round, case_id, case, p_evidence, evidence_map, authorities, turn_id, defence_events
):
    d_arg_text = ""
    for evt in reversed(defence_events):
        if evt.get("speaker") == "DEFENCE_AI":
            d_arg_text = evt.get("content", "")
            break

    p_data = await PlaintiffAgent.attack_defence_argument(
        target_claim=d_arg_text[:500] if d_arg_text else "",
        target_reasoning=d_arg_text,
        plaintiff_evidence=p_evidence,
        authorities=authorities,
    )

    p_passages = [e.get("extracted_text", "") for e in p_evidence if e.get("extracted_text")]
    p_citations = [a.get("citation", "") for a in authorities if a.get("citation")]
    p_confidence = await _compute_confidence(
        p_data["claim"], p_data.get("reasoning", ""), p_passages, p_citations, len(p_evidence), db
    )

    _save_argument(db, case_id, db_round, "PLAINTIFF_AGENT", p_data, p_confidence,
                   turn_id, evidence_map, p_data.get("evidence_ids", []), p_data.get("citation_ids", []))

    ev_labels = [evidence_map.get(eid, eid) for eid in p_data.get("evidence_ids", [])]
    p_content = _format_structured_argument(p_data, p_confidence)
    p_content += f"\n\n[turn_id: {turn_id}]"

    ev_p = CourtroomEvent(
        round_id=db_round.id, speaker="PLAINTIFF_AI", event_type="REBUTTAL",
        content=p_content, references=p_data.get("evidence_ids", []),
        metadata_json={"turn_id": turn_id, "evidence_labels": ev_labels,
                       "confidence": p_confidence, "structured_data": p_data},
    )
    db.add(ev_p)

    return [{"speaker": "PLAINTIFF_AI", "content": p_content,
             "references": ev_labels, "turn_id": turn_id, "evidence_chips": ev_labels}]


async def _generate_defence_rebuttal(
    db, db_round, case_id, case, d_evidence, evidence_map, authorities, turn_id, plaintiff_events
):
    p_arg_text = ""
    for evt in reversed(plaintiff_events):
        if evt.get("speaker") == "PLAINTIFF_AI":
            p_arg_text = evt.get("content", "")
            break

    d_data = await DefenceAgent.attack_plaintiff_argument(
        target_claim=p_arg_text[:500] if p_arg_text else "",
        target_reasoning=p_arg_text,
        defence_evidence=d_evidence,
        authorities=authorities,
    )

    d_passages = [e.get("extracted_text", "") for e in d_evidence if e.get("extracted_text")]
    d_citations = [a.get("citation", "") for a in authorities if a.get("citation")]
    d_confidence = await _compute_confidence(
        d_data["claim"], d_data.get("reasoning", ""), d_passages, d_citations, len(d_evidence), db
    )

    _save_argument(db, case_id, db_round, "DEFENCE_AGENT", d_data, d_confidence,
                   turn_id, evidence_map, d_data.get("evidence_ids", []), d_data.get("citation_ids", []))

    ev_labels = [evidence_map.get(eid, eid) for eid in d_data.get("evidence_ids", [])]
    d_content = _format_structured_argument(d_data, d_confidence)
    d_content += f"\n\n[turn_id: {turn_id}]"

    ev_d = CourtroomEvent(
        round_id=db_round.id, speaker="DEFENCE_AI", event_type="REBUTTAL",
        content=d_content, references=d_data.get("evidence_ids", []),
        metadata_json={"turn_id": turn_id, "evidence_labels": ev_labels,
                       "confidence": d_confidence, "structured_data": d_data},
    )
    db.add(ev_d)

    return [{"speaker": "DEFENCE_AI", "content": d_content,
             "references": ev_labels, "turn_id": turn_id, "evidence_chips": ev_labels}]


async def _generate_cross_examination(
    db, db_round, case_id, case, p_evidence, d_evidence, evidence_map, previous_events, turn_id
):
    p_arg = ""
    d_arg = ""
    for evt in previous_events:
        if evt.get("speaker") == "PLAINTIFF_AI":
            p_arg = evt.get("content", "")
        elif evt.get("speaker") == "DEFENCE_AI":
            d_arg = evt.get("content", "")

    p_q = await PlaintiffAgent.cross_examine_defence(d_arg or case.description, p_evidence)
    d_q = await DefenceAgent.cross_examine_plaintiff(p_arg or case.description, d_evidence)

    ev_p = CourtroomEvent(
        round_id=db_round.id, speaker="PLAINTIFF_AI", event_type="QUESTION",
        content=f"CROSS-EXAMINATION QUESTION TO DEFENCE:\n\n{p_q}",
        metadata_json={"turn_id": turn_id},
    )
    ev_d = CourtroomEvent(
        round_id=db_round.id, speaker="DEFENCE_AI", event_type="QUESTION",
        content=f"CROSS-EXAMINATION QUESTION TO PLAINTIFF:\n\n{d_q}",
        metadata_json={"turn_id": turn_id},
    )
    db.add(ev_p)
    db.add(ev_d)
    return [
        {"speaker": "PLAINTIFF_AI", "content": ev_p.content, "turn_id": turn_id},
        {"speaker": "DEFENCE_AI", "content": ev_d.content, "turn_id": turn_id},
    ]


async def _generate_judge_assistant_brief(db, db_round, case_id, turn_id):
    brief = await JudgeAssistantAgent.prepare_bench_brief(db, case_id)
    contradictions = brief.get("timeline_conflicts", [])
    questions = brief.get("suggested_questions_for_my_lord", [])

    content_lines = [
        f"JUDGE ASSISTANT BRIEF FOR THE BENCH:\n",
        f"Core Legal Issue:\n{brief.get('core_issue', 'N/A')}\n",
        f"Case Type: {brief.get('case_type', 'N/A')}",
        f"Jurisdiction: {brief.get('jurisdiction', 'N/A')}\n",
    ]

    p_claims = brief.get("plaintiff_claims", [])
    d_claims = brief.get("defence_claims", [])
    if p_claims:
        content_lines.append("PLAINTIFF CLAIMS:")
        for c in p_claims:
            content_lines.append(f"  - {c}")
    if d_claims:
        content_lines.append("\nDEFENCE CLAIMS:")
        for c in d_claims:
            content_lines.append(f"  - {c}")

    if contradictions:
        content_lines.append(f"\nTIMELINE CONTRADICTIONS ({len(contradictions)} detected):")
        for tc in contradictions:
            content_lines.append(f"  - {tc.get('event_title', 'Event')} ({tc.get('date', '?')}): {tc.get('notes', '')}")

    ev_summary = brief.get("evidence_summary", {})
    if ev_summary:
        content_lines.append(
            f"\nEVIDENCE SUMMARY: {ev_summary.get('total_exhibits', 0)} total "
            f"({ev_summary.get('plaintiff_exhibits', 0)} plaintiff, "
            f"{ev_summary.get('defence_exhibits', 0)} defence)"
        )

    if questions:
        content_lines.append("\nSUGGESTED QUERIES FOR MY LORD:")
        for q in questions:
            content_lines.append(f"  - {q}")

    content_lines.append(f"\n[turn_id: {turn_id}]")

    ev_j = CourtroomEvent(
        round_id=db_round.id, speaker="JUDGE_ASSISTANT", event_type="RULING",
        content="\n".join(content_lines),
        metadata_json={"turn_id": turn_id},
    )
    db.add(ev_j)
    return [{"speaker": "JUDGE_ASSISTANT", "content": ev_j.content, "turn_id": turn_id}]


from ml import get_ml_registry
