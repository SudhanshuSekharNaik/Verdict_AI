import datetime
import json
import time
from typing import Any, Dict, List, Optional
import uuid

from agents import lawyer_roster
from agents.critic_agent import CriticAgent
from agents.defense_agent import DefenseAgent
from agents.judge_agent import JudgeAgent
from agents.prosecution_agent import ProsecutionAgent
from agents.witness_agent import WitnessAgent
from classifiers.argument_classifier import annotate
from models.schemas import (
    Argument,
    CaseDetail,
    CaseStatus,
    CourtroomEvent,
    EvidenceItem,
    NextTurnResponse,
    Speaker,
    Verdict,
    WitnessItem,
)
from services import database, law_service, rag_service


def format_facts_indexed(facts_list) -> str:
    if not facts_list:
        return ""
    lines = ["INDEXED FACT STATEMENTS (for citation as [Fact #N]):"]
    for f in facts_list:
        lines.append(f"[Fact #{f.fact_index}]: {f.content}")
    return "\n".join(lines)


def format_applicable_laws(laws_list) -> str:
    if not laws_list:
        return "Bharatiya Nyaya Sanhita, 2023 (BNS §303 - Theft), Bharatiya Sakshya Adhiniyam, 2023 (BSA §104 - Burden of proof)"
    lines = []
    for l in laws_list:
        lines.append(f"• {l.act} ({l.section_or_article} — {l.title}): {l.plain_explanation}")
    return "\n".join(lines)


def format_evidence(evidence_list) -> str:
    if not evidence_list:
        return "No registered exhibits."
    lines = ["REGISTERED EVIDENCE EXHIBITS:"]
    for e in evidence_list:
        lines.append(f"• [{e.id}] ({e.submitted_by.upper()} — {e.evidence_type}): '{e.title}' — {e.description} (Source: {e.source}, Date: {e.date}, Custody: {e.chain_of_custody})")
    return "\n".join(lines)


def format_witnesses(witnesses_list) -> str:
    if not witnesses_list:
        return "No registered witnesses."
    lines = ["REGISTERED WITNESSES & TESTIMONY SCOPE:"]
    for w in witnesses_list:
        lines.append(f"• [{w.id}] {w.name} (Called by: {w.called_by.upper()}, Role: {w.role}) — Connection: {w.connection_to_case} | Expected Scope: \"{w.expected_testimony}\"")
    return "\n".join(lines)


def format_party_statements(statements) -> str:
    if not statements:
        return "No specific pre-trial party statements recorded."
    lines = []
    if statements.prosecution:
        p = statements.prosecution
        lines.append("🔴 PROSECUTION PRE-TRIAL POSITION (ADVOCACY CLAIM):")
        lines.append(f"Account of Events: {p.incident_account}")
        if p.theory_of_case:
            lines.append(f"Prosecution Theory: {p.theory_of_case}")
        if p.what_is_disputed:
            lines.append(f"Disputes with Defense: {p.what_is_disputed}")
        if p.key_allegations:
            lines.append("Key Allegations: " + "; ".join(p.key_allegations))
        if p.facts_relied_upon:
            lines.append("Key Facts Relied Upon: " + ", ".join(p.facts_relied_upon))
        if p.desired_outcome:
            lines.append(f"Desired Outcome: {p.desired_outcome}")

    if statements.defense:
        d = statements.defense
        lines.append("\n🔵 DEFENSE PRE-TRIAL POSITION (ADVOCACY CLAIM):")
        lines.append(f"Account of Events: {d.incident_account}")
        if d.theory_of_case:
            lines.append(f"Defense Theory: {d.theory_of_case}")
        if d.what_is_disputed:
            lines.append(f"Disputes with Prosecution: {d.what_is_disputed}")
        if d.key_allegations:
            lines.append("Key Disputes: " + "; ".join(d.key_allegations))
        if d.facts_relied_upon:
            lines.append("Key Facts Relied Upon: " + ", ".join(d.facts_relied_upon))
        if d.desired_outcome:
            lines.append(f"Desired Outcome: {d.desired_outcome}")

    return "\n".join(lines)


def format_issues(issues_list) -> str:
    if not issues_list:
        return "1. Taking of property 2. Without consent 3. Dishonest intention 4. Sufficiency of circumstantial proof"
    return "\n".join([f"[{iss.issue_id}]: {iss.question}" for iss in issues_list])


def compile_debate_history(arguments: List[Argument]) -> str:
    if not arguments:
        return "No prior arguments in this trial."
    lines = []
    for arg in arguments:
        spk = arg.speaker.value.upper() if isinstance(arg.speaker, Speaker) else str(arg.speaker).upper()
        stage = arg.stage_type.replace("_", " ").title()
        leg = f" [Legal Basis: {arg.legal_basis}]" if arg.legal_basis else ""
        lines.append(f"--- {stage} ({spk}){leg} [ID: {arg.id}] ---\n{arg.content}\n")
    return "\n".join(lines)


