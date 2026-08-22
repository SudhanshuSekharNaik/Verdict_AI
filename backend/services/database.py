import datetime
import json
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

from models.schemas import (
    ApplicableLaw,
    Argument,
    AuditLog,
    CaseDetail,
    CaseFact,
    CaseStatements,
    CaseStatus,
    CourtroomEvent,
    EvidenceItem,
    IssueFinding,
    LawAssessment,
    LegalIssue,
    PartyStatement,
    Speaker,
    TranscriptEntry,
    Verdict,
    WitnessItem,
)
from services import law_service

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "courtroom.db")
DEMO_CASE_ID = "demo_state_v_rohan_verma"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                docket_number TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                fact_pattern TEXT NOT NULL,
                charge_or_dispute TEXT NOT NULL,
                case_category TEXT NOT NULL DEFAULT 'criminal',
                counsel_filing_id TEXT NOT NULL DEFAULT 'agent_02',
                counsel_opposing_id TEXT NOT NULL DEFAULT 'agent_01',
                simulation_type TEXT NOT NULL DEFAULT 'standard',
                jurisdiction TEXT NOT NULL DEFAULT 'Sessions Court, Bhubaneswar',
                total_rounds INTEGER NOT NULL DEFAULT 3,
                case_type TEXT NOT NULL DEFAULT 'user',
                status TEXT NOT NULL DEFAULT 'filed',
                current_stage TEXT NOT NULL DEFAULT 'case_filed',
                current_speaker TEXT DEFAULT 'prosecution',
                current_witness_id TEXT,
                current_round INTEGER NOT NULL DEFAULT 1,
                statements_locked INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS case_facts (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                fact_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS case_evidence (
                id TEXT NOT NULL,
                case_id TEXT NOT NULL,
                submitted_by TEXT NOT NULL DEFAULT 'prosecution',
                title TEXT NOT NULL,
                evidence_type TEXT NOT NULL DEFAULT 'document',
                description TEXT NOT NULL,
                source TEXT DEFAULT 'Case Record',
                date TEXT DEFAULT 'August 2026',
                supports_facts TEXT DEFAULT '[]',
                challenges_issues TEXT DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'submitted',
                file_hash TEXT DEFAULT 'NOT PROVIDED',
                chain_of_custody TEXT DEFAULT 'NOT PROVIDED',
                device_source TEXT DEFAULT 'NOT PROVIDED',
                created_at TEXT NOT NULL,
                PRIMARY KEY (case_id, id),
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS case_witnesses (
                id TEXT NOT NULL,
                case_id TEXT NOT NULL,
                called_by TEXT NOT NULL DEFAULT 'prosecution',
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'eyewitness',
                connection_to_case TEXT NOT NULL,
                expected_testimony TEXT NOT NULL,
                linked_evidence_ids TEXT DEFAULT '[]',
                linked_fact_indices TEXT DEFAULT '[]',
                is_expert INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'not_called',
                testimony_turns TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                PRIMARY KEY (case_id, id),
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )

        # Migration check for composite primary key on case_evidence and case_witnesses
        try:
            wit_info = conn.execute("PRAGMA table_info(case_witnesses)").fetchall()
            pk_cols = [c["name"] for c in wit_info if c["pk"] > 0]
            if len(pk_cols) < 2:
                conn.execute("ALTER TABLE case_witnesses RENAME TO old_case_witnesses")
                conn.execute("""
                    CREATE TABLE case_witnesses (
                        id TEXT NOT NULL,
                        case_id TEXT NOT NULL,
                        called_by TEXT NOT NULL DEFAULT 'prosecution',
                        name TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'eyewitness',
                        connection_to_case TEXT NOT NULL,
                        expected_testimony TEXT NOT NULL,
                        linked_evidence_ids TEXT DEFAULT '[]',
                        linked_fact_indices TEXT DEFAULT '[]',
                        is_expert INTEGER DEFAULT 0,
                        status TEXT NOT NULL DEFAULT 'not_called',
                        testimony_turns TEXT DEFAULT '[]',
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (case_id, id),
                        FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
                    )
                """)
                conn.execute("INSERT OR IGNORE INTO case_witnesses SELECT * FROM old_case_witnesses")
                conn.execute("DROP TABLE old_case_witnesses")

                conn.execute("ALTER TABLE case_evidence RENAME TO old_case_evidence")
                conn.execute("""
                    CREATE TABLE case_evidence (
                        id TEXT NOT NULL,
                        case_id TEXT NOT NULL,
                        submitted_by TEXT NOT NULL DEFAULT 'prosecution',
                        title TEXT NOT NULL,
                        evidence_type TEXT NOT NULL DEFAULT 'document',
                        description TEXT NOT NULL,
                        source TEXT DEFAULT 'Case Record',
                        date TEXT DEFAULT 'August 2026',
                        supports_facts TEXT DEFAULT '[]',
                        challenges_issues TEXT DEFAULT '[]',
                        status TEXT NOT NULL DEFAULT 'submitted',
                        file_hash TEXT DEFAULT 'NOT PROVIDED',
                        chain_of_custody TEXT DEFAULT 'NOT PROVIDED',
                        device_source TEXT DEFAULT 'NOT PROVIDED',
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (case_id, id),
                        FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
                    )
                """)
                conn.execute("INSERT OR IGNORE INTO case_evidence SELECT * FROM old_case_evidence")
                conn.execute("DROP TABLE old_case_evidence")
        except Exception:
            pass
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS courtroom_events (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                event_type TEXT NOT NULL,
                speaker TEXT,
                witness_id TEXT,
                content TEXT NOT NULL,
                question_turn INTEGER,
                objection TEXT,
                evidence_id TEXT,
                evidence_action TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS party_statements (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                speaker TEXT NOT NULL,
                incident_account TEXT NOT NULL,
                key_allegations TEXT DEFAULT '[]',
                what_is_disputed TEXT DEFAULT '',
                theory_of_case TEXT DEFAULT '',
                desired_outcome TEXT DEFAULT '',
                facts_relied_upon TEXT DEFAULT '[]',
                evidence_relied_upon TEXT DEFAULT '[]',
                witnesses_relied_upon TEXT DEFAULT '[]',
                position_details TEXT DEFAULT '{}',
                updated_at TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS case_issues (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                issue_id TEXT NOT NULL,
                question TEXT NOT NULL,
                prosecution_position TEXT NOT NULL,
                defense_position TEXT NOT NULL,
                judge_finding TEXT DEFAULT 'Pending deliberation',
                finding_rationale TEXT DEFAULT '',
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS arguments (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                speaker TEXT NOT NULL,
                stage_type TEXT NOT NULL,
                content TEXT NOT NULL,
                argument_type TEXT,
                argument_strength TEXT,
                legal_basis TEXT,
                party_statement_ref TEXT,
                evidence_references TEXT DEFAULT '[]',
                responds_to_argument_id TEXT,
                is_contradiction_flagged INTEGER DEFAULT 0,
                contradiction_note TEXT,
                is_unsupported_flagged INTEGER DEFAULT 0,
                unsupported_note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS verdicts (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL UNIQUE,
                winner TEXT DEFAULT 'defense_prevailed',
                decision TEXT NOT NULL,
                verdict_category TEXT DEFAULT 'not_guilty',
                confidence TEXT DEFAULT '0.85',
                decision_basis TEXT,
                reasoning_summary TEXT,
                issue_findings TEXT DEFAULT '[]',
                law_assessments TEXT DEFAULT '[]',
                prosecution_strengths TEXT DEFAULT '[]',
                defense_strengths TEXT DEFAULT '[]',
                key_factors TEXT DEFAULT '[]',
                evidence_gaps TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )

        # Migrations for existing schemas
        try:
            conn.execute("ALTER TABLE cases ADD COLUMN case_category TEXT NOT NULL DEFAULT 'criminal'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE cases ADD COLUMN simulation_type TEXT NOT NULL DEFAULT 'standard'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE cases ADD COLUMN jurisdiction TEXT NOT NULL DEFAULT 'Sessions Court, Bhubaneswar'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE cases ADD COLUMN current_witness_id TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE party_statements ADD COLUMN evidence_relied_upon TEXT DEFAULT '[]'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE party_statements ADD COLUMN witnesses_relied_upon TEXT DEFAULT '[]'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE verdicts ADD COLUMN affirmative_defense_analysis TEXT DEFAULT '{}'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE cases ADD COLUMN counsel_filing_id TEXT NOT NULL DEFAULT 'agent_02'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE cases ADD COLUMN counsel_opposing_id TEXT NOT NULL DEFAULT 'agent_01'")
        except Exception:
            pass

    conn.close()


def parse_facts_into_sentences(fact_pattern: str) -> List[str]:
    raw_parts = re.split(r"(?<=[.!?])\s+|\n+", fact_pattern.strip())
    clean_parts = [p.strip() for p in raw_parts if len(p.strip()) > 8]
    if not clean_parts:
        clean_parts = [fact_pattern.strip()]
    return clean_parts


def create_case_record(
    title: str,
    facts: str,
    charge_or_dispute: str,
    case_category: str = "criminal",
    counsel_filing_id: str = "agent_02",
    counsel_opposing_id: str = "agent_01",
    simulation_type: str = "standard",
    jurisdiction: str = "Sessions Court, Bhubaneswar",
    total_rounds: int = 3,
    case_type: str = "user",
    custom_id: Optional[str] = None,
    legal_issues: Optional[List[Dict[str, Any]]] = None,
) -> CaseDetail:
    init_db()
    case_id = custom_id or str(uuid.uuid4())[:8]
    docket_num = f"DOCKET NO. {case_id.upper()}"
    now = datetime.datetime.utcnow().isoformat()

    conn = get_db_connection()
    with conn:
        existing = conn.execute("SELECT id FROM cases WHERE id = ?", (case_id,)).fetchone()
        if existing:
            conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))

        conn.execute(
            """
            INSERT INTO cases (
                id, docket_number, title, fact_pattern, charge_or_dispute,
                case_category, counsel_filing_id, counsel_opposing_id,
                simulation_type, jurisdiction, total_rounds,
                case_type, status, current_stage, current_speaker, current_round,
                statements_locked, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?)
        """,
            (
                case_id,
                docket_num,
                title,
                facts,
                charge_or_dispute,
                case_category,
                counsel_filing_id or "agent_02",
                counsel_opposing_id or "agent_01",
                simulation_type,
                jurisdiction,
                total_rounds,
                case_type,
                CaseStatus.FILED.value,
                "case_filed",
                "prosecution",
                now,
                now,
            ),
        )

        # Parse & store individual facts
        facts_list = parse_facts_into_sentences(facts)
        for idx, fact_text in enumerate(facts_list, start=1):
            fact_id = f"f_{case_id}_{idx}"
            conn.execute(
                """
                INSERT INTO case_facts (id, case_id, fact_index, content)
                VALUES (?, ?, ?, ?)
            """,
                (fact_id, case_id, idx, fact_text),
            )

        # Auto-initialize initial legal issues or use custom provided issues
        initial_issues = legal_issues or law_service.generate_case_issues(facts, charge_or_dispute)
        for iss in initial_issues:
            iss_id = iss.get("issue_id") or f"ISSUE_{idx}"
            conn.execute(
                """
                INSERT INTO case_issues (id, case_id, issue_id, question, prosecution_position, defense_position, judge_finding, finding_rationale)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    f"iss_{case_id}_{iss_id}",
                    case_id,
                    iss_id,
                    iss.get("question", ""),
                    iss.get("prosecution_position", "Supports"),
                    iss.get("defense_position", "Disputes"),
                    "Pending deliberation",
                    "",
                ),
            )

        log_id = f"log_{str(uuid.uuid4())[:8]}"
        conn.execute(
            """
            INSERT INTO audit_logs (id, case_id, event_type, description, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                log_id,
                case_id,
                "CASE_FILED",
                f"Matter filed under docket {docket_num} with {len(facts_list)} canonical facts",
                now,
            ),
        )

    conn.close()
    return get_case_by_id(case_id)


# ---------- EVIDENCE CRUD ----------
def add_case_evidence(case_id: str, evidence_data: Dict[str, Any]) -> EvidenceItem:
    init_db()
    ev_id = evidence_data.get("id") or f"EX-{str(uuid.uuid4())[:6].upper()}"
    now = datetime.datetime.utcnow().isoformat()

    conn = get_db_connection()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO case_evidence (
                id, case_id, submitted_by, title, evidence_type, description,
                source, date, supports_facts, challenges_issues, status,
                file_hash, chain_of_custody, device_source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                ev_id,
                case_id,
                evidence_data.get("submitted_by", "prosecution"),
                evidence_data.get("title", "Evidence Exhibit"),
                evidence_data.get("evidence_type", "document"),
                evidence_data.get("description", ""),
                evidence_data.get("source", "Case Record"),
                evidence_data.get("date", "August 2026"),
                json.dumps(evidence_data.get("supports_facts", [])),
                json.dumps(evidence_data.get("challenges_issues", [])),
                evidence_data.get("status", "submitted"),
                evidence_data.get("file_hash", "NOT PROVIDED"),
                evidence_data.get("chain_of_custody", "NOT PROVIDED"),
                evidence_data.get("device_source", "NOT PROVIDED"),
                now,
            ),
        )
    conn.close()
    return get_case_evidence_item(ev_id, case_id)


def get_case_evidence_item(ev_id: str, case_id: Optional[str] = None) -> Optional[EvidenceItem]:
    conn = get_db_connection()
    if case_id:
        row = conn.execute("SELECT * FROM case_evidence WHERE id = ? AND case_id = ?", (ev_id, case_id)).fetchone()
    else:
        row = conn.execute("SELECT * FROM case_evidence WHERE id = ?", (ev_id,)).fetchone()
    conn.close()
    if not row:
        return None
    r_keys = row.keys()
    return EvidenceItem(
        id=row["id"],
        case_id=row["case_id"],
        submitted_by=row["submitted_by"],
        title=row["title"],
        evidence_type=row["evidence_type"],
        description=row["description"],
        source=row["source"],
        date=row["date"],
        supports_facts=json.loads(row["supports_facts"]) if "supports_facts" in r_keys and row["supports_facts"] else [],
        challenges_issues=json.loads(row["challenges_issues"]) if "challenges_issues" in r_keys and row["challenges_issues"] else [],
        status=row["status"],
        file_hash=row["file_hash"] if "file_hash" in r_keys else "NOT PROVIDED",
        chain_of_custody=row["chain_of_custody"] if "chain_of_custody" in r_keys else "NOT PROVIDED",
        device_source=row["device_source"] if "device_source" in r_keys else "NOT PROVIDED",
        created_at=row["created_at"],
    )


def get_case_evidence(case_id: str) -> List[EvidenceItem]:
    init_db()
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM case_evidence WHERE case_id = ? ORDER BY id ASC", (case_id,)).fetchall()
    conn.close()
    res = []
    for r in rows:
        r_keys = r.keys()
        res.append(
            EvidenceItem(
                id=r["id"],
                case_id=r["case_id"],
                submitted_by=r["submitted_by"],
                title=r["title"],
                evidence_type=r["evidence_type"],
                description=r["description"],
                source=r["source"],
                date=r["date"],
                supports_facts=json.loads(r["supports_facts"]) if "supports_facts" in r_keys and r["supports_facts"] else [],
                challenges_issues=json.loads(r["challenges_issues"]) if "challenges_issues" in r_keys and r["challenges_issues"] else [],
                status=r["status"],
                file_hash=r["file_hash"] if "file_hash" in r_keys else "NOT PROVIDED",
                chain_of_custody=r["chain_of_custody"] if "chain_of_custody" in r_keys else "NOT PROVIDED",
                device_source=r["device_source"] if "device_source" in r_keys else "NOT PROVIDED",
                created_at=r["created_at"],
            )
        )
    return res


def update_evidence_status(ev_id: str, status: str, case_id: Optional[str] = None):
    init_db()
    conn = get_db_connection()
    with conn:
        if case_id:
            conn.execute("UPDATE case_evidence SET status = ? WHERE id = ? AND case_id = ?", (status, ev_id, case_id))
        else:
            conn.execute("UPDATE case_evidence SET status = ? WHERE id = ?", (status, ev_id))
    conn.close()


# ---------- WITNESS CRUD ----------
def add_case_witness(case_id: str, witness_data: Dict[str, Any]) -> WitnessItem:
    init_db()
    w_id = witness_data.get("id") or f"W-{str(uuid.uuid4())[:4].upper()}"
    now = datetime.datetime.utcnow().isoformat()

    conn = get_db_connection()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO case_witnesses (
                id, case_id, called_by, name, role, connection_to_case,
                expected_testimony, linked_evidence_ids, linked_fact_indices,
                is_expert, status, testimony_turns, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                w_id,
                case_id,
                witness_data.get("called_by", "prosecution"),
                witness_data.get("name", "Witness"),
                witness_data.get("role", "eyewitness"),
                witness_data.get("connection_to_case", ""),
                witness_data.get("expected_testimony", ""),
                json.dumps(witness_data.get("linked_evidence_ids", [])),
                json.dumps(witness_data.get("linked_fact_indices", [])),
                1 if witness_data.get("is_expert") else 0,
                witness_data.get("status", "not_called"),
                json.dumps(witness_data.get("testimony_turns", [])),
                now,
            ),
        )
    conn.close()
    return get_case_witness_item(w_id, case_id)


def get_case_witness_item(w_id: str, case_id: Optional[str] = None) -> Optional[WitnessItem]:
    conn = get_db_connection()
    if case_id:
        row = conn.execute("SELECT * FROM case_witnesses WHERE id = ? AND case_id = ?", (w_id, case_id)).fetchone()
    else:
        row = conn.execute("SELECT * FROM case_witnesses WHERE id = ?", (w_id,)).fetchone()
    conn.close()
    if not row:
        return None
    r_keys = row.keys()
    return WitnessItem(
        id=row["id"],
        case_id=row["case_id"],
        called_by=row["called_by"],
        name=row["name"],
        role=row["role"],
        connection_to_case=row["connection_to_case"],
        expected_testimony=row["expected_testimony"],
        linked_evidence_ids=json.loads(row["linked_evidence_ids"]) if "linked_evidence_ids" in r_keys and row["linked_evidence_ids"] else [],
        linked_fact_indices=json.loads(row["linked_fact_indices"]) if "linked_fact_indices" in r_keys and row["linked_fact_indices"] else [],
        is_expert=bool(row["is_expert"]) if "is_expert" in r_keys else False,
        status=row["status"],
        testimony_turns=json.loads(row["testimony_turns"]) if "testimony_turns" in r_keys and row["testimony_turns"] else [],
        created_at=row["created_at"],
    )


def get_case_witnesses(case_id: str) -> List[WitnessItem]:
    init_db()
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM case_witnesses WHERE case_id = ? ORDER BY id ASC", (case_id,)).fetchall()
    conn.close()
    res = []
    for r in rows:
        r_keys = r.keys()
        res.append(
            WitnessItem(
                id=r["id"],
                case_id=r["case_id"],
                called_by=r["called_by"],
                name=r["name"],
                role=r["role"],
                connection_to_case=r["connection_to_case"],
                expected_testimony=r["expected_testimony"],
                linked_evidence_ids=json.loads(r["linked_evidence_ids"]) if "linked_evidence_ids" in r_keys and r["linked_evidence_ids"] else [],
                linked_fact_indices=json.loads(r["linked_fact_indices"]) if "linked_fact_indices" in r_keys and r["linked_fact_indices"] else [],
                is_expert=bool(r["is_expert"]) if "is_expert" in r_keys else False,
                status=r["status"],
                testimony_turns=json.loads(r["testimony_turns"]) if "testimony_turns" in r_keys and r["testimony_turns"] else [],
                created_at=r["created_at"],
            )
        )
    return res


def update_witness_status(w_id: str, status: str, turn_record: Optional[Dict[str, Any]] = None, case_id: Optional[str] = None):
    init_db()
    conn = get_db_connection()
    with conn:
        if case_id:
            row = conn.execute("SELECT testimony_turns FROM case_witnesses WHERE id = ? AND case_id = ?", (w_id, case_id)).fetchone()
        else:
            row = conn.execute("SELECT testimony_turns FROM case_witnesses WHERE id = ?", (w_id,)).fetchone()
        turns = []
        if row and row["testimony_turns"]:
            try:
                turns = json.loads(row["testimony_turns"])
            except Exception:
                turns = []
        if turn_record:
            turns.append(turn_record)
        if case_id:
            conn.execute(
                "UPDATE case_witnesses SET status = ?, testimony_turns = ? WHERE id = ? AND case_id = ?",
                (status, json.dumps(turns), w_id, case_id),
            )
        else:
            conn.execute(
                "UPDATE case_witnesses SET status = ?, testimony_turns = ? WHERE id = ?",
                (status, json.dumps(turns), w_id),
            )
    conn.close()


# ---------- COURTROOM EVENTS AUDIT ----------
def save_courtroom_event(
    case_id: str,
    stage: str,
    event_type: str,
    content: str,
    speaker: Optional[str] = None,
    witness_id: Optional[str] = None,
    question_turn: Optional[int] = None,
    objection: Optional[Dict[str, Any]] = None,
    evidence_id: Optional[str] = None,
    evidence_action: Optional[str] = None,
) -> CourtroomEvent:
    init_db()
    evt_id = f"evt_{str(uuid.uuid4())[:8]}"
    now = datetime.datetime.utcnow().isoformat()

    conn = get_db_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO courtroom_events (
                id, case_id, stage, event_type, speaker, witness_id,
                content, question_turn, objection, evidence_id, evidence_action, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                evt_id,
                case_id,
                stage,
                event_type,
                speaker,
                witness_id,
                content,
                question_turn,
                json.dumps(objection) if objection else None,
                evidence_id,
                evidence_action,
                now,
            ),
        )
    conn.close()
    return CourtroomEvent(
        id=evt_id,
        case_id=case_id,
        stage=stage,
        event_type=event_type,
        speaker=speaker,
        witness_id=witness_id,
        content=content,
        question_turn=question_turn,
        objection=objection,
        evidence_id=evidence_id,
        evidence_action=evidence_action,
        timestamp=now,
    )


def get_courtroom_events(case_id: str) -> List[CourtroomEvent]:
    init_db()
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM courtroom_events WHERE case_id = ? ORDER BY timestamp ASC", (case_id,)
    ).fetchall()
    conn.close()
    res = []
    for r in rows:
        r_keys = r.keys()
        obj = None
        if "objection" in r_keys and r["objection"]:
            try:
                obj = json.loads(r["objection"])
            except Exception:
                obj = None
        res.append(
            CourtroomEvent(
                id=r["id"],
                case_id=r["case_id"],
                stage=r["stage"],
                event_type=r["event_type"],
                speaker=r["speaker"] if "speaker" in r_keys else None,
                witness_id=r["witness_id"] if "witness_id" in r_keys else None,
                content=r["content"],
                question_turn=r["question_turn"] if "question_turn" in r_keys else None,
                objection=obj,
                evidence_id=r["evidence_id"] if "evidence_id" in r_keys else None,
                evidence_action=r["evidence_action"] if "evidence_action" in r_keys else None,
                timestamp=r["timestamp"],
            )
        )
    return res


