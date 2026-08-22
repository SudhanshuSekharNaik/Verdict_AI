from typing import Any, Dict, List, Optional
from agents.base_agent import BaseCourtroomAgent
from agents import lawyer_roster


class DefenseAgent(BaseCourtroomAgent):
    """
    Defense / Opposing Counsel in the simulated courtroom proceeding.
    Defends the client by challenging the opposing party's proof under statutory standards,
    deploying RAG-retrieved doctrines, raising reasonable doubt / affirmative defenses,
    and referencing the Defense Party Position.
    """

    def __init__(
        self,
        title: str,
        facts: str,
        charge_or_dispute: str,
        facts_indexed: str = "",
        applicable_laws_str: str = "",
        party_statements_str: str = "",
        issues_str: str = "",
        counsel_id: str = "agent_01",
        rag_grounding_str: str = "",
    ):
        self.counsel_profile = lawyer_roster.get_counsel_profile(counsel_id)
        counsel_name = self.counsel_profile.name
        specialization = self.counsel_profile.specialization
        credentials = self.counsel_profile.credentials
        tone = self.counsel_profile.tone_description
        statutes_list = ", ".join(self.counsel_profile.statutes)

        rag_section = f"\n{rag_grounding_str}\n" if rag_grounding_str else ""

        system_prompt = f"""You are AGENT {self.counsel_profile.number} ({specialization}) representing the Accused / Respondent in an adversarial legal proceeding called "{title}".

SPECIALIST ROLE & DEFENSE FOCUS:
{credentials}
Advocacy Style: {tone}
Primary Governing Statutes: {statutes_list}
{rag_section}
SOURCE & EVIDENCE HIERARCHY (STRICT RULE):
LEVEL 1 - AUTHORITATIVE CASE RECORD (THE ONLY PROVEN FACTS):
{facts}

{facts_indexed if facts_indexed else ""}

LEVEL 2 - APPLICABLE STATUTES & PRECEDENTS:
{applicable_laws_str if applicable_laws_str else statutes_list}

LEVEL 3 - PARTY POSITIONS (SUBJECTIVE ADVOCACY STANCES - NOT INDEPENDENT FACTS):
{party_statements_str if party_statements_str else "Filing party alleges statutory violation; Defense disputes liability, proof, and intent."}

LEVEL 4 - ISSUES BEFORE THE COURT:
{issues_str if issues_str else "1. Essential ingredients of the dispute 2. Statutory violations 3. Standard of proof"}

MATTER BEFORE THE COURT: {charge_or_dispute}

CRITICAL RULES:
1. STRICT FACT GROUNDING: Argue ONLY from established facts. Do not invent unverified alibis, forensic receipts, or witness testimonies.
2. STATUTORY & DOCTRINAL CHALLENGE: Attack the opponent's failure to meet the statutory burden of proof (e.g. BSA §104 / standard of evidence).
3. CITATION DISCIPLINE: Cite retrieved statutes and landmark case names explicitly when relevant. Do NOT fabricate section numbers or case citations.
4. ONE TURN PER INVOCATION: Generate only one sharp, persuasive 2-3 paragraph rebuttal.

Return ONLY a valid JSON object in this exact schema:
{{
  "speaker": "defense",
  "round": <round_number>,
  "argument_type": "<rebuttal|reasonable_doubt_argument|credibility_argument|closing_argument>",
  "legal_basis": "<e.g. {self.counsel_profile.statutes[0] if self.counsel_profile.statutes else 'Indian Law'}>",
  "party_statement_ref": "Opposing Party Submission",
  "argument": "<your 2-3 paragraph rebuttal>",
  "evidence_references": ["Fact #1", ...],
  "strength": "<strong|moderate|weak>"
}}

DISCLAIMER: Fictional simulation for research and education, not real legal advice."""
        super().__init__(system_prompt)

    def generate_rebuttal(
        self,
        round_num: int,
        round_objective: str,
        prior_debate_summary: str,
        latest_prosecution_argument: str,
        correction_feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        context_parts = [
            f"=== CURRENT STAGE: ROUND {round_num} - DEFENSE'S TURN ===",
            f"Objective for this round: {round_objective}",
            f"Prosecution's preceding argument:\n\"{latest_prosecution_argument}\"",
            "Directly attack the prosecution's assertions. Highlight missing elements of BNS §303 and lack of forensic proof under BSA §104.",
        ]

        if prior_debate_summary:
            context_parts.append(f"Debate history:\n{prior_debate_summary}")

        if correction_feedback:
            context_parts.append(f"CORRECTION: {correction_feedback}. Ensure strict grounding.")

        context_parts.append("Deliver your single rebuttal now as the specified JSON object.")
    def generate_opening(self) -> Dict[str, Any]:
        prompt = """=== DEFENSE OPENING STATEMENT ===
Present the Defense opening statement to the Court. Articulate the defense theory, the presumption of innocence under BSA §104, the requirement for standard of proof beyond reasonable doubt, and the alternative innocent explanation.

Return ONLY a JSON object:
{
  "speaker": "defense",
  "round": 1,
  "argument_type": "opening_statement",
  "legal_basis": "Presumption of Innocence & BSA §104",
  "party_statement_ref": "Defense Opening",
  "argument": "<your 2-3 paragraph opening statement>",
  "evidence_references": ["Fact #3", "Fact #5"],
  "strength": "strong"
}"""
        return self.say_json(prompt, max_tokens=1000, temperature=0.3)

    def generate_cross_question(
        self,
        witness_name: str,
        witness_role: str,
        prior_testimony_summary: str,
        question_num: int,
    ) -> Dict[str, Any]:
        prompt = f"""=== DEFENSE CROSS-EXAMINATION OF PROSECUTION WITNESS ===
Witness on Stand: {witness_name} ({witness_role})
Prior Testimony Given:
{prior_testimony_summary}

Question #{question_num}
Ask EXACTLY ONE focused cross-examination question challenging the witness on lack of direct knowledge, assumptions, missing internal CCTV, or inability to establish dishonest taking.

Return ONLY a JSON object:
{{
  "speaker": "defense",
  "stage": "cross_examination",
  "question_num": {question_num},
  "question": "<your single cross-examination question>",
  "target_gap": "<e.g. Witness cannot confirm what occurred inside the locked room>"
}}"""
        return self.say_json(prompt, max_tokens=500, temperature=0.3)

    def generate_examination_question(
        self,
        witness_name: str,
        witness_role: str,
        expected_testimony: str,
        question_num: int,
        prior_qa_list: List[Dict[str, str]] = [],
    ) -> Dict[str, Any]:
        qa_history = "\n".join([f"Q: {q.get('question', '')}\nA: {q.get('answer', '')}" for q in prior_qa_list])
        prompt = f"""=== DEFENSE EXAMINATION-IN-CHIEF ===
Witness on Stand: {witness_name} ({witness_role})
Expected Scope: {expected_testimony}
Question #{question_num}

Prior Q&A:
{qa_history if qa_history else "First question."}

Ask EXACTLY ONE clear non-leading question establishing innocent explanation and lack of culpability.

Return ONLY a JSON object:
{{
  "speaker": "defense",
  "stage": "examination_in_chief",
  "question_num": {question_num},
  "question": "<your single targeted question>",
  "target_fact": "<e.g. Fact #5>"
}}"""
        return self.say_json(prompt, max_tokens=500, temperature=0.3)

    def evaluate_objection(
        self, question_text: str, examining_counsel: str
    ) -> Dict[str, Any]:
        prompt = f"""=== DEFENSE OBJECTION EVALUATOR ===
Examining Counsel: {examining_counsel}
Question Asked:
\"{question_text}\"

Evaluate if this question warrants a procedural objection (e.g. leading during examination-in-chief, assumes facts not in evidence, hearsay, speculative, or argumentative).

Return ONLY a JSON object:
{{
  "raise_objection": <true|false>,
  "ground": "<leading|relevance|speculation|hearsay|assumes_facts|argumentative>",
  "objection_statement": "<e.g. Objection My Lord, counsel is leading the witness in chief.>"
}}"""
        return self.say_json(prompt, max_tokens=300, temperature=0.2)

    def generate_closing(
        self, full_trial_summary: str = "", latest_prosecution_arg: str = ""
    ) -> Dict[str, Any]:
        prompt = f"""=== DEFENSE FINAL CLOSING ARGUMENT ===
Summarize the defense position. Directly rebut prosecution points, highlight reasonable doubts, lack of direct eyewitnesses or forensic traces, and invoke the presumption of innocence under BSA §104.

PROSECUTION CLOSING ARGUMENT:
{latest_prosecution_arg if latest_prosecution_arg else "Prosecution argues circumstantial chain."}

TRIAL RECORD SUMMARY:
{full_trial_summary if full_trial_summary else "Full deposition record."}

Return ONLY a JSON object:
{{
  "speaker": "defense",
  "argument_type": "closing_argument",
  "legal_basis": "Presumption of Innocence & BSA §104",
  "party_statement_ref": "Defense Position",
  "argument": "<your 2-3 paragraph analytical closing argument>",
  "evidence_references": ["Fact #5", "Fact #7", "D-EX-01"],
  "strength": "strong"
}}"""
        return self.say_json(prompt, max_tokens=1200, temperature=0.3)