def execute_next_turn(case_id: str) -> NextTurnResponse:
    """
    Executes EXACTLY ONE sequential turn in the procedural courtroom state machine:
    1. Court Opening / Charges
    2. Prosecution Opening Statement
    3. Prosecution Witness Examination-in-Chief & Cross-Examination
    4. Defence Evidence / Witnesses
    5. Closing Arguments (Prosecution -> Defense)
    6. Judge Deliberation & Traceable Judgment
    """
    case = database.get_case_by_id(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")

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
            next_action_prompt="Trial already concluded",
            audit_event="TRIAL_ALREADY_RESOLVED",
        )

    # If first turn after start
    if not case.current_stage or case.current_stage in ("pending", "pre_trial", "filed"):
        conn = database.get_db_connection()
        with conn:
            conn.execute(
                "UPDATE cases SET status = ?, current_stage = 'court_opening', current_speaker = 'judge', updated_at = ? WHERE id = ?",
                (CaseStatus.TRIAL_IN_PROGRESS.value, datetime.datetime.utcnow().isoformat(), case.id),
            )
        conn.close()
        database.save_courtroom_event(
            case.id,
            stage="court_opening",
            event_type="COURT_OPENED",
            speaker="judge",
            content=f"Court is in session. Matter '{case.title}' ({case.docket_number}) called for trial. The charge '{case.charge_or_dispute}' is formally framed.",
        )
        case = database.get_case_by_id(case_id)

    arguments = case.arguments
    facts_indexed_str = format_facts_indexed(case.facts_list)
    evidence_str = format_evidence(case.evidence_list)
    witnesses_str = format_witnesses(case.witnesses_list)
    laws_str = format_applicable_laws(case.applicable_laws)
    statements_str = format_party_statements(case.statements)
    issues_str = format_issues(case.legal_issues)

    counsel_filing_id = getattr(case, "counsel_filing_id", "agent_02") or "agent_02"
    counsel_opposing_id = getattr(case, "counsel_opposing_id", "agent_01") or "agent_01"

    prof_filing = lawyer_roster.get_counsel_profile(counsel_filing_id)
    prof_opposing = lawyer_roster.get_counsel_profile(counsel_opposing_id)

    rag_query = f"{case.charge_or_dispute}\n{case.facts[:600]}\n" + "\n".join([getattr(iss, "question", "") for iss in case.legal_issues])
    rag_filing = rag_service.query_domain_knowledge(domain=prof_filing.domain_folder, query_text=rag_query)
    rag_opposing = rag_service.query_domain_knowledge(domain=prof_opposing.domain_folder, query_text=rag_query)

    prosecution = ProsecutionAgent(
        title=case.title,
        facts=case.facts,
        charge_or_dispute=case.charge_or_dispute,
        facts_indexed=facts_indexed_str,
        applicable_laws_str=laws_str,
        party_statements_str=statements_str,
        issues_str=issues_str,
        counsel_id=counsel_filing_id,
        rag_grounding_str=rag_filing.get("grounding_block", ""),
    )
    defense = DefenseAgent(
        title=case.title,
        facts=case.facts,
        charge_or_dispute=case.charge_or_dispute,
        facts_indexed=facts_indexed_str,
        applicable_laws_str=laws_str,
        party_statements_str=statements_str,
        issues_str=issues_str,
        counsel_id=counsel_opposing_id,
        rag_grounding_str=rag_opposing.get("grounding_block", ""),
    )
    judge = JudgeAgent(
        title=case.title,
        facts=case.facts,
        charge_or_dispute=case.charge_or_dispute,
        facts_indexed=facts_indexed_str,
        evidence_str=evidence_str,
        witnesses_str=witnesses_str,
        applicable_laws_str=laws_str,
        party_statements_str=statements_str,
        issues_str=issues_str,
    )

    current_stage = case.current_stage

    # 1. COURT OPENING -> Call Prosecution Opening
    if current_stage == "court_opening":
        evt = database.save_courtroom_event(
            case.id,
            stage="court_opening",
            event_type="PROSECUTION_CALLED",
            speaker="judge",
            content=f"The Court calls upon the Prosecution to deliver its opening statement and outline the prima facie case under {case.charge_or_dispute}.",
        )
        conn = database.get_db_connection()
        with conn:
            conn.execute(
                "UPDATE cases SET current_stage = 'prosecution_opening', current_speaker = 'prosecution', updated_at = ? WHERE id = ?",
                (datetime.datetime.utcnow().isoformat(), case.id),
            )
        conn.close()

        return NextTurnResponse(
            case_id=case.id,
            status=CaseStatus.TRIAL_IN_PROGRESS,
            current_stage="prosecution_opening",
            current_speaker="prosecution",
            current_witness_id=None,
            current_round=1,
            total_rounds=case.total_rounds,
            is_completed=False,
            courtroom_event=evt,
            next_action_prompt="Prosecution Opening Statement",
            audit_event="COURT_OPENED",
        )

    # 2. PROSECUTION OPENING STATEMENT
    elif current_stage == "prosecution_opening":
        raw_res = prosecution.generate_opening(case_charge=case.charge_or_dispute)
        arg_text = raw_res.get("argument") or f"May it please the Hon'ble Court, the Prosecution submits that the evidence and witness depositions will conclusively establish the elements of {case.charge_or_dispute}."
        leg_basis = raw_res.get("legal_basis") or case.charge_or_dispute.split("—")[0].strip()
        new_arg_obj = Argument(
            case_id=case.id,
            round_number=1,
            speaker=Speaker.PROSECUTION,
            stage_type="prosecution_opening",
            content=arg_text,
            argument_type="opening_statement",
            argument_strength="strong",
            legal_basis=leg_basis,
            party_statement_ref="Prosecution Opening Address",
            evidence_references=raw_res.get("evidence_references", ["Fact #1", "Fact #2"]),
        )
        database.save_argument_record(new_arg_obj)

        evt = database.save_courtroom_event(
            case.id,
            stage="prosecution_opening",
            event_type="OPENING_DELIVERED",
            speaker="prosecution",
            content=arg_text,
        )

        conn = database.get_db_connection()
        with conn:
            conn.execute(
                "UPDATE cases SET current_stage = 'defence_opening', current_speaker = 'defense', updated_at = ? WHERE id = ?",
                (datetime.datetime.utcnow().isoformat(), case.id),
            )
        conn.close()

        return NextTurnResponse(
            case_id=case.id,
            status=CaseStatus.TRIAL_IN_PROGRESS,
            current_stage="defence_opening",
            current_speaker="defense",
            current_witness_id=None,
            current_round=1,
            total_rounds=case.total_rounds,
            is_completed=False,
            new_argument=new_arg_obj,
            courtroom_event=evt,
            next_action_prompt="Defense Opening Statement",
            audit_event=f"PROSECUTION_OPENING_RECORDED_{prosecution.last_model_used}",
        )

    # 3. DEFENCE OPENING STATEMENT
    elif current_stage == "defence_opening":
        raw_res = defense.generate_opening(case_charge=case.charge_or_dispute)
        arg_text = raw_res.get("argument") or "With utmost respect to this Hon'ble Court, the Defense submits that the State's circumstantial claims fail the standard of proof beyond reasonable doubt under BSA §104."
        leg_basis = raw_res.get("legal_basis") or "Presumption of Innocence & BSA §104"
        new_arg_obj = Argument(
            case_id=case.id,
            round_number=1,
            speaker=Speaker.DEFENSE,
            stage_type="defence_opening",
            content=arg_text,
            argument_type="opening_statement",
            argument_strength="strong",
            legal_basis=leg_basis,
            party_statement_ref="Defense Opening Address",
            evidence_references=raw_res.get("evidence_references", ["Fact #3", "Fact #5"]),
        )
        database.save_argument_record(new_arg_obj)

        evt = database.save_courtroom_event(
            case.id,
            stage="defence_opening",
            event_type="OPENING_DELIVERED",
            speaker="defense",
            content=arg_text,
        )

        # Transition to Prosecution Evidence: determine first witness (PW-01)
        pros_witnesses = [w for w in case.witnesses_list if w.called_by == "prosecution"]
        first_w_id = pros_witnesses[0].id if pros_witnesses else None

        conn = database.get_db_connection()
        with conn:
            conn.execute(
                "UPDATE cases SET current_stage = 'prosecution_evidence', current_speaker = 'prosecution', current_witness_id = ?, updated_at = ? WHERE id = ?",
                (first_w_id, datetime.datetime.utcnow().isoformat(), case.id),
            )
        conn.close()

        if first_w_id:
            database.update_witness_status(first_w_id, "on_stand", case_id=case.id)

        return NextTurnResponse(
            case_id=case.id,
            status=CaseStatus.TRIAL_IN_PROGRESS,
            current_stage="prosecution_evidence",
            current_speaker="prosecution",
            current_witness_id=first_w_id,
            current_round=1,
            total_rounds=case.total_rounds,
            is_completed=False,
            new_argument=new_arg_obj,
            courtroom_event=evt,
            next_action_prompt=f"Prosecution calls witness {first_w_id or 'PW-01'} to the stand",
            audit_event="DEFENCE_OPENING_RECORDED",
        )

    # 4. PROSECUTION EVIDENCE (Witness Examination)
    elif current_stage == "prosecution_evidence":
        witness_id = case.current_witness_id
        witness = next((w for w in case.witnesses_list if w.id == witness_id), None)

        if not witness and case.witnesses_list:
            pros_w = [w for w in case.witnesses_list if w.called_by == "prosecution" and w.status != "discharged"]
            witness = pros_w[0] if pros_w else case.witnesses_list[0]
            witness_id = witness.id

        if not witness:
            # No witnesses, proceed directly to closing
            conn = database.get_db_connection()
            with conn:
                conn.execute(
                    "UPDATE cases SET current_stage = 'closing_prosecution', current_speaker = 'prosecution', current_witness_id = NULL, updated_at = ? WHERE id = ?",
                    (datetime.datetime.utcnow().isoformat(), case.id),
                )
            conn.close()
            return execute_next_turn(case_id)

        w_turns = witness.testimony_turns or []
        direct_turns = [t for t in w_turns if t.get("stage") == "examination_in_chief"]
        cross_turns = [t for t in w_turns if t.get("stage") == "cross_examination"]

        # Direct Examination: 3 questions
        if len(direct_turns) < 3:
            q_num = len(direct_turns) + 1
            raw_q = prosecution.generate_examination_question(
                witness_name=witness.name,
                witness_role=witness.role,
                expected_testimony=witness.expected_testimony,
                question_num=q_num,
                prior_qa_list=w_turns,
            )
            q_text = raw_q.get("question", f"Please describe what you observed during the material timeline.")

            # Witness answers strictly from their record
            w_agent = WitnessAgent(
                case_title=case.title,
                canonical_facts=case.facts,
                witness_id=witness.id,
                witness_name=witness.name,
                role=witness.role,
                connection_to_case=witness.connection_to_case,
                expected_testimony=witness.expected_testimony,
                linked_facts=[f"Fact #{idx}" for idx in witness.linked_fact_indices],
                linked_exhibits=witness.linked_evidence_ids,
            )
            raw_ans = w_agent.answer_question(
                examining_counsel="prosecution",
                examination_type="examination_in_chief",
                question=q_text,
                prior_testimony_summary="\n".join([f"Q: {t.get('question')}\nA: {t.get('answer')}" for t in w_turns]),
            )
            ans_text = raw_ans.get("answer", "I testify strictly based on the observations and facts on record.")

            turn_record = {
                "turn": len(w_turns) + 1,
                "counsel": "prosecution",
                "stage": "examination_in_chief",
                "question": q_text,
                "answer": ans_text,
            }
            database.update_witness_status(witness.id, "on_stand", turn_record=turn_record, case_id=case.id)

            evt = database.save_courtroom_event(
                case.id,
                stage="prosecution_evidence",
                event_type="EXAMINATION_QUESTION_ANSWER",
                speaker="prosecution",
                witness_id=witness.id,
                content=f"🔴 Direct Q ({q_num}/3): {q_text}\n\n👤 {witness.name} ({witness.id}): \"{ans_text}\"",
                question_turn=len(w_turns) + 1,
            )

            # Auto-introduce linked exhibits
            if q_num == 1 and witness.linked_evidence_ids:
                ex_id = witness.linked_evidence_ids[0]
                database.update_evidence_status(ex_id, "admitted", case_id=case.id)
                database.save_courtroom_event(
                    case.id,
                    stage="prosecution_evidence",
                    event_type="EVIDENCE_ADMITTED",
                    speaker="judge",
                    content=f"Exhibit {ex_id} offered by Prosecution is formally marked and admitted into evidence.",
                    evidence_id=ex_id,
                    evidence_action="admitted",
                )
            elif q_num == 2 and len(witness.linked_evidence_ids) > 1:
                ex_id = witness.linked_evidence_ids[1]
                database.update_evidence_status(ex_id, "admitted", case_id=case.id)
                database.save_courtroom_event(
                    case.id,
                    stage="prosecution_evidence",
                    event_type="EVIDENCE_ADMITTED",
                    speaker="judge",
                    content=f"Exhibit {ex_id} offered by Prosecution is formally marked and admitted into evidence.",
                    evidence_id=ex_id,
                    evidence_action="admitted",
                )

            next_spk = "prosecution" if q_num < 3 else "defense"
            next_prompt = f"Next Examination Question ({q_num + 1}/3)" if q_num < 3 else "Proceed to Cross-Examination (1/3)"

            conn = database.get_db_connection()
            with conn:
                conn.execute(
                    "UPDATE cases SET current_stage = 'prosecution_evidence', current_speaker = ?, current_witness_id = ?, updated_at = ? WHERE id = ?",
                    (next_spk, witness.id, datetime.datetime.utcnow().isoformat(), case.id),
                )
            conn.close()

            return NextTurnResponse(
                case_id=case.id,
                status=CaseStatus.TRIAL_IN_PROGRESS,
                current_stage="prosecution_evidence",
                current_speaker=next_spk,
                current_witness_id=witness.id,
                current_round=1,
                total_rounds=case.total_rounds,
                is_completed=False,
                courtroom_event=evt,
                next_action_prompt=next_prompt,
                audit_event=f"WITNESS_EXAMINED_{witness.id}_Q{q_num}",
            )

        # Cross-Examination turns: 3 questions
        elif len(cross_turns) < 3:
            cross_num = len(cross_turns) + 1
            raw_cross = defense.generate_cross_question(
                witness_name=witness.name,
                witness_role=witness.role,
                prior_testimony_summary="\n".join([f"Q: {t.get('question')}\nA: {t.get('answer')}" for t in w_turns]),
                question_num=cross_num,
            )
            cross_q = raw_cross.get("question", "You did not personally witness the physical act without ambiguity, correct?")

            w_agent = WitnessAgent(
                case_title=case.title,
                canonical_facts=case.facts,
                witness_id=witness.id,
                witness_name=witness.name,
                role=witness.role,
                connection_to_case=witness.connection_to_case,
                expected_testimony=witness.expected_testimony,
                linked_facts=[f"Fact #{idx}" for idx in witness.linked_fact_indices],
                linked_exhibits=witness.linked_evidence_ids,
            )
            raw_ans = w_agent.answer_question(
                examining_counsel="defense",
                examination_type="cross_examination",
                question=cross_q,
                prior_testimony_summary="\n".join([f"Q: {t.get('question')}\nA: {t.get('answer')}" for t in w_turns]),
            )
            ans_text = raw_ans.get("answer", "I can only speak directly to what is within my knowledge and records.")

            turn_record = {
                "turn": len(w_turns) + 1,
                "counsel": "defense",
                "stage": "cross_examination",
                "question": cross_q,
                "answer": ans_text,
            }
            database.update_witness_status(witness.id, "on_stand", turn_record=turn_record, case_id=case.id)

            evt = database.save_courtroom_event(
                case.id,
                stage="prosecution_evidence",
                event_type="CROSS_EXAMINATION_ANSWER",
                speaker="defense",
                witness_id=witness.id,
                content=f"🔵 Cross Q ({cross_num}/3): {cross_q}\n\n👤 {witness.name} ({witness.id}): \"{ans_text}\"",
                question_turn=len(w_turns) + 1,
            )

            # Check if this witness completed all 3 cross questions
            if cross_num >= 3:
                database.update_witness_status(witness.id, "discharged", case_id=case.id)
                database.save_courtroom_event(
                    case.id,
                    stage="prosecution_evidence",
                    event_type="WITNESS_DISCHARGED",
                    speaker="judge",
                    witness_id=witness.id,
                    content=f"Witness {witness.name} ({witness.id}) is discharged from the stand. Prosecution rests on this witness.",
                )

                # Check if there is another unexamined prosecution witness (e.g. PW-02)
                unexamined_pros = [w for w in case.witnesses_list if w.called_by == "prosecution" and w.id != witness.id and w.status != "discharged"]
                if unexamined_pros:
                    next_w_id = unexamined_pros[0].id
                    database.update_witness_status(next_w_id, "on_stand", case_id=case.id)
                    next_stage = "prosecution_evidence"
                    next_speaker = "prosecution"
                    prompt_msg = f"Prosecution calls {next_w_id} ({unexamined_pros[0].name})"
                else:
                    # Check for defense witness
                    def_witnesses = [w for w in case.witnesses_list if w.called_by == "defense" and w.status != "discharged"]
                    if def_witnesses:
                        next_stage = "defence_evidence"
                        next_speaker = "defense"
                        next_w_id = def_witnesses[0].id
                        database.update_witness_status(next_w_id, "on_stand", case_id=case.id)
                        prompt_msg = f"Defence calls witness {next_w_id} ({def_witnesses[0].name})"
                    else:
                        next_stage = "closing_prosecution"
                        next_speaker = "prosecution"
                        next_w_id = None
                        prompt_msg = "Prosecution Closing Arguments"

                conn = database.get_db_connection()
                with conn:
                    conn.execute(
                        "UPDATE cases SET current_stage = ?, current_speaker = ?, current_witness_id = ?, updated_at = ? WHERE id = ?",
                        (next_stage, next_speaker, next_w_id, datetime.datetime.utcnow().isoformat(), case.id),
                    )
                conn.close()

                return NextTurnResponse(
                    case_id=case.id,
                    status=CaseStatus.TRIAL_IN_PROGRESS,
                    current_stage=next_stage,
                    current_speaker=next_speaker,
                    current_witness_id=next_w_id,
                    current_round=1,
                    total_rounds=case.total_rounds,
                    is_completed=False,
                    courtroom_event=evt,
                    next_action_prompt=prompt_msg,
                    audit_event=f"WITNESS_DISCHARGED_{witness.id}",
                )

            conn = database.get_db_connection()
            with conn:
                conn.execute(
                    "UPDATE cases SET current_stage = 'prosecution_evidence', current_speaker = 'defense', current_witness_id = ?, updated_at = ? WHERE id = ?",
                    (witness.id, datetime.datetime.utcnow().isoformat(), case.id),
                )
            conn.close()

            return NextTurnResponse(
                case_id=case.id,
                status=CaseStatus.TRIAL_IN_PROGRESS,
                current_stage="prosecution_evidence",
                current_speaker="defense",
                current_witness_id=witness.id,
                current_round=1,
                total_rounds=case.total_rounds,
                is_completed=False,
                courtroom_event=evt,
                next_action_prompt=f"Next Cross-Examination Question ({cross_num + 1}/3)",
                audit_event=f"WITNESS_CROSS_EXAMINED_{witness.id}_Q{cross_num}",
            )

        else:
            # Witness already fully examined
            database.update_witness_status(witness.id, "discharged", case_id=case.id)
            def_witnesses = [w for w in case.witnesses_list if w.called_by == "defense" and w.status != "discharged"]
            if def_witnesses:
                next_stage = "defence_evidence"
                next_speaker = "defense"
                next_w_id = def_witnesses[0].id
                database.update_witness_status(next_w_id, "on_stand", case_id=case.id)
            else:
                next_stage = "closing_prosecution"
                next_speaker = "prosecution"
                next_w_id = None

            conn = database.get_db_connection()
            with conn:
                conn.execute(
                    "UPDATE cases SET current_stage = ?, current_speaker = ?, current_witness_id = ?, updated_at = ? WHERE id = ?",
                    (next_stage, next_speaker, next_w_id, datetime.datetime.utcnow().isoformat(), case.id),
                )
            conn.close()
            return execute_next_turn(case_id)

    # 5. DEFENCE EVIDENCE (Defence Witness Examination & Cross-Examination)
    elif current_stage == "defence_evidence":
        witness_id = case.current_witness_id
        witness = next((w for w in case.witnesses_list if w.id == witness_id), None)
        if not witness:
            conn = database.get_db_connection()
            with conn:
                conn.execute(
                    "UPDATE cases SET current_stage = 'closing_prosecution', current_speaker = 'prosecution', current_witness_id = NULL, updated_at = ? WHERE id = ?",
                    (datetime.datetime.utcnow().isoformat(), case.id),
                )
            conn.close()
            return execute_next_turn(case_id)

        w_turns = witness.testimony_turns or []
        direct_turns = [t for t in w_turns if t.get("stage") == "examination_in_chief"]
        cross_turns = [t for t in w_turns if t.get("stage") == "cross_examination"]

        # Defence Direct Examination: 3 questions
        if len(direct_turns) < 3:
            q_num = len(direct_turns) + 1
            raw_q = defense.generate_examination_question(
                witness_name=witness.name,
                witness_role=witness.role,
                expected_testimony=witness.expected_testimony,
                question_num=q_num,
                prior_qa_list=w_turns,
            )
            q_text = raw_q.get("question", "Please clarify the defense position and critical timeline facts.")

            w_agent = WitnessAgent(
                case_title=case.title,
                canonical_facts=case.facts,
                witness_id=witness.id,
                witness_name=witness.name,
                role=witness.role,
                connection_to_case=witness.connection_to_case,
                expected_testimony=witness.expected_testimony,
                linked_facts=[f"Fact #{idx}" for idx in witness.linked_fact_indices],
                linked_exhibits=witness.linked_evidence_ids,
            )
            raw_ans = w_agent.answer_question(
                examining_counsel="defense",
                examination_type="examination_in_chief",
                question=q_text,
                prior_testimony_summary="\n".join([f"Q: {t.get('question')}\nA: {t.get('answer')}" for t in w_turns]),
            )
            ans_text = raw_ans.get("answer", "I confirm the facts and circumstances as stated.")

            turn_record = {
                "turn": len(w_turns) + 1,
                "counsel": "defense",
                "stage": "examination_in_chief",
                "question": q_text,
                "answer": ans_text,
            }
            database.update_witness_status(witness.id, "on_stand", turn_record=turn_record, case_id=case.id)

            evt = database.save_courtroom_event(
                case.id,
                stage="defence_evidence",
                event_type="DEFENCE_WITNESS_EXAMINED",
                speaker="defense",
                witness_id=witness.id,
                content=f"🔵 Direct Q ({q_num}/3): {q_text}\n\n👤 {witness.name} ({witness.id}): \"{ans_text}\"",
                question_turn=len(w_turns) + 1,
            )

            # Auto-introduce defense exhibit if available
            if q_num == 1 and witness.linked_evidence_ids:
                ex_id = witness.linked_evidence_ids[0]
                database.update_evidence_status(ex_id, "admitted", case_id=case.id)
                database.save_courtroom_event(
                    case.id,
                    stage="defence_evidence",
                    event_type="EVIDENCE_ADMITTED",
                    speaker="judge",
                    content=f"Exhibit {ex_id} offered by Defense is formally marked and admitted into evidence.",
                    evidence_id=ex_id,
                    evidence_action="admitted",
                )

            next_spk = "defense" if q_num < 3 else "prosecution"
            next_prompt = f"Next Defence Direct ({q_num + 1}/3)" if q_num < 3 else "Prosecution Cross-Examination (1/3)"

            conn = database.get_db_connection()
            with conn:
                conn.execute(
                    "UPDATE cases SET current_stage = 'defence_evidence', current_speaker = ?, current_witness_id = ?, updated_at = ? WHERE id = ?",
                    (next_spk, witness.id, datetime.datetime.utcnow().isoformat(), case.id),
                )
            conn.close()

            return NextTurnResponse(
                case_id=case.id,
                status=CaseStatus.TRIAL_IN_PROGRESS,
                current_stage="defence_evidence",
                current_speaker=next_spk,
                current_witness_id=witness.id,
                current_round=case.total_rounds,
                total_rounds=case.total_rounds,
                is_completed=False,
                courtroom_event=evt,
                next_action_prompt=next_prompt,
                audit_event=f"DEFENCE_WITNESS_EXAMINED_Q{q_num}",
            )

        # Prosecution Cross-Examination of Defense Witness: 3 questions
        elif len(cross_turns) < 3:
            cross_num = len(cross_turns) + 1
            raw_cross = prosecution.generate_cross_question(
                witness_name=witness.name,
                witness_role=witness.role,
                prior_testimony_summary="\n".join([f"Q: {t.get('question')}\nA: {t.get('answer')}" for t in w_turns]),
                question_num=cross_num,
            )
            cross_q = raw_cross.get("question", "Isn't it true you did not independently verify the documentation yourself?")

            w_agent = WitnessAgent(
                case_title=case.title,
                canonical_facts=case.facts,
                witness_id=witness.id,
                witness_name=witness.name,
                role=witness.role,
                connection_to_case=witness.connection_to_case,
                expected_testimony=witness.expected_testimony,
                linked_facts=[f"Fact #{idx}" for idx in witness.linked_fact_indices],
                linked_exhibits=witness.linked_evidence_ids,
            )
            raw_ans = w_agent.answer_question(
                examining_counsel="prosecution",
                examination_type="cross_examination",
                question=cross_q,
                prior_testimony_summary="\n".join([f"Q: {t.get('question')}\nA: {t.get('answer')}" for t in w_turns]),
            )
            ans_text = raw_ans.get("answer", "I acted strictly within the scope of my routine responsibilities.")

            turn_record = {
                "turn": len(w_turns) + 1,
                "counsel": "prosecution",
                "stage": "cross_examination",
                "question": cross_q,
                "answer": ans_text,
            }
            database.update_witness_status(witness.id, "on_stand", turn_record=turn_record, case_id=case.id)

            evt = database.save_courtroom_event(
                case.id,
                stage="defence_evidence",
                event_type="DEFENCE_WITNESS_CROSS_EXAMINED",
                speaker="prosecution",
                witness_id=witness.id,
                content=f"🔴 Cross Q ({cross_num}/3): {cross_q}\n\n👤 {witness.name} ({witness.id}): \"{ans_text}\"",
                question_turn=len(w_turns) + 1,
            )

            # If cross-examination reached 3 questions, discharge witness
            if cross_num >= 3:
                database.update_witness_status(witness.id, "discharged", case_id=case.id)
                database.save_courtroom_event(
                    case.id,
                    stage="defence_evidence",
                    event_type="WITNESS_DISCHARGED",
                    speaker="judge",
                    witness_id=witness.id,
                    content=f"Defense Witness {witness.name} ({witness.id}) is discharged from the stand. Evidentiary stage concluded.",
                )

                # Move to Closing Arguments
                conn = database.get_db_connection()
                with conn:
                    conn.execute(
                        "UPDATE cases SET current_stage = 'closing_prosecution', current_speaker = 'prosecution', current_witness_id = NULL, updated_at = ? WHERE id = ?",
                        (datetime.datetime.utcnow().isoformat(), case.id),
                    )
                conn.close()

                return NextTurnResponse(
                    case_id=case.id,
                    status=CaseStatus.TRIAL_IN_PROGRESS,
                    current_stage="closing_prosecution",
                    current_speaker="prosecution",
                    current_witness_id=None,
                    current_round=case.total_rounds,
                    total_rounds=case.total_rounds,
                    is_completed=False,
                    courtroom_event=evt,
                    next_action_prompt="Prosecution Closing Arguments",
                    audit_event="DEFENCE_EVIDENCE_CONCLUDED",
                )

            conn = database.get_db_connection()
            with conn:
                conn.execute(
                    "UPDATE cases SET current_stage = 'defence_evidence', current_speaker = 'prosecution', current_witness_id = ?, updated_at = ? WHERE id = ?",
                    (witness.id, datetime.datetime.utcnow().isoformat(), case.id),
                )
            conn.close()

            return NextTurnResponse(
                case_id=case.id,
                status=CaseStatus.TRIAL_IN_PROGRESS,
                current_stage="defence_evidence",
                current_speaker="prosecution",
                current_witness_id=witness.id,
                current_round=case.total_rounds,
                total_rounds=case.total_rounds,
                is_completed=False,
                courtroom_event=evt,
                next_action_prompt=f"Next Prosecution Cross ({cross_num + 1}/3)",
                audit_event=f"DEFENCE_WITNESS_CROSS_EXAMINED_Q{cross_num}",
            )

        else:
            # Defence witness already examined -> move to closing
            database.update_witness_status(witness.id, "discharged", case_id=case.id)
            conn = database.get_db_connection()
            with conn:
                conn.execute(
                    "UPDATE cases SET current_stage = 'closing_prosecution', current_speaker = 'prosecution', current_witness_id = NULL, updated_at = ? WHERE id = ?",
                    (datetime.datetime.utcnow().isoformat(), case.id),
                )
            conn.close()
            return execute_next_turn(case_id)

    # 5. PROSECUTION CLOSING STATEMENT
    elif current_stage == "closing_prosecution":
        debate_summary = compile_debate_history(arguments)
        raw_res = prosecution.generate_closing(full_trial_summary=debate_summary, case_charge=case.charge_or_dispute)
        arg_text = raw_res.get("argument") or f"May it please the Court, the State respectfully submits that the unbroken chain of circumstantial and documentary proof satisfies {case.charge_or_dispute} beyond reasonable doubt."
        leg_basis = raw_res.get("legal_basis") or f"{case.charge_or_dispute.split('—')[0].strip()} & BSA §104"

        new_arg_obj = Argument(
            case_id=case.id,
            round_number=case.total_rounds,
            speaker=Speaker.PROSECUTION,
            stage_type="closing_prosecution",
            content=arg_text,
            argument_type="closing_argument",
            argument_strength="strong",
            legal_basis=leg_basis,
            party_statement_ref="State Closing Summation",
            evidence_references=raw_res.get("evidence_references", ["Fact #1", "Fact #2", "P-EX-01"]),
        )
        database.save_argument_record(new_arg_obj)

        evt = database.save_courtroom_event(
            case.id,
            stage="closing_prosecution",
            event_type="PROSECUTION_CLOSING_DELIVERED",
            speaker="prosecution",
            content=arg_text,
        )

        conn = database.get_db_connection()
        with conn:
            conn.execute(
                "UPDATE cases SET current_stage = 'closing_defense', current_speaker = 'defense', updated_at = ? WHERE id = ?",
                (datetime.datetime.utcnow().isoformat(), case.id),
            )
        conn.close()

        return NextTurnResponse(
            case_id=case.id,
            status=CaseStatus.TRIAL_IN_PROGRESS,
            current_stage="closing_defense",
            current_speaker="defense",
            current_witness_id=None,
            current_round=case.total_rounds,
            total_rounds=case.total_rounds,
            is_completed=False,
            new_argument=new_arg_obj,
            courtroom_event=evt,
            next_action_prompt="Defense Closing Arguments",
            audit_event=f"PROSECUTION_CLOSING_RECORDED_{prosecution.last_model_used}",
        )

    # 6. DEFENCE CLOSING STATEMENT
    elif current_stage == "closing_defense":
        debate_summary = compile_debate_history(arguments)
        latest_pros = next((a.content for a in reversed(arguments) if a.speaker == Speaker.PROSECUTION), "")
        raw_res = defense.generate_closing(full_trial_summary=debate_summary, latest_prosecution_arg=latest_pros, case_charge=case.charge_or_dispute)
        arg_text = raw_res.get("argument") or "The defense respectfully submits that in the absence of conclusive forensic links and direct proof, reasonable doubt remains paramount under BSA §104."
        leg_basis = raw_res.get("legal_basis") or "Presumption of Innocence & BSA §104"

        new_arg_obj = Argument(
            case_id=case.id,
            round_number=case.total_rounds,
            speaker=Speaker.DEFENSE,
            stage_type="closing_defense",
            content=arg_text,
            argument_type="closing_argument",
            argument_strength="strong",
            legal_basis=leg_basis,
            party_statement_ref="Defense Closing Summation",
            evidence_references=raw_res.get("evidence_references", ["Fact #5", "Fact #7", "D-EX-01"]),
        )
        database.save_argument_record(new_arg_obj)

        evt = database.save_courtroom_event(
            case.id,
            stage="closing_defense",
            event_type="DEFENSE_CLOSING_DELIVERED",
            speaker="defense",
            content=arg_text,
        )

        conn = database.get_db_connection()
        with conn:
            conn.execute(
                "UPDATE cases SET status = ?, current_stage = 'judge_deliberation', current_speaker = 'judge', updated_at = ? WHERE id = ?",
                (CaseStatus.DELIBERATION.value, datetime.datetime.utcnow().isoformat(), case.id),
            )
        conn.close()

        return NextTurnResponse(
            case_id=case.id,
            status=CaseStatus.DELIBERATION,
            current_stage="judge_deliberation",
            current_speaker="judge",
            current_witness_id=None,
            current_round=case.total_rounds,
            total_rounds=case.total_rounds,
            is_completed=False,
            new_argument=new_arg_obj,
            courtroom_event=evt,
            next_action_prompt="Proceed to AI Judge Deliberation & Verdict",
            audit_event="DEFENSE_CLOSING_RECORDED",
        )

    # 7. JUDGE DELIBERATION & VERDICT
    elif current_stage == "judge_deliberation" or case.current_speaker == "judge":
        updated_case = database.get_case_by_id(case_id)
        full_record = compile_debate_history(updated_case.arguments)

        raw_verdict = judge.deliberate_and_rule(
            full_record,
            legal_issues=[iss.model_dump() for iss in updated_case.legal_issues],
            canonical_facts_str=facts_indexed_str,
            evidence_str=evidence_str,
            witnesses_str=witnesses_str,
            applicable_laws_str=laws_str,
        )

        verdict_obj = Verdict(
            case_id=case.id,
            winner=raw_verdict.get("winner", "defense_prevailed"),
            decision=raw_verdict.get("decision", "NOT GUILTY — The charge is not proven beyond reasonable doubt."),
            verdict_category=raw_verdict.get("verdict_category", "not_guilty"),
            confidence=raw_verdict.get("confidence", 0.85),
            decision_basis=raw_verdict.get("decision_basis", ""),
            reasoning_summary=raw_verdict.get("reasoning_summary", ""),
            reasoning=raw_verdict.get("reasoning_summary", ""),
            issue_findings=raw_verdict.get("issue_findings", []),
            law_assessments=raw_verdict.get("law_assessments", []),
            affirmative_defense_analysis=raw_verdict.get("affirmative_defense_analysis", {}),
            prosecution_strengths=raw_verdict.get("prosecution_strengths", []),
            defense_strengths=raw_verdict.get("defense_strengths", []),
            key_factors=raw_verdict.get("key_factors", []),
            evidence_gaps=raw_verdict.get("evidence_gaps", []),
        )
        database.save_verdict_record(verdict_obj)

        evt = database.save_courtroom_event(
            case.id,
            stage="resolved",
            event_type="JUDGMENT_DELIVERED",
            speaker="judge",
            content=f"COURT FINDING & JUDGMENT: {verdict_obj.decision}\n\nBasis: {verdict_obj.decision_basis}",
        )

        return NextTurnResponse(
            case_id=case.id,
            status=CaseStatus.RESOLVED,
            current_stage="resolved",
            current_speaker=None,
            current_witness_id=None,
            current_round=case.total_rounds,
            total_rounds=case.total_rounds,
            is_completed=True,
            verdict=verdict_obj,
            courtroom_event=evt,
            next_action_prompt="Trial Resolved — View Complete Verdict & Final Case Report",
            audit_event="VERDICT_DELIVERED",
        )

    else:
        # Fallback
        conn = database.get_db_connection()
        with conn:
            conn.execute(
                "UPDATE cases SET current_stage = 'court_opening', current_speaker = 'judge', updated_at = ? WHERE id = ?",
                (datetime.datetime.utcnow().isoformat(), case.id),
            )
        conn.close()
        return execute_next_turn(case_id)