# ---------- CANONICAL DEMO SEEDING ----------
def get_or_create_demo_case() -> CaseDetail:
    init_db()
    existing = get_case_by_id(DEMO_CASE_ID)
    if existing and existing.evidence_list and len(existing.evidence_list) >= 6 and existing.witnesses_list and len(existing.witnesses_list) >= 5:
        return existing

    demo_facts = (
        "Sameer Kapoor travelled in Coach C2 of the Mumbai–Pune Intercity Express on 18 August 2026. "
        "Sameer was discovered with a fatal chest injury near the vestibule between coaches C2 and C3 at approximately 8:44 PM. "
        "Rohan Verma and Sameer Kapoor had an active ₹12 lakh business loan dispute with contentious text exchanges. "
        "Rohan Verma had a confirmed reservation in Coach C2. "
        "Passengers heard raised voices near the vestibule at approximately 8:42 PM. "
        "Rohan was observed by a passenger walking toward the vestibule at 8:40 PM. "
        "Rohan returned toward his seat at 8:45 PM looking visibly hurried. "
        "A single-edged folding knife was recovered under seat 42 in Coach C2 three stations later in Karjat. "
        "Forensic laboratory analysis established no definitive latent fingerprints matching Rohan Verma on the weapon. "
        "Rohan claims he went to the restroom and had no physical altercation with Sameer."
    )
    demo_charge = "Homicide / Murder under Bharatiya Nyaya Sanhita, 2023 §103 — Alleged fatal stabbing of Sameer Kapoor aboard Mumbai–Pune Intercity Express."

    case = create_case_record(
        title="State of Maharashtra v. Rohan Verma",
        facts=demo_facts,
        charge_or_dispute=demo_charge,
        case_category="criminal",
        simulation_type="standard",
        jurisdiction="Sessions Court, Greater Mumbai",
        total_rounds=3,
        case_type="demo",
        custom_id=DEMO_CASE_ID,
    )

    # Seed 6 Prosecution Exhibits + 3 Defence Exhibits
    add_case_evidence(
        DEMO_CASE_ID,
        {
            "id": "P-EX-01",
            "submitted_by": "prosecution",
            "title": "Train Corridor CCTV Footage",
            "evidence_type": "digital_record",
            "description": "CCTV footage from Coach C2 corridor showing movements toward the vestibule between 8:38 PM and 8:47 PM.",
            "source": "Central Railway Security Server",
            "date": "18 August 2026",
            "supports_facts": ["Fact #1", "Fact #6", "Fact #7"],
            "status": "ready_to_offer",
            "file_hash": "SHA-256: 4f9e11a28b0c...",
            "chain_of_custody": "Extracted by RPF Sub-Inspector Shinde",
            "device_source": "Coach C2 Overhead Cam 02",
        },
    )
    add_case_evidence(
        DEMO_CASE_ID,
        {
            "id": "P-EX-02",
            "submitted_by": "prosecution",
            "title": "Reservation Chart Coach C2",
            "evidence_type": "document",
            "description": "Official Indian Railways reservation chart showing seats for Rohan Verma (Seat 18) and Sameer Kapoor (Seat 32).",
            "source": "IRCTC Reservation Database",
            "date": "18 August 2026",
            "supports_facts": ["Fact #1", "Fact #4"],
            "status": "ready_to_offer",
            "file_hash": "NOT PROVIDED",
            "chain_of_custody": "Produced by Ticket Examiner",
            "device_source": "NOT PROVIDED",
        },
    )
    add_case_evidence(
        DEMO_CASE_ID,
        {
            "id": "P-EX-03",
            "submitted_by": "prosecution",
            "title": "WhatsApp Message Transcript ₹12L Dispute",
            "evidence_type": "digital_record",
            "description": "Certified electronic message transcript detailing the ₹12 lakh loan default dispute between parties.",
            "source": "Cyber Cell Forensics Unit",
            "date": "16 August 2026",
            "supports_facts": ["Fact #3"],
            "status": "ready_to_offer",
            "file_hash": "SHA-256: d918f0c239a...",
            "chain_of_custody": "Extracted under BSA §63 certificate",
            "device_source": "Victim Mobile Device",
        },
    )
    add_case_evidence(
        DEMO_CASE_ID,
        {
            "id": "P-EX-04",
            "submitted_by": "prosecution",
            "title": "Medical Post-Mortem Examination Report",
            "evidence_type": "expert_report",
            "description": "Autopsy report establishing single incised puncture wound causing fatal hemorrhage.",
            "source": "KEM Hospital Forensic Dept",
            "date": "19 August 2026",
            "supports_facts": ["Fact #2"],
            "status": "ready_to_offer",
            "file_hash": "NOT PROVIDED",
            "chain_of_custody": "Dr. Anjali Deshmukh",
            "device_source": "NOT PROVIDED",
        },
    )
    add_case_evidence(
        DEMO_CASE_ID,
        {
            "id": "P-EX-05",
            "submitted_by": "prosecution",
            "title": "Coach Attendant Duty Log",
            "evidence_type": "document",
            "description": "Logbook recording vestibule door inspection and emergency alarm activation at 8:48 PM.",
            "source": "Central Railway Operations",
            "date": "18 August 2026",
            "supports_facts": ["Fact #2", "Fact #8"],
            "status": "ready_to_offer",
            "file_hash": "NOT PROVIDED",
            "chain_of_custody": "Produced by Attendant Suresh Patil",
            "device_source": "NOT PROVIDED",
        },
    )
    add_case_evidence(
        DEMO_CASE_ID,
        {
            "id": "P-EX-06",
            "submitted_by": "prosecution",
            "title": "Recovered Knife Seizure Panchnama",
            "evidence_type": "physical_object",
            "description": "Seizure memo for 4-inch single-edged folding knife recovered under Coach C2 seat 42 at Karjat Station.",
            "source": "Maharashtra Police Seizure Record",
            "date": "18 August 2026",
            "supports_facts": ["Fact #8", "Fact #9"],
            "status": "ready_to_offer",
            "file_hash": "NOT PROVIDED",
            "chain_of_custody": "Seized by IO Inspector Kadam",
            "device_source": "NOT PROVIDED",
        },
    )
    add_case_evidence(
        DEMO_CASE_ID,
        {
            "id": "D-EX-01",
            "submitted_by": "defense",
            "title": "Rohan Phone GPS & Tower Telemetry Log",
            "evidence_type": "digital_record",
            "description": "Cellular tower triangulation data confirming device presence in passenger seat area.",
            "source": "Telecom Service Provider",
            "date": "18 August 2026",
            "supports_facts": ["Fact #10"],
            "status": "ready_to_offer",
            "file_hash": "SHA-256: 7b22a019e...",
            "chain_of_custody": "Produced by Defence Cyber Expert",
            "device_source": "Carrier CDR Records",
        },
    )
    add_case_evidence(
        DEMO_CASE_ID,
        {
            "id": "D-EX-02",
            "submitted_by": "defense",
            "title": "Bank Settlement Acknowledgment Agreement",
            "evidence_type": "document",
            "description": "Signed pre-settlement memo agreeing to restructure loan repayments by November 2026.",
            "source": "Verma & Associates Legal Records",
            "date": "10 August 2026",
            "supports_facts": ["Fact #3"],
            "status": "ready_to_offer",
            "file_hash": "NOT PROVIDED",
            "chain_of_custody": "Produced by Defence Counsel",
            "device_source": "NOT PROVIDED",
        },
    )
    add_case_evidence(
        DEMO_CASE_ID,
        {
            "id": "D-EX-03",
            "submitted_by": "defense",
            "title": "Forensic Latent Fingerprint Exclusion Report",
            "evidence_type": "forensic_report",
            "description": "State Forensic Science Laboratory report confirming no ridge impressions of Rohan Verma on weapon.",
            "source": "State Forensic Science Laboratory, Kalina",
            "date": "22 August 2026",
            "supports_facts": ["Fact #9"],
            "status": "ready_to_offer",
            "file_hash": "SHA-256: a188e49fc01...",
            "chain_of_custody": "Produced by Forensic Expert",
            "device_source": "FSL Kalina Lab Unit",
        },
    )

    # Seed 5 Prosecution Witnesses + 1 Defence Witness
    add_case_witness(
        DEMO_CASE_ID,
        {
            "id": "PW-01",
            "called_by": "prosecution",
            "name": "Meera Joshi",
            "role": "eyewitness",
            "connection_to_case": "Co-passenger seated in Coach C2, Seat 24",
            "expected_testimony": "Testify regarding observing Rohan Verma walk toward the vestibule at 8:40 PM and return hurried at 8:45 PM.",
            "linked_evidence_ids": ["P-EX-01", "P-EX-02"],
            "linked_fact_indices": [1, 6, 7],
            "is_expert": False,
            "status": "on_stand",
        },
    )
    add_case_witness(
        DEMO_CASE_ID,
        {
            "id": "PW-02",
            "called_by": "prosecution",
            "name": "Aditya Rao",
            "role": "eyewitness",
            "connection_to_case": "Passenger seated near Coach C2 rear vestibule",
            "expected_testimony": "Testify to hearing raised voices and an argument near the vestibule at approximately 8:42 PM.",
            "linked_evidence_ids": ["P-EX-01"],
            "linked_fact_indices": [5],
            "is_expert": False,
            "status": "not_called",
        },
    )
    add_case_witness(
        DEMO_CASE_ID,
        {
            "id": "PW-03",
            "called_by": "prosecution",
            "name": "Suresh Patil",
            "role": "employee",
            "connection_to_case": "Railway Coach Attendant on duty in Coach C2",
            "expected_testimony": "Describe finding the victim unconscious and the subsequent recovery of the knife under seat 42.",
            "linked_evidence_ids": ["P-EX-05", "P-EX-06"],
            "linked_fact_indices": [2, 8],
            "is_expert": False,
            "status": "not_called",
        },
    )
    add_case_witness(
        DEMO_CASE_ID,
        {
            "id": "PW-04",
            "called_by": "prosecution",
            "name": "Inspector Sanjay Kadam",
            "role": "investigating_officer",
            "connection_to_case": "Lead Investigating Officer, GRP Crime Branch",
            "expected_testimony": "Outline the crime scene panchnama, weapon recovery, and financial dispute background.",
            "linked_evidence_ids": ["P-EX-03", "P-EX-06"],
            "linked_fact_indices": [3, 8, 9],
            "is_expert": False,
            "status": "not_called",
        },
    )
    add_case_witness(
        DEMO_CASE_ID,
        {
            "id": "PW-05",
            "called_by": "prosecution",
            "name": "Dr. Anjali Deshmukh",
            "role": "expert",
            "connection_to_case": "Forensic Medical Examiner, KEM Hospital",
            "expected_testimony": "Explain the nature of the fatal incised wound and estimated time of injury.",
            "linked_evidence_ids": ["P-EX-04"],
            "linked_fact_indices": [2],
            "is_expert": True,
            "status": "not_called",
        },
    )
    add_case_witness(
        DEMO_CASE_ID,
        {
            "id": "DW-01",
            "called_by": "defense",
            "name": "Rohan Verma",
            "role": "eyewitness",
            "connection_to_case": "Accused, appearing as Defence Witness",
            "expected_testimony": "Explain that he visited the train restroom, was not in the vestibule with Sameer, and denies any physical altercation.",
            "linked_evidence_ids": ["D-EX-01", "D-EX-02", "D-EX-03"],
            "linked_fact_indices": [4, 10],
            "is_expert": False,
            "status": "not_called",
        },
    )

    return get_case_by_id(DEMO_CASE_ID)


