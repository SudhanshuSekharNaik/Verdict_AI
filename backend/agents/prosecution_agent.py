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
        self.charge_or_dispute = charge_or_dispute

        rag_section = f"\n{rag_grounding_str}\n" if rag_grounding_str else ""

        system_prompt = f"""You are Senior Advocate / Special Public Prosecutor ({specialization}) representing the State / Filing Party in a formal judicial proceeding: "{title}".

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
{party_statements_str if party_statements_str else "Filing party submits proven statutory violation; Opposing party disputes liability and intent."}

LEVEL 4 - FRAMED ISSUES FOR DETERMINATION:
{issues_str if issues_str else "1. Actus Reus / Commission of Act 2. Mens Rea / Culpable Mental State 3. Standard of Proof"}

MATTER CHARGED BEFORE THE BENCH: {charge_or_dispute}

COURTROOM ADVOCACY & PROFESSIONALISM STANDARDS:
1. DIGNIFIED COURTROOM ETIQUETTE: Address the bench respectfully ('May it please the Hon'ble Court...', 'The State respectfully submits...'). Maintain the solemnity and analytical precision of a Senior Counsel in an Indian High Court or Sessions Court.
2. STRICT FACTUAL GROUNDING: Anchor every assertion in the canonical facts, admitted exhibits, and witness testimonies on record. Never invent fictitious witnesses or documents.
3. STATUTORY ELEMENT SCRUTINY: Systematically establish Actus Reus, Mens Rea, Causation, and Chain of Custody under Bharatiya Sakshya Adhiniyam, 2023 (BSA §63 / §104) / Indian Evidence Act.
4. SUBSTANTIVE & PERSUASIVE REASONING: Present 2 to 3 well-structured, coherent paragraphs demonstrating how circumstantial strands or direct proofs form an unbroken chain under the doctrine of *Sharad Birdhichand Sarda*.

Return ONLY a valid JSON object in this exact schema:
{{
  "speaker": "prosecution",
  "round": <round_number>,
  "argument_type": "<opening_argument|evidence_argument|intent_argument|counter_argument|closing_argument>",
  "legal_basis": "{self.counsel_profile.statutes[0] if self.counsel_profile.statutes else 'Statutory Law'}",
  "party_statement_ref": "State Submission",
  "argument": "<your 2-3 paragraph articulate and legally sound submission>",
  "evidence_references": ["Fact #1", ...],
  "strength": "<strong|moderate|weak>"
}}

DISCLAIMER: Fictional simulation for research and legal analysis."""
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
            f"=== CURRENT STAGE: ROUND {round_num} - PROSECUTION ARGUMENT ===",
            f"Objective for this round: {round_objective}",
            f"Matter Charged: {self.charge_or_dispute}",
        ]

        if prior_debate_summary:
            context_parts.append(f"Trial Record & Preceding Submissions:\n{prior_debate_summary}")

        if latest_defense_rebuttal:
            context_parts.append(
                f"Defense's preceding rebuttal:\n\"{latest_defense_rebuttal}\"\n"
                "Respond directly with statutory rigor, dismantle the defense's claims, and demonstrate proof of liability."
            )
        else:
            context_parts.append(
                f"Establish the foundational prima facie ingredients under {self.charge_or_dispute}."
            )

        if correction_feedback:
            context_parts.append(f"PROCEDURAL CORRECTION: {correction_feedback}. Ensure strict grounding.")

        context_parts.append("Deliver your single analytical turn now as the specified JSON object.")
        return self.say_json("\n\n".join(context_parts), max_tokens=700, temperature=0.35)

    def generate_opening(self, case_charge: str = "") -> Dict[str, Any]:
        target_charge = case_charge or self.charge_or_dispute
        prompt = f"""=== PROSECUTION OPENING STATEMENT ===
Matter: {target_charge}

Deliver the State's opening address to the Court with dignified eloquence and precision.
Outline:
1. The formal charge and statutory ingredients under {target_charge}.
2. The core factual narrative and timeline established by the investigation.
3. The ocular, documentary, digital, and circumstantial evidence to be introduced.

Address the Bench respectfully ('May it please the Hon'ble Court...').

Return ONLY a JSON object:
{{
  "speaker": "prosecution",
  "round": 1,
  "argument_type": "opening_statement",
  "legal_basis": "{target_charge.split('—')[0].strip()}",
  "party_statement_ref": "Prosecution Opening Address",
  "argument": "<your 2-3 paragraph dignified opening statement>",
  "evidence_references": ["Fact #1", "Fact #2"],
  "strength": "strong"
}}"""
        return self.say_json(prompt, max_tokens=600, temperature=0.3)

    def generate_examination_question(
        self,
        witness_name: str,
        witness_role: str,
        expected_testimony: str,
        question_num: int,
        prior_qa_list: List[Dict[str, str]] = [],
    ) -> Dict[str, Any]:
        qa_history = "\n".join([f"Q: {q.get('question', '')}\nA: {q.get('answer', '')}" for q in prior_qa_list])
        prompt = f"""=== PROSECUTION EXAMINATION-IN-CHIEF (ROUND {question_num}/3) ===
Witness on Stand: {witness_name} ({witness_role})
Expected Scope of Knowledge: {expected_testimony}
Question Turn: #{question_num} of 3

Prior Deposition of this witness in this session:
{qa_history if qa_history else "First question to the witness."}

Formulate EXACTLY ONE focused, non-leading question in formal courtroom English to elicit material facts from the witness's personal knowledge.

Return ONLY a JSON object:
{{
  "speaker": "prosecution",
  "stage": "examination_in_chief",
  "question_num": {question_num},
  "question": "<your single precise examination question>",
  "target_fact": "<e.g. Fact #2>",
  "intended_purpose": "<e.g. Establish chronological timeline and observations>"
}}"""
        return self.say_json(prompt, max_tokens=500, temperature=0.3)

    def generate_cross_question(
        self,
        witness_name: str,
        witness_role: str,
        prior_testimony_summary: str,
        question_num: int,
    ) -> Dict[str, Any]:
        prompt = f"""=== PROSECUTION CROSS-EXAMINATION OF DEFENSE WITNESS (ROUND {question_num}/3) ===
Witness on Stand: {witness_name} ({witness_role})
Prior Direct Testimony Given:
{prior_testimony_summary}

Question Turn: #{question_num} of 3

Formulate EXACTLY ONE sharp, incisive cross-examination question challenging the witness on bias, lack of independent verification, inconsistencies, or assumptions.

Return ONLY a JSON object:
{{
  "speaker": "prosecution",
  "stage": "cross_examination",
  "question_num": {question_num},
  "question": "<your single rigorous cross-examination question>",
  "target_point": "<e.g. Testing lack of personal verification>"
}}"""
        return self.say_json(prompt, max_tokens=500, temperature=0.3)

    def generate_closing(self, full_trial_summary: str = "", case_charge: str = "") -> Dict[str, Any]:
        target_charge = case_charge or self.charge_or_dispute
        prompt = f"""=== PROSECUTION FINAL CLOSING ARGUMENT ===
Matter: {target_charge}

Synthesize the entire evidentiary and testimonial record. Present a masterful, definitive closing summation:
1. Review the admitted exhibits and sworn depositions.
2. Demonstrate how each statutory ingredient of {target_charge} has been proved beyond reasonable doubt under Bharatiya Sakshya Adhiniyam, 2023 §104.
3. Rebut the defense's theories of reasonable doubt, establishing that the circumstantial chain is complete and points unerringly to guilt.

Address the Court with utmost professional gravity.

TRIAL RECORD & DEPOSITIONS:
{full_trial_summary if full_trial_summary else "Trial exhibits and witness testimonies on record."}

Return ONLY a JSON object:
{{
  "speaker": "prosecution",
  "argument_type": "closing_argument",
  "legal_basis": "{target_charge.split('—')[0].strip()} & BSA §104",
  "party_statement_ref": "State Closing Submission",
  "argument": "<your 2-3 paragraph comprehensive closing argument>",
  "evidence_references": ["Fact #1", "Fact #2", "P-EX-01"],
  "strength": "strong"
}}"""
        return self.say_json(prompt, max_tokens=800, temperature=0.3)
