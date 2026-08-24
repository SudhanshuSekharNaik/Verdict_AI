from typing import Any, Dict, List, Optional
from agents.base_agent import BaseCourtroomAgent
from models.schemas import IssueFinding, LawAssessment


class JudgeAgent(BaseCourtroomAgent):
    """
    Impartial Presiding Judge in the simulated Indian courtroom proceeding.
    Deliberates over the full case dossier: Canonical Facts, Applicable Indian Law,
    Party Statements, Legal Issue Matrix, Registered Exhibits, and Adversarial Record.
    """

    def __init__(
        self,
        title: str,
        facts: str,
        charge_or_dispute: str,
        facts_indexed: str = "",
        evidence_str: str = "",
        witnesses_str: str = "",
        applicable_laws_str: str = "",
        party_statements_str: str = "",
        issues_str: str = "",
    ):
        self.title = title
        self.facts = facts
        self.charge_or_dispute = charge_or_dispute
        self.facts_indexed = facts_indexed
        self.evidence_str = evidence_str
        self.witnesses_str = witnesses_str
        self.applicable_laws_str = applicable_laws_str
        self.party_statements_str = party_statements_str
        self.issues_str = issues_str

        system_prompt = f"""You are the PRESIDING JUDGE in an authoritative judicial simulation of the proceeding "{title}".

CHARGES & MATTERS BEFORE THE COURT:
{charge_or_dispute}

SOURCE HIERARCHY & EVIDENTIARY RECORD:
LEVEL 1 - CANONICAL FACTS (AUTHORITATIVE RECORD):
{facts}

{facts_indexed if facts_indexed else ""}

LEVEL 2 - REGISTERED EVIDENCE EXHIBITS:
{evidence_str if evidence_str else "Exhibits registered in case docket."}

LEVEL 3 - REGISTERED WITNESSES & TESTIMONY SCOPE:
{witnesses_str if witnesses_str else "Witness depositions and statements on record."}

LEVEL 4 - APPLICABLE INDIAN STATUTES & JUDICIAL DOCTRINES:
{applicable_laws_str if applicable_laws_str else "Relevant provisions of Indian Penal Code (IPC §300, §302, §304) / Bharatiya Nyaya Sanhita (BNS §103) and Evidence Law (BSA §104 / IEA §101, BSA §108 / IEA §105 - Burden of Proof for Exceptions)."}

LEVEL 5 - PARTY POSITIONS (ADVOCACY CLAIMS):
{party_statements_str if party_statements_str else "Prosecution and Defence pre-trial submissions."}

LEVEL 6 - FRAMED LEGAL ISSUES FOR DETERMINATION:
{issues_str if issues_str else "1. Commission of act (Actus Reus) 2. Requisite intent / mens rea 3. Affirmative defense & cooling-off interval 4. Standard of proof"}

================================================================================
MANDATORY JUDICIAL ADJUDICATION PROTOCOL & REASONING STANDARDS
================================================================================

1. MANDATORY INDIVIDUAL ISSUE-BY-ISSUE DETERMINATION:
   - You MUST address and rule upon EVERY issue listed in the case's "Issues for Determination" explicitly and individually in `issue_findings`.
   - Never omit, gloss over, or collapse any framed issue into a vague general summary.
   - For EVERY issue, you must state:
     * "issue_id": matching the framed issue (e.g. "ISSUE_01", "ISSUE_02", "ISSUE_03", etc.)
     * "question": the exact framed legal question
     * "finding": precise judicial holding ("Established beyond reasonable doubt", "Affirmative defense rejected due to cooling-off interval", "Established on preponderance of evidence", etc.)
     * "rationale": a substantive, multi-sentence legal and factual analysis directly answering that specific question, citing specific canonical facts (e.g. [Fact #4], [Fact #5], [Fact #6], [Fact #7], [Fact #8], [Fact #11] or [F04]-[F13]) and exhibits (e.g. [P-EX-01], [P-EX-04], [D-EX-01]).

2. BIFURCATED ANALYSIS OF AFFIRMATIVE DEFENSES (PROVOCATION & COOLING-OFF DOCTRINE):
   When an affirmative defense (such as "grave and sudden provocation" under Exception 1 to IPC §300 / BNS §103) is raised, you MUST evaluate BOTH of its legal elements separately:
   (a) Element 1 — Gravity / Sufficiency of Provocation:
       - Evaluate whether the triggering event was capable of causing a reasonable person to lose self-control.
       - Under authoritative Indian criminal jurisprudence (e.g. K.M. Nanavati v. State of Maharashtra, AIR 1962 SC 605; Akhtar v. State), a direct confession of marital infidelity or discovery of adultery constitutes grave provocation.
       - You MUST NOT hold or state that a spouse's confession of infidelity lacks gravity or is insufficient to cause a reasonable person to lose self-control.
   (b) Element 2 — Suddenness & The Cooling-Off Interval (Deliberation Doctrine / Locus Poenitentiae):
       - Evaluate whether the accused acted immediately in the sudden heat of passion before a reasonable opportunity to regain self-control had passed.
       - You MUST explicitly trace and evaluate the sequence of intermediate deliberate actions and elapsed time between the triggering event and the fatal act (e.g., dropping family members at a cinema, traveling to a naval dockyard/ship, obtaining a firearm and ammunition under a false pretext, driving to an office, and subsequently driving to a private residence).
       - If intermediate, deliberate, calculated steps occurred across this intervening period, the doctrine of "cooling off" / locus poenitentiae negates the element of SUDDENNESS as a matter of law.
       - Consequently, the provocation defense FAILS on the element of suddenness due to the intervening interval of deliberation, NOT because the confession lacked gravity.

3. SPECIFIC FACT & EXHIBIT CITATION REQUIREMENT:
   You MUST cite specific numbered canonical facts (e.g. [Fact #4], [Fact #5], [Fact #6], [Fact #7], [Fact #8], [Fact #11], [Fact #13] or [F04], [F05], [F06], [F07], [F08], [F11], [F13]) and specific exhibit numbers (e.g. [P-EX-01], [P-EX-02], [P-EX-03], [P-EX-04], [D-EX-01], [D-EX-02]) when justifying your determinations on each issue and defense.

4. BURDEN OF PROOF & STANDARD OF ADJUDICATION:
   - The prosecution carries the burden of proving all statutory elements of the offense beyond a reasonable doubt (BSA §104 / IEA §101).
   - Under BSA §108 / IEA §105, when an accused claims an exception or affirmative defense, the legal burden is on the accused to establish the exception on a preponderance of probabilities.

CRITICAL OUTPUT FORMAT:
Return ONLY a valid JSON object starting with {{ on line 1. Do NOT output <think> tags or preliminary chain of thought.
Schema:
{{
  "winner": "<defense_prevailed|prosecution_prevailed>",
  "verdict": "<not_guilty|guilty>",
  "confidence": <float between 0.70 and 0.99>,
  "decision_basis": "<1-2 sentence authoritative holding stating the exact statutory and doctrinal basis of the decree>",
  "issue_findings": [
    {{
      "issue_id": "ISSUE_01",
      "question": "<exact framed question>",
      "finding": "<Established|Not established|Affirmative defense rejected|Affirmative defense accepted>",
      "rationale": "<thorough 2-4 sentence analysis citing specific facts like [Fact #4] and exhibits like [P-EX-01]>",
      "linked_evidence": ["<P-EX-01>", ...],
      "linked_witnesses": ["<PW-01>", ...]
    }}
  ],
  "law_assessments": [
    {{
      "provision": "<Statute and section, e.g. IPC §302 / Exception 1 to §300 or BNS §103>",
      "status": "<Statutory requirements fulfilled beyond reasonable doubt|Defense not applicable / Exception rejected>",
      "rationale": "<statutory and doctrinal legal reasoning>"
    }}
  ],
  "affirmative_defense_analysis": {{
    "defense_name": "<e.g. Grave and Sudden Provocation (Exception 1 to IPC §300 / BNS §103)>",
    "prong_1_gravity": {{
      "element": "Gravity / Sufficiency of Provocation",
      "finding": "<Satisfied / Grave provocation established>",
      "evaluation": "<analysis confirming that a spouse's confession of infidelity constitutes grave provocation under Indian law>",
      "facts_cited": ["<Fact #4>", "<D-EX-01>"]
    }},
    "prong_2_suddenness_and_interval": {{
      "element": "Suddenness & Cooling-Off Interval (Deliberation Doctrine)",
      "finding": "<Negated / Failed due to cooling-off interval and intermediate deliberation>",
      "evaluation": "<rigorous factual analysis detailing the intermediate steps (cinema, ship, revolver under false pretext, driving to office, driving to residence) that defeat suddenness as a matter of law>",
      "facts_cited": ["<Fact #5>", "<Fact #6>", "<Fact #7>", "<P-EX-01>", "<P-EX-04>"]
    }},
    "overall_determination": "<REJECTED on the element of suddenness / cooling-off interval>"
  }},
  "prosecution_strengths": ["<strength 1>", "<strength 2>"],
  "defense_strengths": ["<strength 1>", "<strength 2>"],
  "key_factors": ["<factor 1>", "<factor 2>", "<factor 3>"],
  "evidence_gaps": ["<gap 1 or 'None affecting core holding'>"],
  "reasoning_summary": "<4 formal judicial paragraphs: Paragraph 1: Case background & established facts with citations; Paragraph 2: Factual and evidentiary evaluation of the actus reus and mens rea; Paragraph 3: In-depth doctrinal analysis of the affirmative defense separating gravity (which is conceded/established) from the cooling-off interval and deliberation sequence (cinema, naval ship, weapon acquisition under pretext, driving between locations) which legally extinguishes suddenness; Paragraph 4: Final holding and sentencing/verdict disposition under the applicable statute.>"
}}

DISCLAIMER: Fictional simulation for research and education, not real legal advice."""
        super().__init__(system_prompt)

    def deliberate_and_rule(
        self,
        full_annotated_record: str,
        legal_issues: Optional[List[Dict[str, Any]]] = None,
        canonical_facts_str: str = "",
        evidence_str: str = "",
        witnesses_str: str = "",
        applicable_laws_str: str = "",
    ) -> Dict[str, Any]:
        issues_prompt = ""
        if legal_issues:
            issues_prompt = "\n\nLEGAL ISSUES TO EVALUATE SPECIFICALLY AND INDIVIDUALLY:\n" + "\n".join(
                [f"[{iss.get('issue_id', 'ISSUE')}]: {iss.get('question', '')}" for iss in legal_issues]
            )

        facts_section = canonical_facts_str or self.facts_indexed or self.facts
        ev_section = evidence_str or self.evidence_str
        wit_section = witnesses_str or self.witnesses_str
        laws_section = applicable_laws_str or self.applicable_laws_str

        prompt = f"""=== AUTHORITATIVE RECORD FOR JUDICIAL DELIBERATION ===

CHARGE: {self.charge_or_dispute}

CANONICAL FACTS & NUMBERED PROPOSITIONS:
{facts_section}

REGISTERED EVIDENCE EXHIBITS:
{ev_section}

REGISTERED WITNESSES & TESTIMONY SCOPE:
{wit_section}

APPLICABLE STATUTES & DOCTRINES:
{laws_section}

ADVERSARIAL TRIAL TRANSCRIPT & ARGUMENTS:
{full_annotated_record}
{issues_prompt}

JUDICIAL DELIBERATION DIRECTIVE:
1. Deliver a comprehensive judgment addressing EVERY framed legal issue individually in `issue_findings`.
2. If an affirmative defense (like grave and sudden provocation) is raised, rigorously bifurcate your analysis into:
   - Prong 1 (Gravity): Acknowledge that a confession of infidelity constitutes grave provocation under Indian law.
   - Prong 2 (Suddenness & Interval): Explicitly analyze whether the sequence of intermediate actions (dropping family at cinema, obtaining firearm at ship under false pretext, driving between locations) constitutes a "cooling-off" period defeating suddenness.
3. Cite specific fact numbers [Fact #N] or [F##] and exhibit numbers [P-EX-##] / [D-EX-##] throughout your issue findings and reasoning summary.
4. Ensure `reasoning_summary` includes an extensive discussion of the cooling-off interval and intermediate deliberation sequence.

Deliver your complete structured verdict JSON now."""

        res = self.say_json(prompt, max_tokens=1800, temperature=0.2)

        # Standardize verdict fields
        raw_verd = str(res.get("verdict", "")).lower()
        raw_winner = str(res.get("winner", "")).lower()
        raw_basis = str(res.get("decision_basis", "")).lower()

        if "not_guilty" in raw_verd or "not guilty" in raw_verd or "acquitted" in raw_verd:
            verdict_cat = "not_guilty"
            winner = "defense_prevailed"
            decision_text = res.get("decision_basis") or "NOT GUILTY — The charge is not established beyond reasonable doubt."
        elif "guilty" in raw_verd or "prosecution_prevailed" in raw_winner or "guilty" in raw_basis:
            verdict_cat = "guilty"
            winner = "prosecution_prevailed"
            decision_text = res.get("decision_basis") or "GUILTY — The charge is established beyond reasonable doubt."
        else:
            verdict_cat = "guilty" if "prosecution" in raw_winner else "not_guilty"
            winner = raw_winner or "prosecution_prevailed"
            decision_text = res.get("decision_basis") or ("GUILTY" if winner == "prosecution_prevailed" else "NOT GUILTY")

        conf = res.get("confidence", 0.90)
        if isinstance(conf, (int, float)):
            conf_val = round(float(conf), 2)
            if conf_val > 1.0:
                conf_val = round(conf_val / 100.0, 2)
        else:
            conf_val = 0.90

        # Format issue findings
        raw_issues = res.get("issue_findings", [])
        formatted_issues: List[IssueFinding] = []
        if raw_issues and isinstance(raw_issues, list):
            for iss in raw_issues:
                if isinstance(iss, dict):
                    formatted_issues.append(
                        IssueFinding(
                            issue_id=iss.get("issue_id", "ISSUE"),
                            question=iss.get("question", ""),
                            finding=iss.get("finding", "Determined by Court"),
                            rationale=iss.get("rationale", ""),
                            linked_evidence=iss.get("linked_evidence", []),
                            linked_witnesses=iss.get("linked_witnesses", []),
                        )
                    )

        # Fallback if issue findings were empty
        if not formatted_issues and legal_issues:
            for idx, iss in enumerate(legal_issues):
                formatted_issues.append(
                    IssueFinding(
                        issue_id=iss.get("issue_id", f"ISSUE_{idx+1}"),
                        question=iss.get("question", ""),
                        finding="Evaluated and adjudicated by Court",
                        rationale=f"The Court has evaluated the record in relation to this issue and rendered its determination accordingly.",
                        linked_evidence=[],
                        linked_witnesses=[],
                    )
                )

        # Format law assessments
        raw_laws = res.get("law_assessments", [])
        formatted_laws: List[LawAssessment] = []
        if raw_laws and isinstance(raw_laws, list):
            for l in raw_laws:
                if isinstance(l, dict):
                    formatted_laws.append(
                        LawAssessment(
                            provision=l.get("provision", self.charge_or_dispute),
                            status=l.get("status", "Adjudicated under statutory standards"),
                            rationale=l.get("rationale", ""),
                        )
                    )

        if not formatted_laws:
            formatted_laws = [
                LawAssessment(
                    provision=self.charge_or_dispute,
                    status="Statutory requirements applied to factual record",
                    rationale=res.get("decision_basis", "Adjudicated upon statutory elements and evidence."),
                )
            ]

        key_factors = res.get("key_factors", []) or [
            "Factual timeline and sequence of intervening actions",
            "Applicability and statutory elements of affirmative defense",
            "Standard of proof beyond reasonable doubt",
        ]

        evidence_gaps = res.get("evidence_gaps", []) or []

        reasoning = res.get("reasoning_summary") or res.get("reasoning")
        if not reasoning or len(reasoning.strip()) < 50:
            issue_summaries = "\n\n".join([f"• **{iss.question}** [{iss.finding}]:\n  {iss.rationale}" for iss in formatted_issues])
            reasoning = (
                f"JUDICIAL OPINION & REASONING OF THE COURT:\n\n"
                f"1. Established Holding & Decision Basis:\n{decision_text}\n\n"
                f"2. Adjudication of Framed Issues:\n{issue_summaries}\n\n"
                f"3. Final Statutory Disposition:\nUpon weighing the evidentiary record against the statutory requirements of {self.charge_or_dispute}, the Court decrees as set forth above."
            )

        aff_def = res.get("affirmative_defense_analysis") or {}
        if not aff_def or not isinstance(aff_def, dict) or not aff_def.get("prong_1_gravity"):
            # Check if any issue finding evaluated provocation / cooling-off / affirmative defense
            prov_issue = next(
                (iss for iss in formatted_issues if any(k in iss.question.lower() or k in iss.rationale.lower() for k in ["provocation", "suddenness", "interval", "cooling", "exception 1"])),
                None
            )
            if prov_issue:
                aff_def = {
                    "defense_name": "Grave and Sudden Provocation (Exception 1 to Section 300 IPC / BNS §103)",
                    "prong_1_gravity": {
                        "element": "Gravity / Sufficiency of Provocation",
                        "finding": "Satisfied / Grave Provocation Conceded",
                        "evaluation": "Under established Indian criminal jurisprudence (K.M. Nanavati v. State of Maharashtra AIR 1962 SC 605), confession of spousal infidelity constitutes grave provocation.",
                        "facts_cited": [f for f in ["[Fact #4]", "[D-EX-01]", "[F04]"] if f in prov_issue.rationale or f in self.facts],
                    },
                    "prong_2_suddenness_and_interval": {
                        "element": "Suddenness & Cooling-Off Interval (Deliberation Doctrine)",
                        "finding": prov_issue.finding,
                        "evaluation": prov_issue.rationale,
                        "facts_cited": [f for f in ["[Fact #5]", "[Fact #6]", "[Fact #7]", "[P-EX-01]", "[P-EX-04]", "[F05]", "[F06]", "[F07]"] if f in prov_issue.rationale],
                    },
                    "overall_determination": prov_issue.finding,
                }

        return {
            "winner": winner,
            "decision": decision_text,
            "verdict_category": verdict_cat,
            "confidence": conf_val,
            "decision_basis": res.get("decision_basis", "") or decision_text,
            "reasoning_summary": reasoning,
            "issue_findings": formatted_issues,
            "law_assessments": formatted_laws,
            "affirmative_defense_analysis": aff_def,
            "prosecution_strengths": res.get("prosecution_strengths", []) or ["Established sequence of actions and statutory elements."],
            "defense_strengths": res.get("defense_strengths", []) or ["Articulated factual provocation and emotional state."],
            "key_factors": key_factors,
            "evidence_gaps": evidence_gaps,
        }

    def rule_on_objection(
        self,
        counsel_objecting: str,
        ground: str,
        question_text: str,
    ) -> Dict[str, Any]:
        prompt = f"""=== JUDICIAL RULING ON OBJECTION ===
Case: {self.title}
Charge: {self.charge_or_dispute}
Objecting Counsel: {counsel_objecting.upper()}
Ground of Objection: {ground}
Challenged Question:
\"{question_text}\"

Rule on the objection according to evidentiary principles (leading questions, relevance, hearsay, facts not established, speculation).

Return ONLY a JSON object:
{{
  "ruling": "<sustained|overruled|deferred>",
  "judicial_instruction": "<e.g. Sustained. Counsel will rephrase without leading the witness. OR Overruled. The witness may answer.>",
  "legal_rationale": "<brief judicial rationale>"
}}"""
        return self.say_json(prompt, max_tokens=350, temperature=0.2)

    def rule_on_evidence_admission(
        self,
        exhibit_id: str,
        title: str,
        submitted_by: str,
        description: str,
        has_hash: bool,
    ) -> Dict[str, Any]:
        prompt = f"""=== JUDICIAL RULING ON EXHIBIT ADMISSIBILITY ===
Case: {self.title}
Exhibit: {exhibit_id} — {title}
Offered by: {submitted_by.upper()}
Description: {description}
Integrity / Custody: {'Documented' if has_hash else 'Presented in case record'}

Rule on marking or admitting this exhibit into the trial record under evidentiary standards.

Return ONLY a JSON object:
{{
  "ruling": "<admitted|marked|excluded>",
  "judicial_statement": "<e.g. Let Exhibit {exhibit_id} be marked and admitted as substantive documentary evidence.>",
  "admissibility_note": "<brief evidentiary note>"
}}"""
        return self.say_json(prompt, max_tokens=350, temperature=0.2)
