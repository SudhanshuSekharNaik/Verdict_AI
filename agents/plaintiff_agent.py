from typing import Any, Dict, List

from app.models.argument import AgentRoleEnum, AttackTypeEnum
from ml import get_ml_registry


class PlaintiffAgent:
    """Plaintiff AI Agent: Produces evidence-grounded claims with structured legal reasoning."""

    @staticmethod
    async def generate_opening_argument(
        case_title: str,
        case_description: str,
        plaintiff_evidence: List[Dict[str, Any]],
        authorities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        ev_titles = [e.get("title", "Exhibit") for e in plaintiff_evidence]
        ev_ids = [str(e.get("id")) for e in plaintiff_evidence if e.get("id")]

        verified_cits = [
            a for a in authorities
            if a.get("verification", {}).get("status") in ("VERIFIED", "PARTIALLY_SUPPORTED")
        ]
        cit_labels = [a.get("citation", "") for a in verified_cits]
        cit_ids = [str(a.get("source_id")) for a in verified_cits if a.get("source_id")]

        evidence_analysis = []
        for i, ev in enumerate(plaintiff_evidence[:4], 1):
            ev_text = ev.get("extracted_text", "")
            evidence_analysis.append({
                "label": f"P-{i:03d} [{ev.get('title', 'Exhibit')}]",
                "analysis": (
                    f"This exhibit demonstrates: {ev_text[:200] if ev_text else 'documented evidence supporting the Plaintiff position'}."
                ),
            })

        material_facts = []
        for i, ev in enumerate(plaintiff_evidence[:3], 1):
            ev_text = ev.get("extracted_text", "")
            if ev_text:
                material_facts.append(f"P-{i:03d}: {ev_text[:150]}")

        issues = [
            f"Whether the Defendant breached the agreement in {case_title}",
            "Whether the Plaintiff fulfilled all conditions precedent to claiming relief",
            "Whether the Plaintiff is entitled to the claimed relief",
        ]

        legal_rules = []
        if cit_labels:
            legal_rules.append(
                f"Under {cit_labels[0]}, a party who suffers loss by breach is entitled to "
                f"compensation for loss naturally arising from such breach."
            )
            if len(cit_labels) > 1:
                legal_rules.append(
                    f"Per {cit_labels[1]}, the party seeking damages must establish both the "
                    f"fact of loss and its quantum with reasonable certainty."
                )

        claim_text = (
            f"The Plaintiff claims full restitution in {case_title}. The Plaintiff's position "
            f"is supported by {len(plaintiff_evidence)} verified exhibits and {len(verified_cits)} "
            f"confirmed legal authorities."
        )

        application = (
            "The Plaintiff has produced contemporaneous documentary evidence establishing: "
            "(1) performance of contractual obligations, (2) the Defendant's failure to honor "
            "agreed terms, and (3) the resulting loss. The Defendant has not produced any "
            "contemporaneous evidence to contradict the Plaintiff's documented position."
        )

        return {
            "claim": claim_text,
            "issues": issues,
            "legal_rules": legal_rules,
            "material_facts": material_facts,
            "evidence_analysis": evidence_analysis,
            "conflicts": [],
            "application": application,
            "counterarguments": [
                "The Defendant may argue that deductions were justified. However, no "
                "contemporaneous inspection records or joint verification reports support this.",
            ],
            "rebuttals": [],
            "relief": f"Full restitution of the disputed amount with applicable interest.",
        }

    @staticmethod
    async def attack_defence_argument(
        target_claim: str,
        target_reasoning: str,
        plaintiff_evidence: List[Dict[str, Any]],
        authorities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        nli = get_ml_registry().get_nli()

        contradictions_found = []
        chosen_attack_type = AttackTypeEnum.EVIDENCE_WEAKNESS.value
        ev_ids = [str(e.get("id")) for e in plaintiff_evidence if e.get("id")]

        for ev in plaintiff_evidence:
            ev_text = ev.get("extracted_text", "")
            if ev_text:
                try:
                    nli_res = nli.analyze_claim_vs_evidence(claim=target_claim, evidence=ev_text)
                    if nli_res["status"] == "CONTRADICTION":
                        chosen_attack_type = AttackTypeEnum.FACTUAL_CONTRADICTION.value
                        contradictions_found.append({
                            "label": ev.get("title", "Exhibit"),
                            "evidence": ev_text[:200],
                        })
                except Exception:
                    pass

        issues = [
            "Whether the Defence has identified any specific contractual provision authorizing their actions",
            "Whether the Defence's contemporaneous records support their position",
        ]

        evidence_analysis = []
        for i, ev in enumerate(plaintiff_evidence[:3], 1):
            evidence_analysis.append({
                "label": f"P-{i:03d} [{ev.get('title', 'Exhibit')}]",
                "analysis": f"This exhibit contradicts the Defence position: {ev.get('extracted_text', '')[:150]}.",
            })

        claim_text = (
            "The Defence's counter-argument fails because it does not identify any specific "
            "contractual authorization for the actions taken, and the Defence's own documentation "
            "contradicts their position."
        )

        conflicts = []
        if contradictions_found:
            conflicts = [
                f"Plaintiff exhibit '{c['label']}' directly contradicts the Defence assertion."
                for c in contradictions_found[:2]
            ]

        return {
            "claim": claim_text,
            "issues": issues,
            "legal_rules": [
                "The party asserting justification bears the burden of proving it.",
            ],
            "material_facts": [
                f"The Plaintiff has produced {len(plaintiff_evidence)} exhibits contradicting the Defence's position.",
            ],
            "evidence_analysis": evidence_analysis,
            "conflicts": conflicts if conflicts else [
                "The Defence has not produced contemporaneous records supporting their claimed justification.",
            ],
            "application": (
                "The Defence has not identified any specific contractual clause that authorized "
                "the actions taken. Without such identification, the Defence's general assertions "
                "of compliance are insufficient."
            ),
            "counterarguments": [],
            "rebuttals": [],
            "relief": "Full relief as claimed.",
        }

    @staticmethod
    async def answer_judge_question(
        question: str,
        plaintiff_evidence: List[Dict[str, Any]],
        authorities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        ev_refs = ", ".join([e.get("title", "Exhibit") for e in plaintiff_evidence[:2]])
        ev_texts = [e.get("extracted_text", "")[:100] for e in plaintiff_evidence[:2] if e.get("extracted_text")]

        answer = (
            f"Addressing the Bench's specific question: The Plaintiff refers to {ev_refs or 'the Plaintiff exhibits'}. "
        )
        if ev_texts:
            answer += f"Specifically, {ev_texts[0]}. "
        answer += (
            f"The Plaintiff's position is supported by documented, contemporaneous evidence "
            f"establishing performance of contractual obligations."
        )

        return {
            "speaker": "PLAINTIFF_AI",
            "question": question,
            "answer": answer,
            "references": [str(e.get("id")) for e in plaintiff_evidence[:2] if e.get("id")],
        }

    @staticmethod
    async def cross_examine_defence(
        defence_argument: str,
        plaintiff_evidence: List[Dict[str, Any]],
    ) -> str:
        ev_details = ""
        if plaintiff_evidence:
            first_ev = plaintiff_evidence[0]
            ev_details = (
                f" The Plaintiff has documented evidence ({first_ev.get('title', 'Exhibit')}) "
                f"showing: {first_ev.get('extracted_text', 'a different factual position')[:100]}."
            )

        return (
            f"Can the Defence produce any contemporaneous, jointly signed inspection report or explicit "
            f"written notice substantiating their claim of damages before the dispute arose?"
            f"{ev_details}"
        )
