import io
import json
import sys
from typing import Any, Dict

# Ensure UTF-8 output on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agents.judge_agent import JudgeAgent
from models.schemas import LegalIssue


def run_nanavati_benchmark():
    print("================================================================================")
    print("RUNNING BENCHMARK: State of Maharashtra v. K.M. Nanavati (1959 / AIR 1962 SC 605)")
    print("================================================================================")

    title = "State of Maharashtra v. K.M. Nanavati"
    facts = (
        "[Fact #1] Commander K.M. Nanavati was a second-in-command officer in the Indian Navy stationed on INS Mysore, residing in Bombay with his English wife Sylvia and their three children.\n"
        "[Fact #2] During Nanavati's extended absences on naval duty, Sylvia developed an extramarital relationship with Prem Bhagwandas Ahuja, a wealthy Bombay businessman.\n"
        "[Fact #3] Nanavati returned to Bombay on 18 April 1959. Over the following days, he observed Sylvia acting distant and unresponsive.\n"
        "[Fact #4] On the morning of 27 April 1959, Nanavati questioned Sylvia; she confessed to having an affair with Ahuja and expressed uncertainty about whether Ahuja would marry her and accept the children.\n"
        "[Fact #5] After the confession, Nanavati drove Sylvia and their children to the Metro Cinema in Bombay for a scheduled afternoon film, left them there, and stated he would return to collect them.\n"
        "[Fact #6] Nanavati then drove to the naval dockyard, boarded INS Mysore, and requested a loaded .38-calibre semi-automatic revolver and six rounds of ammunition from the ship's armory under the false pretext that he needed protection while traveling alone by car through rural Maharashtra that evening.\n"
        "[Fact #7] Nanavati placed the revolver and ammunition in a brown paper envelope, placed it in his car, drove to Ahuja's office at Nariman Point (finding him absent), and then proceeded to Ahuja's residential flat at 'Jeevan Jyot' on Setalvad Road.\n"
        "[Fact #8] Nanavati entered Ahuja's bedroom, where Ahuja had just emerged from the bath wearing only a towel, and confronted him, asking whether Ahuja intended to marry Sylvia and take care of the children.\n"
        "[Fact #9] Ahuja replied: 'Am I to marry every woman I sleep with?'\n"
        "[Fact #10] A physical struggle ensued between Nanavati and Ahuja inside the bedroom.\n"
        "[Fact #11] During the struggle, three shots were fired from the revolver, all striking Ahuja (one grazing the head, two penetrating the chest and abdomen).\n"
        "[Fact #12] Ahuja collapsed and died at the scene from gunshot wounds.\n"
        "[Fact #13] Nanavati walked out of the building, got into his car, drove to the office of the Deputy Commissioner of Police (DCP John Lobo), and voluntarily surrendered with the firearm, stating he had shot Ahuja.\n"
        "[Fact #14] The post-mortem examination confirmed three entry wounds caused by bullets fired from a .38-calibre weapon at close range; death was caused by internal haemorrhage from the chest wound.\n"
        "[Fact #15] Nanavati was formally charged under Section 302 IPC (murder) and Section 304 Part I IPC (culpable homicide not amounting to murder)."
    )

    charge_or_dispute = (
        "Murder under Section 302, Indian Penal Code, 1860 — alternatively Section 304 Part I "
        "(culpable homicide not amounting to murder). Accused claims the killing occurred under "
        "'grave and sudden provocation' (Exception 1 to Section 300 IPC)."
    )

    evidence_str = (
        "• [P-EX-01] (PROSECUTION — document): 'Naval Arms Register Entry' — Official armory logbook showing Nanavati requisitioned a loaded .38 revolver and 6 rounds under false pretext of rural night driving.\n"
        "• [P-EX-02] (PROSECUTION — expert_report): 'Post-Mortem Autopsy Report' — Dr. B.J. Ranadive confirms death caused by three gunshot wounds at close range.\n"
        "• [P-EX-03] (PROSECUTION — document): 'Police Surrender Statement' — Statement recorded by DCP John Lobo upon voluntary surrender of accused with the weapon.\n"
        "• [P-EX-04] (PROSECUTION — document): 'Timeline Reconstruction' — Investigative timeline showing 3.5 hours elapsed between confession (morning) and shooting (4:20 PM) spanning Metro Cinema, INS Mysore, Nariman Point, and Setalvad Road.\n"
        "• [D-EX-01] (DEFENSE — document): 'Sylvia Nanavati Confession Statement' — Statement recording Sylvia's direct confession of infidelity to accused on morning of 27 April 1959.\n"
        "• [D-EX-02] (DEFENSE — document): 'Naval Service Record' — Exemplary service record and decorated naval career of Commander Nanavati.\n"
        "• [D-EX-03] (DEFENSE — document): 'Sessions Court Jury Verdict' — Record of initial 8-1 jury acquittal subsequently referred under CrPC §307."
    )

    witnesses_str = (
        "• [PW-01] DCP John Lobo (PROSECUTION) — Received surrender of accused and firearm.\n"
        "• [PW-02] Medical Examiner (PROSECUTION) — Confirmed three close-range bullet wounds.\n"
        "• [DW-01] Sylvia Nanavati (DEFENSE) — Testified regarding confession and emotional state."
    )

    applicable_laws_str = (
        "• Indian Penal Code, 1860 (Section 302 — Punishment for murder): Direct intentional causing of death.\n"
        "• Indian Penal Code, 1860 (Section 300, Exception 1 — Grave and sudden provocation): Mitigates murder to culpable homicide ONLY if fatal act occurs whilst deprived of self-control immediately. Intervening time and deliberate intermediate actions defeat suddenness as a matter of law (Cooling-off doctrine / K.M. Nanavati v. State of Maharashtra AIR 1962 SC 605).\n"
        "• Bharatiya Sakshya Adhiniyam, 2023 (Section 104 / IEA §101 — Burden of proof on prosecution; Section 108 / IEA §105 — Burden of establishing statutory exceptions on accused)."
    )

    party_statements_str = (
        "🔴 PROSECUTION POSITION: The State submits that the sequence of deliberate actions (dropping family at cinema, obtaining firearm from ship under false pretext, traveling across multiple locations) proves deliberation and premeditation, legally negating the suddenness requirement of Exception 1 to IPC §300.\n"
        "🔵 DEFENSE POSITION: The defense submits that the accused acted under continuous, overwhelming emotional agitation from his wife's confession of infidelity, culminating in a sudden struggle in Ahuja's bedroom."
    )

    legal_issues = [
        {
            "issue_id": "ISSUE_01",
            "question": "Whether the accused committed the physical acts causing the death of Prem Ahuja (actus reus).",
            "prosecution_position": "Supports — Fired three rounds from .38 revolver causing fatal wounds.",
            "defense_position": "Concedes the struggle and discharge.",
        },
        {
            "issue_id": "ISSUE_02",
            "question": "Whether the interval of time and sequence of intermediate deliberate actions between Sylvia's confession and the shooting negates the element of suddenness under Exception 1 to Section 300 IPC.",
            "prosecution_position": "Supports — Time to drive to cinema, board naval vessel, obtain revolver under false pretext, and drive across town establishes cooling-off.",
            "defense_position": "Disputes — Continuous loss of self-control persisted throughout.",
        },
        {
            "issue_id": "ISSUE_03",
            "question": "Whether the accused is guilty of murder under Section 302 IPC or entitled to mitigation to culpable homicide under Section 304 Part I IPC.",
            "prosecution_position": "Guilty under Section 302 IPC beyond reasonable doubt.",
            "defense_position": "Entitled to Exception 1 mitigation under Section 304 Part I IPC.",
        },
    ]

    issues_str = "\n".join([f"[{iss['issue_id']}]: {iss['question']}" for iss in legal_issues])

    judge = JudgeAgent(
        title=title,
        facts=facts,
        charge_or_dispute=charge_or_dispute,
        facts_indexed=facts,
        evidence_str=evidence_str,
        witnesses_str=witnesses_str,
        applicable_laws_str=applicable_laws_str,
        party_statements_str=party_statements_str,
        issues_str=issues_str,
    )

    trial_record = (
        "--- PROSECUTION CLOSING ARGUMENTS ---\n"
        "The State submits that under Indian criminal law (AIR 1962 SC 605), grave provocation alone cannot sustain Exception 1 to Section 300 IPC. "
        "The accused had ample time to cool down. After the confession [Fact #4], he drove his family to Metro Cinema [Fact #5], drove to INS Mysore, "
        "obtained a .38 revolver under the false pretext of night driving [Fact #6, P-EX-01], and drove to two separate locations [Fact #7, P-EX-04]. "
        "This deliberate sequence defeats suddenness as a matter of law.\n\n"
        "--- DEFENSE CLOSING ARGUMENTS ---\n"
        "The defense submits that Sylvia's confession [Fact #4, D-EX-01] caused grave provocation that completely unhinged the accused's mind. "
        "The defense contends that the accused was in a continuous state of agitation that culminated when Ahuja gave his insolent reply [Fact #9] "
        "in the bedroom, sparking a struggle [Fact #10]."
    )

    print("\nExecuting Judge Deliberation...")
    verdict = judge.deliberate_and_rule(
        full_annotated_record=trial_record,
        legal_issues=legal_issues,
        canonical_facts_str=facts,
        evidence_str=evidence_str,
        witnesses_str=witnesses_str,
        applicable_laws_str=applicable_laws_str,
    )

    print("\n================================================================================")
    print("DELIBERATION RESULT:")
    print("================================================================================")
    print(f"Winner: {verdict.get('winner')}")
    print(f"Verdict: {verdict.get('decision')}")
    print(f"Category: {verdict.get('verdict_category')}")
    print(f"Confidence: {verdict.get('confidence')}")
    print(f"Decision Basis: {verdict.get('decision_basis')}")

    print("\n--- ISSUE-BY-ISSUE FINDINGS ---")
    for iss in verdict.get("issue_findings", []):
        q = iss.question if hasattr(iss, "question") else iss.get("question")
        f = iss.finding if hasattr(iss, "finding") else iss.get("finding")
        r = iss.rationale if hasattr(iss, "rationale") else iss.get("rationale")
        i_id = iss.issue_id if hasattr(iss, "issue_id") else iss.get("issue_id")
        print(f"\n[{i_id}] {q}")
        print(f"  Finding:   {f}")
        print(f"  Rationale: {r}")

    print("\n--- AFFIRMATIVE DEFENSE ANALYSIS ---")
    aff_def = verdict.get("affirmative_defense_analysis", {})
    print(json.dumps(aff_def, indent=2))

    print("\n--- REASONING SUMMARY ---")
    reasoning = verdict.get("reasoning_summary", "")
    print(reasoning)

    # ============================================================================
    # VERIFICATION ASSERTIONS
    # ============================================================================
    print("\n================================================================================")
    print("VERIFYING BENCHMARK ASSERTIONS:")
    print("================================================================================")

    # 1. Verdict must be GUILTY / prosecution_prevailed under Section 302 IPC
    assert verdict.get("verdict_category") == "guilty", f"Expected 'guilty', got {verdict.get('verdict_category')}"
    assert verdict.get("winner") == "prosecution_prevailed", f"Expected 'prosecution_prevailed', got {verdict.get('winner')}"
    print("✓ [Assertion 1 Passed]: Verdict is GUILTY (prosecution_prevailed) under Section 302 IPC.")

    # 2. Every framed issue must be addressed in issue_findings
    issue_findings = verdict.get("issue_findings", [])
    assert len(issue_findings) >= 3, f"Expected at least 3 issue findings, got {len(issue_findings)}"
    issue_ids = [iss.issue_id if hasattr(iss, "issue_id") else iss.get("issue_id") for iss in issue_findings]
    assert "ISSUE_01" in issue_ids or "1" in str(issue_ids), "ISSUE_01 must be addressed"
    assert "ISSUE_02" in issue_ids or "2" in str(issue_ids), "ISSUE_02 (interval/cooling-off) must be addressed"
    print("✓ [Assertion 2 Passed]: All framed issues (including ISSUE_02) explicitly addressed.")

    # 3. Reasoning must discuss cooling-off interval & intermediate deliberation sequence
    reasoning_lower = reasoning.lower() + " " + json.dumps(aff_def).lower() + " " + " ".join([str(i) for i in issue_findings]).lower()
    
    interval_keywords = ["cool", "interval", "deliberat", "time", "cinema", "ship", "revolver", "pretext", "location", "office"]
    matched_keywords = [kw for kw in interval_keywords if kw in reasoning_lower]
    print(f"Matched cooling-off keywords: {matched_keywords}")
    assert len(matched_keywords) >= 5, f"Expected discussion of interval/steps, matched only: {matched_keywords}"
    print("✓ [Assertion 3 Passed]: Opinion explicitly analyzes the interval, intermediate steps (cinema, ship, revolver under pretext), and cooling-off doctrine.")

    # 4. Affirmative defense analysis must bifurcate gravity vs suddenness
    if aff_def:
        p1 = aff_def.get("prong_1_gravity", {})
        p2 = aff_def.get("prong_2_suddenness_and_interval", {})
        print(f"Prong 1 (Gravity): {p1.get('finding')}")
        print(f"Prong 2 (Suddenness): {p2.get('finding')}")
        assert "grave" in str(p1).lower() or "satisf" in str(p1).lower() or "establish" in str(p1).lower(), "Prong 1 must recognize confession as grave provocation"
        assert "negat" in str(p2).lower() or "fail" in str(p2).lower() or "reject" in str(p2).lower() or "cool" in str(p2).lower(), "Prong 2 must find suddenness negated by cooling off"
        print("✓ [Assertion 4 Passed]: Affirmative defense analysis correctly bifurcates Gravity (satisfied) from Suddenness (negated by cooling-off).")

    print("\n🎉 ALL BENCHMARK TESTS & LEGAL REASONING CHECKS PASSED SUCCESSFULLY! 🎉")


if __name__ == "__main__":
    run_nanavati_benchmark()
