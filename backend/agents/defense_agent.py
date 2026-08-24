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
        self.charge_or_dispute = charge_or_dispute

        rag_section = f"\n{rag_grounding_str}\n" if rag_grounding_str else ""

        system_prompt = f"""You are Senior Defense Advocate ({specialization}) representing the Accused / Respondent in a formal judicial proceeding: "{title}".

ADVOCACY PROFILE & CREDENTIALS:
{credentials}
Style & Demeanor: {tone}
Primary Governing Legal Framework: {statutes_list}
{rag_section}
CASE DOSSIER & RECORD:
LEVEL 1 - CANONICAL PROVEN FACTS (AUTHORITATIVE RECORD):
{facts}

{facts_indexed if facts_indexed else ""}

LEVEL 2 - APPLICABLE STATUTES & PRECEDENTS:
{applicable_laws_str if applicable_laws_str else statutes_list}

LEVEL 3 - PARTY POSITIONS & ADVOCACY THEORIES:
{party_statements_str if party_statements_str else "Filing party alleges statutory violation; Defense disputes liability, proof, and intent."}

LEVEL 4 - FRAMED ISSUES FOR DETERMINATION:
{issues_str if issues_str else "1. Actus Reus / Commission of Act 2. Mens Rea / Culpable Mental State 3. Standard of Proof & Reasonable Doubt"}

MATTER CHARGED BEFORE THE BENCH: {charge_or_dispute}

COURTROOM ADVOCACY & PROFESSIONALISM STANDARDS:
1. DIGNIFIED COURTROOM ETIQUETTE: Address the bench respectfully ('With utmost respect to this Hon'ble Court...', 'The Defense respectfully submits...'). Maintain the composure, sharp analytical rigor, and eloquence of a Senior Criminal Defense Advocate in an Indian High Court or Sessions Court.
2. PRESUMPTION OF INNOCENCE & STATUTORY BURDEN: Rigorously enforce Section 104 of Bharatiya Sakshya Adhiniyam, 2023 (BSA §104 / Indian Evidence Act §101). The burden rests wholly on the Prosecution; the defense need only establish reasonable doubt or an equally probable innocent explanation.
3. SCRUTINIZE EVIDENTIARY GAPS: Attack missing links in the circumstantial chain, absence of definitive forensic DNA/fingerprint matches, broken custody logs, and speculative leaps.
4. SUBSTANTIVE & PERSUASIVE SUBMISSIONS: Formulate 2 to 3 logically coherent paragraphs demonstrating why the State has failed to meet the rigorous standard of proof beyond reasonable doubt.

Return ONLY a valid JSON object in this exact schema:
{{
  "speaker": "defense",
  "round": <round_number>,
  "argument_type": "<rebuttal|reasonable_doubt_argument|credibility_argument|closing_argument>",
  "legal_basis": "{self.counsel_profile.statutes[0] if self.counsel_profile.statutes else 'Statutory Law'}",
  "party_statement_ref": "Defense Position Submission",
  "argument": "<your 2-3 paragraph sharp, articulate, and legally grounded defense submission>",
  "evidence_references": ["Fact #1", ...],
  "strength": "<strong|moderate|weak>"
}}

DISCLAIMER: Fictional simulation for research and legal analysis."""
        super().__init__(system_prompt)

    def generate_rebuttal(
        self,
        round_num: int,
        round_objective: str,
        prior_debate_summary: str,
        latest_prosecution_argument: str,
        correction_feedback: Optional[str] = None,
        case_charge: str = "",
    ) -> Dict[str, Any]:
        target_charge = case_charge or self.charge_or_dispute
        context_parts = [
            f"=== CURRENT STAGE: ROUND {round_num} - DEFENSE REBUTTAL ===",
            f"Objective for this round: {round_objective}",
            f"Matter Charged: {target_charge}",
            f"Prosecution's preceding submission:\n\"{latest_prosecution_argument}\"",
            f"Directly attack the prosecution's assertions. Highlight missing statutory elements under {target_charge} and lack of forensic certainty under BSA §104.",
        ]

        if prior_debate_summary:
            context_parts.append(f"Trial Record & Preceding Arguments:\n{prior_debate_summary}")

        if correction_feedback:
            context_parts.append(f"PROCEDURAL CORRECTION: {correction_feedback}. Ensure strict grounding.")

        context_parts.append("Deliver your single rebuttal turn now as the specified JSON object.")
        return self.say_json("\n\n".join(context_parts), max_tokens=1200, temperature=0.35)

    def generate_opening(self, case_charge: str = "") -> Dict[str, Any]:
        target_charge = case_charge or self.charge_or_dispute
        prompt = f"""=== DEFENSE OPENING STATEMENT ===
Matter: {target_charge}

Deliver the Defense opening address to the Court with dignified eloquence and precision.
Outline:
1. The foundational presumption of innocence under Indian jurisprudence and BSA §104.
2. The alternative innocent explanation, lack of direct culpability, or absence of mens rea.
3. The fatal gaps in the State's circumstantial allegations that will fail the standard of proof beyond reasonable doubt.

Address the Bench respectfully ('With utmost respect to this Hon'ble Court...').

Return ONLY a JSON object:
{{
  "speaker": "defense",
  "round": 1,
  "argument_type": "opening_statement",
  "legal_basis": "Presumption of Innocence & BSA §104",
  "party_statement_ref": "Defense Opening Address",
  "argument": "<your 2-3 paragraph articulate and dignified opening statement>",
  "evidence_references": ["Fact #3", "Fact #5"],
  "strength": "strong"
}}"""
        return self.say_json(prompt, max_tokens=1100, temperature=0.3)

    def generate_cross_question(
        self,
        witness_name: str,
        witness_role: str,
        prior_testimony_summary: str,
        question_num: int,
    ) -> Dict[str, Any]:
        prompt = f"""=== DEFENSE CROSS-EXAMINATION OF PROSECUTION WITNESS (ROUND {question_num}/3) ===
Witness on Stand: {witness_name} ({witness_role})
Prior Direct Testimony Given:
{prior_testimony_summary}

Question Turn: #{question_num} of 3

Formulate EXACTLY ONE focused, incisive cross-examination question in formal courtroom English challenging the witness on lack of direct ocular certainty, assumptions, gaps in observation, or alternative innocent possibilities.

Return ONLY a JSON object:
{{
  "speaker": "defense",
  "stage": "cross_examination",
  "question_num": {question_num},
  "question": "<your single rigorous cross-examination question>",
  "target_gap": "<e.g. Witness cannot confirm what transpired in the unobserved interval>"
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
        prompt = f"""=== DEFENSE EXAMINATION-IN-CHIEF (ROUND {question_num}/3) ===
