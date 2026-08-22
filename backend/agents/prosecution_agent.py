from typing import Any, Dict, List, Optional
from agents.base_agent import BaseCourtroomAgent
from agents import lawyer_roster


class ProsecutionAgent(BaseCourtroomAgent):
    """
    Prosecution / Filing Counsel in the simulated courtroom proceeding.
    Advocates for the charge / claim by linking statutory elements and RAG-retrieved legal doctrine
    to the authoritative Case Record and Party Submissions.
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
        counsel_id: str = "agent_02",
        rag_grounding_str: str = "",
    ):
        self.counsel_profile = lawyer_roster.get_counsel_profile(counsel_id)
        counsel_name = self.counsel_profile.name
        specialization = self.counsel_profile.specialization
        credentials = self.counsel_profile.credentials
        tone = self.counsel_profile.tone_description
        statutes_list = ", ".join(self.counsel_profile.statutes)

        rag_section = f"\n{rag_grounding_str}\n" if rag_grounding_str else ""

        system_prompt = f"""You are AGENT {self.counsel_profile.number} ({specialization}) representing the State / Filing Party in an adversarial legal proceeding called "{title}".

SPECIALIST ROLE & ADVOCACY FOCUS:
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
{party_statements_str if party_statements_str else "Filing party submits intentional statutory violation; Opposing party disputes liability and intent."}

LEVEL 4 - ISSUES BEFORE THE COURT:
{issues_str if issues_str else "1. Essential ingredients of the dispute 2. Statutory violations 3. Standard of proof"}

MATTER BEFORE THE COURT: {charge_or_dispute}

CRITICAL RULES:
1. STRICT FACT GROUNDING: Argue ONLY from established facts. Do not invent unverified witnesses, forensic logs, or admissions.
2. CITATION DISCIPLINE: Cite retrieved statutes and landmark case names explicitly when relevant. Do NOT fabricate section numbers or case citations.
3. DISTINGUISH ALLEGATIONS FROM FACTS: Treat party statements as advocacy positions, not verified facts.
4. ONE TURN PER INVOCATION: Generate only one sharp, persuasive 2-3 paragraph argument.

Return ONLY a valid JSON object in this exact schema:
{{
  "speaker": "prosecution",
  "round": <round_number>,
  "argument_type": "<opening_argument|evidence_argument|intent_argument|counter_argument|closing_argument>",
  "legal_basis": "<e.g. {self.counsel_profile.statutes[0] if self.counsel_profile.statutes else 'Indian Law'}>",
  "party_statement_ref": "Filing Party Submission",
  "argument": "<your 2-3 paragraph argument>",
  "evidence_references": ["Fact #1", ...],
  "strength": "<strong|moderate|weak>"
}}

DISCLAIMER: Fictional simulation for research and education, not real legal advice."""
        super().__init__(system_prompt)

    def generate_argument(
        self,
        round_num: int,
        round_objective: str,
        prior_debate_summary: str = "",
        latest_defense_rebuttal: Optional[str] = None,
        correction_feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        context_parts = [
            f"=== CURRENT STAGE: ROUND {round_num} - PROSECUTION'S TURN ===",
            f"Objective for this round: {round_objective}",
        ]

        if prior_debate_summary:
            context_parts.append(f"Debate history so far:\n{prior_debate_summary}")

        if latest_defense_rebuttal:
            context_parts.append(
                f"Defense's latest rebuttal:\n\"{latest_defense_rebuttal}\"\n"
                "Respond directly to defense's points and advance your statutory elements."
            )
        else:
            context_parts.append(
                "This is Round 1 Opening. Present the foundational prima facie case under BNS §303."
            )

        if correction_feedback:
            context_parts.append(f"CORRECTION: {correction_feedback}. Ensure strict grounding.")

        context_parts.append("Deliver your single turn now as the specified JSON object.")
        return self.say_json("\n\n".join(context_parts), max_tokens=1200, temperature=0.35)

    def generate_opening(self) -> Dict[str, Any]:
        prompt = """=== PROSECUTION OPENING STATEMENT ===
Present the State's opening statement to the Court. Detail the charge under BNS §303, the foundational facts to be established through evidence and witnesses, and the legal elements to be proved.

Return ONLY a JSON object:
{
  "speaker": "prosecution",
  "round": 1,
  "argument_type": "opening_statement",
  "legal_basis": "BNS §303 — Theft",
  "party_statement_ref": "Prosecution Statement",
  "argument": "<your 2-3 paragraph opening statement>",
  "evidence_references": ["Fact #1", "Fact #2"],
  "strength": "strong"
}"""
        return self.say_json(prompt, max_tokens=1000, temperature=0.3)

    def generate_examination_question(
        self,
        witness_name: str,
        witness_role: str,
        expected_testimony: str,
        question_num: int,
        prior_qa_list: List[Dict[str, str]] = [],
    ) -> Dict[str, Any]:
        qa_history = "\n".join([f"Q: {q.get('question', '')}\nA: {q.get('answer', '')}" for q in prior_qa_list])
        prompt = f"""=== PROSECUTION EXAMINATION-IN-CHIEF ===
Witness on Stand: {witness_name} ({witness_role})
Expected Scope: {expected_testimony}
Question #{question_num}

Prior Q&A with this witness:
{qa_history if qa_history else "First question."}

Ask EXACTLY ONE clear, non-leading question to elicit facts establishing your case.

Return ONLY a JSON object:
{{
  "speaker": "prosecution",
  "stage": "examination_in_chief",
  "question_num": {question_num},
  "question": "<your single targeted question>",
  "target_fact": "<e.g. Fact #2>",
  "intended_purpose": "<e.g. Establish entry timestamp>"
}}"""
        return self.say_json(prompt, max_tokens=500, temperature=0.3)

    def generate_cross_question(
        self,
        witness_name: str,
        witness_role: str,
        prior_testimony_summary: str,
        question_num: int,
    ) -> Dict[str, Any]:
        prompt = f"""=== PROSECUTION CROSS-EXAMINATION OF DEFENSE WITNESS ===
Witness: {witness_name} ({witness_role})
Prior Testimony Given:
{prior_testimony_summary}

Question #{question_num}
Ask EXACTLY ONE sharp cross-examination question probing bias, lack of personal verification, or gaps.

Return ONLY a JSON object:
{{
  "speaker": "prosecution",
  "stage": "cross_examination",
  "question_num": {question_num},
  "question": "<your single cross-examination question>",
  "target_point": "<e.g. Challenging independent verification>"
}}"""
        return self.say_json(prompt, max_tokens=500, temperature=0.3)

    def generate_closing(self, full_trial_summary: str = "") -> Dict[str, Any]:
        prompt = f"""=== PROSECUTION FINAL CLOSING ARGUMENT ===
Summarize the entire trial record. Explain why the evidence admitted, witness testimony, and statutory provisions establish guilt beyond reasonable doubt under the applicable Bharatiya Nyaya Sanhita provision.

TRIAL RECORD SUMMARY:
{full_trial_summary if full_trial_summary else "Trial arguments and depositions recorded."}

Return ONLY a JSON object:
{{
  "speaker": "prosecution",
  "argument_type": "closing_argument",
  "legal_basis": "BNS & BSA §104",
  "party_statement_ref": "Prosecution Position",
  "argument": "<your 2-3 paragraph forceful closing argument>",
  "evidence_references": ["Fact #1", "Fact #2", "Fact #6"],
  "strength": "strong"
}}"""
        return self.say_json(prompt, max_tokens=1200, temperature=0.3)