# ---------- CASE RETRIEVAL ----------
def get_case_by_id(case_id: str) -> Optional[CaseDetail]:
    init_db()
    conn = get_db_connection()

    case_row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    if not case_row:
        conn.close()
        return None

    keys = case_row.keys()
    case_type = case_row["case_type"] if "case_type" in keys else "user"
    status_str = case_row["status"]
    case_category = case_row["case_category"] if "case_category" in keys else "criminal"
    simulation_type = case_row["simulation_type"] if "simulation_type" in keys else "standard"
    jurisdiction = case_row["jurisdiction"] if "jurisdiction" in keys else "Sessions Court, Bhubaneswar"
    curr_witness = case_row["current_witness_id"] if "current_witness_id" in keys else None

    try:
        status = CaseStatus(status_str)
    except ValueError:
        if status_str in ("statements_recorded", "in_progress"):
            status = CaseStatus.TRIAL_IN_PROGRESS
        else:
            status = CaseStatus.FILED

    fact_rows = conn.execute(
        "SELECT * FROM case_facts WHERE case_id = ? ORDER BY fact_index ASC", (case_id,)
    ).fetchall()
    facts_list = [
        CaseFact(
            id=r["id"],
            case_id=r["case_id"],
            fact_index=r["fact_index"],
            content=r["content"],
        )
        for r in fact_rows
    ]

    # Evidence & Witnesses
    evidence_list = get_case_evidence(case_id)
    witnesses_list = get_case_witnesses(case_id)
    courtroom_events = get_courtroom_events(case_id)

    # Party Statements
    ps_rows = conn.execute("SELECT * FROM party_statements WHERE case_id = ?", (case_id,)).fetchall()
    pros_stmt, def_stmt = None, None
    for r in ps_rows:
        r_keys = r.keys()
        allegations = json.loads(r["key_allegations"]) if "key_allegations" in r_keys and r["key_allegations"] else []
        facts_rel = json.loads(r["facts_relied_upon"]) if "facts_relied_upon" in r_keys and r["facts_relied_upon"] else []
        ev_rel = json.loads(r["evidence_relied_upon"]) if "evidence_relied_upon" in r_keys and r["evidence_relied_upon"] else []
        wit_rel = json.loads(r["witnesses_relied_upon"]) if "witnesses_relied_upon" in r_keys and r["witnesses_relied_upon"] else []
        pos_det = json.loads(r["position_details"]) if "position_details" in r_keys and r["position_details"] else {}

        stmt_obj = PartyStatement(
            speaker=Speaker(r["speaker"]),
            incident_account=r["incident_account"],
            key_allegations=allegations,
            what_is_disputed=r["what_is_disputed"] if "what_is_disputed" in r_keys else "",
            theory_of_case=r["theory_of_case"] if "theory_of_case" in r_keys else "",
            desired_outcome=r["desired_outcome"] if "desired_outcome" in r_keys else "",
            facts_relied_upon=facts_rel,
            evidence_relied_upon=ev_rel,
            witnesses_relied_upon=wit_rel,
            is_submitted=True,
            position_details=pos_det,
            updated_at=r["updated_at"],
        )
        if r["speaker"] == "prosecution":
            pros_stmt = stmt_obj
        else:
            def_stmt = stmt_obj

    locked = bool(case_row["statements_locked"]) if "statements_locked" in keys else False
    statements = None
    if pros_stmt or def_stmt:
        statements = CaseStatements(
            case_id=case_id,
            prosecution=pros_stmt,
            defense=def_stmt,
            is_locked=locked,
        )

    issue_rows = conn.execute(
        "SELECT * FROM case_issues WHERE case_id = ? ORDER BY issue_id ASC", (case_id,)
    ).fetchall()
    legal_issues = [
        LegalIssue(
            issue_id=r["issue_id"],
            question=r["question"],
            prosecution_position=r["prosecution_position"],
            defense_position=r["defense_position"],
            judge_finding=r["judge_finding"] if "judge_finding" in r.keys() else "Pending deliberation",
            finding_rationale=r["finding_rationale"] if "finding_rationale" in r.keys() else "",
        )
        for r in issue_rows
    ]

    matched_law_dicts = law_service.match_applicable_laws(case_row["fact_pattern"], case_row["charge_or_dispute"])
    applicable_laws = [ApplicableLaw(**l) for l in matched_law_dicts]

    arg_rows = conn.execute(
        "SELECT * FROM arguments WHERE case_id = ? ORDER BY created_at ASC", (case_id,)
    ).fetchall()
    arguments = []
    transcript = []
    for r in arg_rows:
        r_keys = r.keys()
        ev_refs = []
        try:
            ev_refs = json.loads(r["evidence_references"]) if "evidence_references" in r_keys and r["evidence_references"] else []
        except Exception:
            ev_refs = []

        arg_obj = Argument(
            id=r["id"],
            case_id=r["case_id"],
            round_number=r["round_number"],
            speaker=Speaker(r["speaker"]),
            stage_type=r["stage_type"],
            content=r["content"],
            argument_type=r["argument_type"] if "argument_type" in r_keys else "factual evidence",
            argument_strength=r["argument_strength"] if "argument_strength" in r_keys else "moderate",
            legal_basis=(r["legal_basis"] if "legal_basis" in r_keys and r["legal_basis"] else "BNS §303 — Theft"),
            party_statement_ref=r["party_statement_ref"] if "party_statement_ref" in r_keys else None,
            evidence_references=ev_refs,
            responds_to_argument_id=r["responds_to_argument_id"] if "responds_to_argument_id" in r_keys else None,
            is_contradiction_flagged=bool(r["is_contradiction_flagged"]) if "is_contradiction_flagged" in r_keys else False,
            contradiction_note=r["contradiction_note"] if "contradiction_note" in r_keys else None,
            is_unsupported_flagged=bool(r["is_unsupported_flagged"]) if "is_unsupported_flagged" in r_keys else False,
            unsupported_note=r["unsupported_note"] if "unsupported_note" in r_keys else None,
            created_at=r["created_at"],
        )
        arguments.append(arg_obj)
        transcript.append(
            TranscriptEntry(
                speaker=arg_obj.speaker,
                stage=arg_obj.stage_type,
                text=arg_obj.content,
                argument_type=arg_obj.argument_type,
                argument_strength=arg_obj.argument_strength,
                timestamp=arg_obj.created_at,
            )
        )

    verdict_row = conn.execute("SELECT * FROM verdicts WHERE case_id = ?", (case_id,)).fetchone()
    verdict = None
    if verdict_row:
        v_keys = verdict_row.keys()
        try:
            iss_find_raw = json.loads(verdict_row["issue_findings"]) if "issue_findings" in v_keys and verdict_row["issue_findings"] else []
            iss_findings = [IssueFinding(**f) for f in iss_find_raw]
            law_ass_raw = json.loads(verdict_row["law_assessments"]) if "law_assessments" in v_keys and verdict_row["law_assessments"] else []
            law_assessments = [LawAssessment(**l) for l in law_ass_raw]
            pros_str = json.loads(verdict_row["prosecution_strengths"]) if "prosecution_strengths" in v_keys and verdict_row["prosecution_strengths"] else []
            def_str = json.loads(verdict_row["defense_strengths"]) if "defense_strengths" in v_keys and verdict_row["defense_strengths"] else []
            k_fac = json.loads(verdict_row["key_factors"]) if "key_factors" in v_keys and verdict_row["key_factors"] else []
            ev_gap = json.loads(verdict_row["evidence_gaps"]) if "evidence_gaps" in v_keys and verdict_row["evidence_gaps"] else []
            aff_def_raw = json.loads(verdict_row["affirmative_defense_analysis"]) if "affirmative_defense_analysis" in v_keys and verdict_row["affirmative_defense_analysis"] else {}
        except Exception:
            iss_findings, law_assessments, pros_str, def_str, k_fac, ev_gap, aff_def_raw = [], [], [], [], [], [], {}

        verdict = Verdict(
            id=verdict_row["id"],
            case_id=verdict_row["case_id"],
            winner=verdict_row["winner"] if "winner" in v_keys and verdict_row["winner"] else "defense_prevailed",
            decision=verdict_row["decision"],
            verdict_category=verdict_row["verdict_category"] if "verdict_category" in v_keys else "not_guilty",
            confidence=verdict_row["confidence"] if "confidence" in v_keys else "0.85",
            decision_basis=verdict_row["decision_basis"] if "decision_basis" in v_keys and verdict_row["decision_basis"] else "",
            reasoning_summary=verdict_row["reasoning_summary"] if "reasoning_summary" in v_keys and verdict_row["reasoning_summary"] else "",
            reasoning=verdict_row["reasoning_summary"] if "reasoning_summary" in v_keys and verdict_row["reasoning_summary"] else "",
            issue_findings=iss_findings,
            law_assessments=law_assessments,
            affirmative_defense_analysis=aff_def_raw,
            prosecution_strengths=pros_str,
            defense_strengths=def_str,
            key_factors=k_fac,
            evidence_gaps=ev_gap,
            created_at=verdict_row["created_at"],
        )

    log_rows = conn.execute(
        "SELECT * FROM audit_logs WHERE case_id = ? ORDER BY timestamp DESC", (case_id,)
    ).fetchall()
    audit_logs = [
        AuditLog(
            id=r["id"],
            case_id=r["case_id"],
            event_type=r["event_type"],
            description=r["description"],
            timestamp=r["timestamp"],
        )
        for r in log_rows
    ]

    conn.close()

    clamped_round = min(case_row["current_round"], case_row["total_rounds"])

    return CaseDetail(
        id=case_row["id"],
        docket_number=case_row["docket_number"],
        title=case_row["title"],
        facts=case_row["fact_pattern"],
        charge_or_dispute=case_row["charge_or_dispute"],
        case_category=case_category,
        counsel_filing_id=case_row["counsel_filing_id"] if "counsel_filing_id" in keys and case_row["counsel_filing_id"] else "agent_02",
        counsel_opposing_id=case_row["counsel_opposing_id"] if "counsel_opposing_id" in keys and case_row["counsel_opposing_id"] else "agent_01",
        simulation_type=simulation_type,
        jurisdiction=jurisdiction,
        total_rounds=case_row["total_rounds"],
        case_type=case_type,
        status=status,
        current_stage=case_row["current_stage"],
        current_speaker=case_row["current_speaker"],
        current_witness_id=curr_witness,
        current_round=clamped_round,
        facts_list=facts_list,
        evidence_list=evidence_list,
        witnesses_list=witnesses_list,
        statements=statements,
        legal_issues=legal_issues,
        applicable_laws=applicable_laws,
        arguments=arguments,
        courtroom_events=courtroom_events,
        transcript=transcript,
        verdict=verdict,
        audit_logs=audit_logs,
        created_at=case_row["created_at"],
        updated_at=case_row["updated_at"],
    )


