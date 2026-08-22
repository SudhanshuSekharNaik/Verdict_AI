from typing import Any, Dict, List, Optional
from agents.base_agent import BaseCourtroomAgent


class WitnessAgent(BaseCourtroomAgent):
    """
    Simulates a witness on the stand in the courtroom simulation.
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
        system_prompt = f"""You are WITNESS "{witness_name}" (ID: {witness_id}, Role: {role}) testifying under oath in the simulated matter "{case_title}".

YOUR IDENTITY & SCOPE OF KNOWLEDGE:
- Role: {role}
- Connection to Case: {connection_to_case}
- What you personally witnessed / know: {expected_testimony}
- Linked Canonical Facts: {', '.join(linked_facts) if linked_facts else 'General case background'}
- Linked Exhibits / Documents: {', '.join(linked_exhibits) if linked_exhibits else 'None'}

CANONICAL CASE RECORD:
{canonical_facts}

STRICT TESTIMONY RULES:
1. TESTIFY ONLY FROM YOUR PERSONAL KNOWLEDGE: Speak in the first person ("I saw...", "I accessed...", "According to the logs...").
2. NEVER INVENT: Do not invent phone calls, confessions, CCTV, forensic reports, or conversations not in your knowledge record.
3. ADMIT GAPS HONESTLY: If opposing counsel asks you something you cannot verify, say: "I do not have personal knowledge of that." or "The records available to me do not show that."
4. KEEP ANSWERS NATURAL & CONCISE: 1-3 sentences per question.

Return ONLY a valid JSON object:
{{
  "witness_id": "{witness_id}",
  "witness_name": "{witness_name}",
  "answer": "<your concise testimony answer>",
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
        prompt = f"""=== WITNESS STAND: {examination_type.replace('_', ' ').upper()} ===
Examining Counsel: {examining_counsel.upper()}
Question asked to you:
\"{question}\"

Prior testimony in this session:
{prior_testimony_summary if prior_testimony_summary else "Beginning of examination."}

Answer the question truthfully and strictly within your personal knowledge boundaries as the specified JSON object."""
        return self.say_json(prompt, max_tokens=600, temperature=0.25)
