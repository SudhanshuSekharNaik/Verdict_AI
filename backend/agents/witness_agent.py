from typing import Any, Dict, List, Optional
from agents.base_agent import BaseCourtroomAgent


class WitnessAgent(BaseCourtroomAgent):
    """
    Simulates a sworn witness on the stand in the Indian courtroom simulation.
    Answers questions strictly from:
    1. Assigned witness role and connection to case
    2. Explicitly linked canonical facts and expected testimony
    3. Exhibits shown to the witness

    NEVER invents facts, events, documents, or observations not provided in the case record.
    If asked about matters outside their knowledge, states: "I do not have personal knowledge or records establishing that."
    """

    def __init__(
        self,
        case_title: str,
        canonical_facts: str,
        witness_id: str,
        witness_name: str,
        role: str,
        connection_to_case: str,
        expected_testimony: str,
        linked_facts: List[str] = [],
        linked_exhibits: List[str] = [],
    ):
        system_prompt = f"""You are SWORN WITNESS "{witness_name}" (ID: {witness_id}, Role: {role}) testifying under solemn affirmation in the judicial proceeding "{case_title}".

WITNESS PROFILE & SCOPE OF KNOWLEDGE:
- Formal Role: {role}
- Connection to Case: {connection_to_case}
- Personal Observations & Sworn Scope: {expected_testimony}
- Linked Canonical Facts: {', '.join(linked_facts) if linked_facts else 'General case background'}
- Admitted Exhibits / Documents: {', '.join(linked_exhibits) if linked_exhibits else 'None'}

CANONICAL CASE DOSSIER:
{canonical_facts}

SWORN TESTIMONY & PROFESSIONALISM RULES:
1. TESTIFY STRICTLY IN CHARACTER: Speak in the first person with dignified, natural, and realistic composure appropriate for your role (e.g. an observant co-passenger, an official investigating officer referring to case diaries, a technical expert citing forensic data, or a family member).
2. HIGH-QUALITY SUBSTANTIVE ANSWERS: Provide 2 to 3 articulate, meaningful sentences directly answering the counsel's query with specific factual details from your personal knowledge scope.
3. NEVER INVENT FICTIONAL EVENTS: Do not invent unverified confessions, secret documents, or conversations absent from the case dossier.
4. ACKNOWLEDGE BOUNDARIES DIGNIFIEDLY: When asked during cross-examination about facts beyond your eyesight or documentation, respond with honest clarity: "I cannot confirm what occurred outside my direct observation" or "Our station records do not reflect that circumstance."

Return ONLY a valid JSON object:
{{
  "witness_id": "{witness_id}",
  "witness_name": "{witness_name}",
  "answer": "<your 2-3 sentence articulate, meaningful, and character-authentic testimony>",
  "facts_referenced": ["Fact #N", ...],
  "exhibits_referenced": ["P-EX-01", ...],
  "admits_lack_of_knowledge": <true|false>
}}"""
        super().__init__(system_prompt)

    def answer_question(
        self,
        examining_counsel: str,  # "prosecution" or "defense"
        examination_type: str,   # "examination_in_chief", "cross_examination", "re_examination"
        question: str,
        prior_testimony_summary: str = "",
    ) -> Dict[str, Any]:
        counsel_title = "Public Prosecutor / Filing Counsel" if examining_counsel.lower() == "prosecution" else "Defense Counsel"
        stage_title = "EXAMINATION-IN-CHIEF" if "chief" in examination_type.lower() else "CROSS-EXAMINATION"
        prompt = f"""=== WITNESS STAND: {stage_title} ===
Examining Advocate: {counsel_title}
Question put to you under oath:
\"{question}\"

Prior testimony in this session:
{prior_testimony_summary if prior_testimony_summary else "Beginning of examination."}

Provide your sworn, authentic, and substantive answer as the specified JSON object."""
        return self.say_json(prompt, max_tokens=600, temperature=0.25)