def list_all_cases(
    status_filter: Optional[str] = None,
    case_type_filter: Optional[str] = None,
    sort_by: str = "updated_at",
) -> List[CaseDetail]:
    init_db()
    conn = get_db_connection()
    query = "SELECT id FROM cases"
    conditions = []
    params = []

    if status_filter and status_filter != "all":
        if status_filter == "ongoing":
            conditions.append("status IN ('trial_in_progress', 'in_progress')")
        elif status_filter == "active_hearings":
            conditions.append("status IN ('filed', 'statements_pending', 'legal_analysis', 'ready_for_trial', 'statements_recorded')")
        elif status_filter == "deliberation":
            conditions.append("status = 'deliberation'")
        elif status_filter == "resolved":
            conditions.append("status = 'resolved'")
        elif status_filter == "archived":
            conditions.append("status = 'archived'")
        else:
            conditions.append("status = ?")
            params.append(status_filter)

    if case_type_filter:
        conditions.append("case_type = ?")
        params.append(case_type_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    if sort_by == "created_at":
        query += " ORDER BY created_at DESC"
    elif sort_by == "status":
        query += " ORDER BY status ASC, updated_at DESC"
    else:
        query += " ORDER BY updated_at DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    result = []
    for r in rows:
        c = get_case_by_id(r["id"])
        if c:
            result.append(c)
    return result


def get_dashboard_metrics(include_benchmarks: bool = False) -> Dict[str, Any]:
    init_db()
    conn = get_db_connection()

    type_filter = "" if include_benchmarks else "WHERE case_type = 'user'"
    where_and = "" if include_benchmarks else "AND case_type = 'user'"

    total_cases = conn.execute(f"SELECT COUNT(*) FROM cases {type_filter}").fetchone()[0]
    active_trials = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE status IN ('trial_in_progress', 'in_progress') {where_and}"
    ).fetchone()[0]
    in_deliberation = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE status = 'deliberation' {where_and}"
    ).fetchone()[0]
    resolved_cases = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE status = 'resolved' {where_and}"
    ).fetchone()[0]

    # Calculate real verdict percentages
    guilty_count = conn.execute(
        f"SELECT COUNT(*) FROM verdicts v JOIN cases c ON v.case_id = c.id WHERE (v.verdict_category = 'guilty' OR (v.decision LIKE '%guilty%' AND v.decision NOT LIKE '%not guilty%')) {where_and}"
    ).fetchone()[0]
    not_guilty_count = conn.execute(
        f"SELECT COUNT(*) FROM verdicts v JOIN cases c ON v.case_id = c.id WHERE (v.verdict_category = 'not_guilty' OR v.decision LIKE '%not guilty%') {where_and}"
    ).fetchone()[0]
    other_verdicts = max(0, resolved_cases - (guilty_count + not_guilty_count))

    verdict_distribution = {
        "guilty_count": guilty_count,
        "not_guilty_count": not_guilty_count,
        "other_count": other_verdicts,
        "total_resolved": resolved_cases,
        "guilty_pct": round((guilty_count / resolved_cases * 100)) if resolved_cases > 0 else 0,
        "not_guilty_pct": round((not_guilty_count / resolved_cases * 100)) if resolved_cases > 0 else 0,
        "other_pct": round((other_verdicts / resolved_cases * 100)) if resolved_cases > 0 else 0,
    }

    # 1. Ongoing Trials (status = TRIAL_IN_PROGRESS, max 3)
    ongoing_rows = conn.execute(
        f"SELECT id FROM cases WHERE status IN ('trial_in_progress', 'in_progress') {where_and} ORDER BY updated_at DESC LIMIT 3"
    ).fetchall()
    ongoing_trials = [get_case_by_id(r["id"]) for r in ongoing_rows if get_case_by_id(r["id"])]

    # 2. Active Hearings (status IN FILED, STATEMENTS_PENDING, LEGAL_ANALYSIS, READY_FOR_TRIAL, max 3)
    hearing_rows = conn.execute(
        f"SELECT id FROM cases WHERE status IN ('filed', 'statements_pending', 'legal_analysis', 'ready_for_trial', 'statements_recorded') {where_and} ORDER BY updated_at DESC LIMIT 3"
    ).fetchall()
    active_hearings = [get_case_by_id(r["id"]) for r in hearing_rows if get_case_by_id(r["id"])]

    # 3. Awaiting Judgment (status = DELIBERATION, max 3)
    delib_rows = conn.execute(
        f"SELECT id FROM cases WHERE status = 'deliberation' {where_and} ORDER BY updated_at DESC LIMIT 3"
    ).fetchall()
    awaiting_judgment = [get_case_by_id(r["id"]) for r in delib_rows if get_case_by_id(r["id"])]

    # 4. Resolved Cases (status = RESOLVED, max 3)
    resolved_rows = conn.execute(
        f"SELECT id FROM cases WHERE status = 'resolved' {where_and} ORDER BY updated_at DESC LIMIT 3"
    ).fetchall()
    resolved_cases_list = [get_case_by_id(r["id"]) for r in resolved_rows if get_case_by_id(r["id"])]

    # 5. Recent Activity Feed (max 5 items)
    activity_rows = conn.execute(
        """
        SELECT a.event_type, a.description, a.timestamp, c.id as case_id, c.title as case_title
        FROM audit_logs a
        JOIN cases c ON a.case_id = c.id
        ORDER BY a.timestamp DESC
        LIMIT 5
    """
    ).fetchall()
    recent_activity = [
        {
            "event_type": r["event_type"],
            "description": r["description"],
            "timestamp": r["timestamp"],
            "case_id": r["case_id"],
            "case_title": r["case_title"],
        }
        for r in activity_rows
    ]

    conn.close()

    return {
        "total_dockets": total_cases,
        "active_trials": active_trials,
        "in_deliberation": in_deliberation,
        "resolved_cases": resolved_cases,
        "verdict_distribution": verdict_distribution,
        "ongoing_trials": ongoing_trials,
        "active_hearings": active_hearings,
        "awaiting_judgment": awaiting_judgment,
        "resolved_cases_list": resolved_cases_list,
        "recent_activity": recent_activity,
    }


