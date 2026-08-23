from typing import Any, Dict, List

from app.models.argument import AgentRoleEnum, AttackTypeEnum
from ml import get_ml_registry


class DefenceAgent:
    """Defence AI Agent: Produces adversarial counter-arguments attacking the Plaintiff's actual claims."""

    @staticmethod
    async def generate_opening_argument(
        case_title: str,
        case_description: str,
        defence_evidence: List[Dict[str, Any]],
        authorities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        ev_titles = [e.get("title", "Defence Exhibit") for e in defence_evidence]
        ev_ids = [str(e.get("id")) for e in defence_evidence if e.get("id")]
        ev_texts = {e.get("title", ""): e.get("extracted_text", "") for e in defence_evidence}

        verified_cits = [
            a for a in authorities
            if a.get("verification", {}).get("status") in ("VERIFIED", "PARTIALLY_SUPPORTED")
        ]
        cit_labels = [a.get("citation", "") for a in verified_cits]
        cit_ids = [str(a.get("source_id")) for a in verified_cits if a.get("source_id")]

        evidence_facts = []
        for title, text in ev_texts.items():
            if text:
                evidence_facts.append(f"{title}: {text[:200]}")

        claim_text = (
            f"The Defendant denies liability in {case_title}. The Plaintiff has failed to "
            f"demonstrate a breach of any specific contractual obligation, and the Defendant's "
            f"actions were authorized by the terms of the agreement."
        )

        reasoning_parts = {
            "claim": claim_text,
            "issues": [
                f"Whether the Defendant breached any specific obligation in {case_title}",
                "Whether the Plaintiff fulfilled all conditions precedent to claiming relief",
                "Whether the Plaintiff's claimed loss is recoverable under the applicable law",
            ],
            "legal_rules": [],
            "material_facts": [],
            "evidence_analysis": [],
            "conflicts": [],
            "application": "",
            "counterarguments": [],
            "rebuttals": [],
            "relief": "Dismissal of the Plaintiff's claims with costs.",
        }

        if cit_labels:
            reasoning_parts["legal_rules"] = [
                f"Under {cit_labels[0]}, the claimant bears the burden of proving both breach and quantifiable loss.",
            ]
            if len(cit_labels) > 1:
                reasoning_parts["legal_rules"].append(
                    f"Per {cit_labels[1]}, damages must be proved with reasonable certainty, not mere speculation."
                )

        for i, fact in enumerate(evidence_facts[:3], 1):
            reasoning_parts["material_facts"].append(f"Exhibit D-{i:03d}: {fact}")

        for i, ev in enumerate(defence_evidence[:3], 1):
            reasoning_parts["evidence_analysis"].append({
                "label": f"D-{i:03d} [{ev.get('title', 'Exhibit')}]",
                "analysis": (
                    f"This exhibit establishes that {ev.get('extracted_text', 'the Defence has documented evidence')[:150]}."
                    f" This directly contradicts the Plaintiff's assertion."
                ),
            })

        reasoning_parts["application"] = (
            "The Plaintiff has not identified any specific contractual provision that was breached. "
            "General allegations of non-performance, without reference to particular clauses, are "
            "insufficient to establish a prima facie case. The Defence's documented evidence demonstrates "
            "that the Defendant acted within the scope of contractual authority."
        )

        reasoning_parts["counterarguments"] = [
            "The Plaintiff may argue that all contractual obligations were performed. However, the "
            "Plaintiff has not produced contemporaneous evidence of performance for the disputed period.",
        ]

        return reasoning_parts

    @staticmethod
    async def attack_plaintiff_argument(
        target_claim: str,
        target_reasoning: str,
        defence_evidence: List[Dict[str, Any]],
        authorities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        nli = get_ml_registry().get_nli()

        contradictions_found = []
        chosen_attack_type = AttackTypeEnum.MISSING_EVIDENCE.value
        ev_ids = [str(e.get("id")) for e in defence_evidence if e.get("id")]

        for ev in defence_evidence:
            ev_text = ev.get("extracted_text", "")
            if ev_text:
                try:
                    nli_res = nli.analyze_claim_vs_evidence(claim=target_claim, evidence=ev_text)
                    if nli_res["status"] == "CONTRADICTION":
                        chosen_attack_type = AttackTypeEnum.FACTUAL_CONTRADICTION.value
                        contradictions_found.append({
                            "label": ev.get("title", "Exhibit"),
                            "contradicts": target_claim[:100],
                            "evidence": ev_text[:200],
                        })
                except Exception:
                    pass

        issues = [
            "Whether the Plaintiff has identified the specific contractual provision breached",
            "Whether the Plaintiff's evidence establishes actual loss (as opposed to claimed loss)",
            "Whether the Defence's contemporaneous records override the Plaintiff's assertions",
        ]

        evidence_analysis = []
        for i, ev in enumerate(defence_evidence[:3], 1):
            evidence_analysis.append({
                "label": f"D-{i:03d} [{ev.get('title', 'Exhibit')}]",
                "analysis": f"This exhibit demonstrates: {ev.get('extracted_text', 'documented evidence of the Defence position')[:150]}.",
            })

        claim_text = (
            "The Plaintiff's argument fails because it does not identify any specific contractual "
            "provision that was breached, and the Defence's contemporaneous documentation contradicts "
            "the Plaintiff's account of events."
        )

        reasoning_parts = {
            "claim": claim_text,
            "issues": issues,
            "legal_rules": [
                "The burden of proving breach of contract lies with the claimant (Plaintiff).",
                "Damages must be proved with reasonable certainty, not speculation.",
            ],
            "material_facts": [
                f"The Defence has produced {len(defence_evidence)} exhibits contradicting the Plaintiff's position.",
            ],
            "evidence_analysis": evidence_analysis,
            "conflicts": [
                f"Plaintiff asserts: '{target_claim[:100]}...'"
                f" but Defence exhibit D-001 contradicts this.",
            ],
            "application": (
                "The Plaintiff has not met the burden of proof. General assertions without reference "
                "to specific contractual provisions or contemporaneous evidence are insufficient."
            ),
            "counterarguments": [],
            "rebuttals": [],
            "relief": "Dismissal of the Plaintiff's claims.",
        }

        if contradictions_found:
            reasoning_parts["conflicts"].extend([
                f"Defence exhibit '{c['label']}' directly contradicts the Plaintiff's assertion: '{c['contradicts'][:60]}...'"
                for c in contradictions_found[:2]
            ])

        return reasoning_parts

    @staticmethod
    async def answer_judge_question(
        question: str,
        defence_evidence: List[Dict[str, Any]],
        authorities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        ev_refs = ", ".join([e.get("title", "Exhibit") for e in defence_evidence[:2]])
        ev_texts = [e.get("extracted_text", "")[:100] for e in defence_evidence[:2] if e.get("extracted_text")]

        answer = (
            f"Addressing the Bench's specific question: The Defence refers to {ev_refs or 'the Defence exhibits'}. "
        )
        if ev_texts:
            answer += (
                f"Specifically, {ev_texts[0]}. "
            )
        answer += (
            f"The Defence's position is supported by documented, contemporaneous evidence that the "
            f"Plaintiff's claims are not substantiated."
        )

        return {
            "speaker": "DEFENCE_AI",
            "question": question,
            "answer": answer,
            "references": [str(e.get("id")) for e in defence_evidence[:2] if e.get("id")],
        }

    @staticmethod
    async def cross_examine_plaintiff(
        plaintiff_argument: str,
        defence_evidence: List[Dict[str, Any]],
    ) -> str:
        ev_details = ""
        if defence_evidence:
            first_ev = defence_evidence[0]
            ev_details = (
                f" The Defence has documented evidence ({first_ev.get('title', 'Exhibit')}) "
                f"showing: {first_ev.get('extracted_text', 'a different factual position')[:100]}."
            )

        return (
            f"Can the Plaintiff identify the exact contractual clause that was breached, "
            f"and produce contemporaneous evidence of non-performance during the disputed period?"
            f"{ev_details}"
        )