Witness on Stand: {witness_name} ({witness_role})
Expected Scope of Knowledge: {expected_testimony}
Question Turn: #{question_num} of 3

Prior Deposition of this witness in this session:
{qa_history if qa_history else "First question to the witness."}

Formulate EXACTLY ONE clear, non-leading question in formal courtroom English to elicit facts supporting the defense's position and establishing lack of culpability.

Return ONLY a JSON object:
{{
  "speaker": "defense",
  "stage": "examination_in_chief",
  "question_num": {question_num},
  "question": "<your single precise examination question>",
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
        self, full_trial_summary: str = "", latest_prosecution_arg: str = "", case_charge: str = ""
    ) -> Dict[str, Any]:
        target_charge = case_charge or self.charge_or_dispute
        prompt = f"""=== DEFENSE FINAL CLOSING ARGUMENT ===
Matter: {target_charge}

Synthesize the entire trial record and deliver a masterclass in defense closing advocacy:
1. Rebut the Prosecution's closing arguments directly point-by-point.
2. Highlight the irreducible reasonable doubts, the absence of conclusive forensic links, and the plausibility of the defense theory.
3. Invoke the sacred presumption of innocence and Section 104 of Bharatiya Sakshya Adhiniyam, 2023, asking the Court for an honorable discharge / acquittal.

Address the Court with utmost professional gravity and eloquence.

PROSECUTION CLOSING ARGUMENT:
{latest_prosecution_arg if latest_prosecution_arg else "Prosecution argues circumstantial chain."}

TRIAL RECORD & DEPOSITIONS:
{full_trial_summary if full_trial_summary else "Full trial record and depositions."}

Return ONLY a JSON object:
{{
  "speaker": "defense",
  "argument_type": "closing_argument",
  "legal_basis": "Presumption of Innocence & BSA §104",
  "party_statement_ref": "Defense Closing Submission",
  "argument": "<your 2-3 paragraph analytical and persuasive closing argument>",
  "evidence_references": ["Fact #5", "Fact #7", "D-EX-01"],
  "strength": "strong"
}}"""
        return self.say_json(prompt, max_tokens=1300, temperature=0.3)