def save_argument_record(arg: Argument) -> Argument:
    init_db()
    conn = get_db_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO arguments (
                id, case_id, round_number, speaker, stage_type, content,
                argument_type, argument_strength, legal_basis, party_statement_ref,
                evidence_references, responds_to_argument_id,
                is_contradiction_flagged, contradiction_note, is_unsupported_flagged, unsupported_note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                arg.id,
                arg.case_id,
                arg.round_number,
                arg.speaker.value if isinstance(arg.speaker, Speaker) else str(arg.speaker),
                arg.stage_type,
                arg.content,
                arg.argument_type,
                arg.argument_strength,
                arg.legal_basis,
                arg.party_statement_ref,
                json.dumps(arg.evidence_references),
                arg.responds_to_argument_id,
                1 if arg.is_contradiction_flagged else 0,
                arg.contradiction_note,
                1 if arg.is_unsupported_flagged else 0,
                arg.unsupported_note,
                arg.created_at,
            ),
        )
    conn.close()
    return arg


def save_verdict_record(verdict: Verdict) -> Verdict:
    init_db()
    conn = get_db_connection()
    aff_def = verdict.affirmative_defense_analysis
    if hasattr(aff_def, "model_dump"):
        aff_def_json = json.dumps(aff_def.model_dump())
    elif isinstance(aff_def, dict):
        aff_def_json = json.dumps(aff_def)
    else:
        aff_def_json = "{}"

    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO verdicts (
                id, case_id, winner, decision, verdict_category, confidence, decision_basis,
                reasoning_summary, issue_findings, law_assessments, affirmative_defense_analysis,
                prosecution_strengths, defense_strengths, key_factors, evidence_gaps, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                verdict.id,
                verdict.case_id,
                verdict.winner,
                verdict.decision,
                verdict.verdict_category,
                str(verdict.confidence),
                verdict.decision_basis,
                verdict.reasoning_summary,
                json.dumps([f.model_dump() for f in verdict.issue_findings]),
                json.dumps([l.model_dump() for l in verdict.law_assessments]),
                aff_def_json,
                json.dumps(verdict.prosecution_strengths),
                json.dumps(verdict.defense_strengths),
                json.dumps(verdict.key_factors),
                json.dumps(verdict.evidence_gaps),
                verdict.created_at,
            ),
        )
        now = datetime.datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE cases SET status = ?, current_stage = 'case_resolved', updated_at = ? WHERE id = ?",
            (CaseStatus.RESOLVED.value, now, verdict.case_id),
        )
    conn.close()
    return verdict