def handle_objection(case_id: str, raised_by: str, ground: str, question_text: str) -> Dict[str, Any]:
    case = database.get_case_by_id(case_id)
    if not case:
        raise ValueError("Case not found")

    judge = JudgeAgent(title=case.title, facts=case.facts, charge_or_dispute=case.charge_or_dispute)
    res = judge.rule_on_objection(counsel_objecting=raised_by, ground=ground, question_text=question_text)

    ruling = res.get("ruling", "overruled")
    instruction = res.get("judicial_instruction", "The witness may answer the question.")

    evt = database.save_courtroom_event(
        case.id,
        stage=case.current_stage,
        event_type="OBJECTION_RULED",
        speaker="judge",
        content=f"⚖ OBJECTION by {raised_by.upper()} on ground '{ground}': {ruling.upper()}.\n\nCourt: \"{instruction}\"",
        objection={
            "raised_by": raised_by,
            "ground": ground,
            "ruling": ruling,
            "instruction": instruction,
        },
    )
    return {"ruling": ruling, "instruction": instruction, "event": evt.model_dump()}


def handle_introduce_evidence(case_id: str, evidence_id: str) -> Dict[str, Any]:
    case = database.get_case_by_id(case_id)
    if not case:
        raise ValueError("Case not found")

    evidence = next((e for e in case.evidence_list if e.id == evidence_id), None)
    if not evidence:
        raise ValueError(f"Evidence {evidence_id} not found")

    judge = JudgeAgent(title=case.title, facts=case.facts, charge_or_dispute=case.charge_or_dispute)
    res = judge.rule_on_evidence_admission(
        exhibit_id=evidence.id,
        title=evidence.title,
        submitted_by=evidence.submitted_by,
        description=evidence.description,
        has_hash=bool(evidence.file_hash and evidence.file_hash != "NOT PROVIDED"),
    )

    status = res.get("ruling", "admitted")
    statement = res.get("judicial_statement", f"Exhibit {evidence.id} is marked and admitted into evidence.")
    database.update_evidence_status(evidence.id, status)

    evt = database.save_courtroom_event(
        case.id,
        stage=case.current_stage,
        event_type="EVIDENCE_ADMITTED",
        speaker="judge",
        content=f"📎 {evidence.id} ({evidence.title}): {status.upper()}.\n\nCourt: \"{statement}\"",
        evidence_id=evidence.id,
        evidence_action=status,
    )
    return {"status": status, "statement": statement, "event": evt.model_dump()}


def execute_full_case_sync(case_id: str) -> CaseDetail:
    max_steps = 25
    steps = 0
    while steps < max_steps:
        resp = execute_next_turn(case_id)
        if resp.is_completed:
            break
        steps += 1
        time.sleep(0.05)
    return database.get_case_by_id(case_id)