def save_single_party_statement(
    case_id: str,
    speaker: str,
    incident_account: str,
    key_allegations: List[str] = [],
    what_is_disputed: str = "",
    theory_of_case: str = "",
    desired_outcome: str = "",
    facts_relied_upon: List[str] = [],
    evidence_relied_upon: List[str] = [],
    witnesses_relied_upon: List[str] = [],
) -> CaseDetail:
    init_db()
    stmt_id = f"ps_{speaker}_{case_id}"
    now = datetime.datetime.utcnow().isoformat()

    conn = get_db_connection()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO party_statements (
                id, case_id, speaker, incident_account, key_allegations,
                what_is_disputed, theory_of_case, desired_outcome, facts_relied_upon,
                evidence_relied_upon, witnesses_relied_upon, position_details, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '{}', ?)
        """,
            (
                stmt_id,
                case_id,
                speaker,
                incident_account,
                json.dumps(key_allegations),
                what_is_disputed,
                theory_of_case,
                desired_outcome,
                json.dumps(facts_relied_upon),
                json.dumps(evidence_relied_upon),
                json.dumps(witnesses_relied_upon),
                now,
            ),
        )
        conn.execute(
            "UPDATE cases SET status = ?, current_stage = 'statements_pending', updated_at = ? WHERE id = ?",
            (CaseStatus.STATEMENTS_PENDING.value, now, case_id),
        )
    conn.close()
    return get_case_by_id(case_id)
