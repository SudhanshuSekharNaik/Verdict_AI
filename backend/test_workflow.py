import io
import json
import sys
import requests

# Ensure UTF-8 output on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

def test_full_courtroom_flow():
    print("--- 1. Creating Case ---")
    case_payload = {
        "title": "State v. Arjun Mehta",
        "facts": (
            "On 14 August 2026 at approximately 9:30 PM, a laptop belonging to Neha Sharma was reported stolen "
            "from her locked office at Orion Technologies in Bhubaneswar. Security footage shows Arjun Mehta, an employee "
            "who had access to the office, entering the room at 9:18 PM and leaving approximately eight minutes later carrying "
            "a black backpack. The laptop was last seen on Neha's desk before Arjun entered the room. Arjun states that he "
            "entered the office to collect documents and that the backpack contained his personal belongings. The stolen laptop "
            "was later found three days later at a second-hand electronics shop. The shop owner stated that a person resembling "
            "Arjun had attempted to sell it, but the owner cannot identify the person with certainty. No fingerprints or other "
            "forensic evidence linking Arjun to the laptop have been reported. Arjun denies stealing or selling the laptop."
        ),
        "charge_or_dispute": "Theft — whether Arjun Mehta intentionally took and attempted to dispose of Neha Sharma's laptop without her consent.",
        "total_rounds": 2,
    }
    r = requests.post(f"{BASE_URL}/api/cases", json=case_payload)
    assert r.status_code == 200, f"Failed to create case: {r.text}"
    case = r.json()
    case_id = case["id"]
    print(f"Created Case: {case_id} ({case['docket_number']})")

    print("\n--- 2. Saving Pre-Trial Party Statements ---")
    # Save single statements
    requests.post(
        f"{BASE_URL}/api/cases/{case_id}/statement/single",
        json={
            "speaker": "prosecution",
            "incident_account": "The State submits that Arjun Mehta utilized his authorized access to enter Neha Sharma's locked office at 9:18 PM with a premeditated plan to commit theft.",
            "key_allegations": [
                "Exclusive presence during the 8-minute theft window",
                "Concealment in black backpack",
                "Attempted resale at electronics shop"
            ],
            "what_is_disputed": "Disputes defendant's innocent explanation that backpack only contained personal papers.",
            "theory_of_case": "Defendant intentionally removed property using authorized corporate access.",
            "desired_outcome": "Conviction under BNS §303",
            "facts_relied_upon": ["Fact #1", "Fact #2", "Fact #3", "Fact #5"]
        }
    )
    r_def = requests.post(
        f"{BASE_URL}/api/cases/{case_id}/statement/single",
        json={
            "speaker": "defense",
            "incident_account": "Arjun Mehta entered the office solely to retrieve official project documents. The backpack contained his personal work items. He never touched the laptop.",
            "key_allegations": [
                "Entered solely for legitimate work document collection",
                "Total lack of forensic evidence (no fingerprints/DNA)",
                "Shop owner cannot identify seller with certainty"
            ],
            "what_is_disputed": "Disputes that defendant moved or had possession of the laptop.",
            "theory_of_case": "Presence and opportunity alone do not establish dishonest taking beyond reasonable doubt.",
            "desired_outcome": "Full Acquittal",
            "facts_relied_upon": ["Fact #3", "Fact #4", "Fact #6", "Fact #7"]
        }
    )
    assert r_def.status_code == 200
    print(f"Status after statements: {r_def.json()['status']}")

    print("\n--- 3. Checking Legal Analysis & Issues ---")
    r_la = requests.get(f"{BASE_URL}/api/cases/{case_id}/legal-analysis")
    assert r_la.status_code == 200
    la_data = r_la.json()
    print(f"Applicable Laws ({len(la_data['applicable_laws'])}):")
    for law in la_data["applicable_laws"]:
        print(f"  - {law['act']} ({law['section_or_article']} — {law['title']})")
    print(f"Legal Issues ({len(la_data['legal_issues'])}):")
    for iss in la_data["legal_issues"]:
        print(f"  - [{iss['issue_id']}] {iss['question']}")

    print("\n--- 4. Executing Sequential Turns ---")
    step = 1
    while True:
        r_turn = requests.post(f"{BASE_URL}/api/cases/{case_id}/trial/next-turn")
        assert r_turn.status_code == 200, f"Turn execution failed: {r_turn.text}"
        turn_data = r_turn.json()
        
        if turn_data.get("new_argument"):
            arg = turn_data["new_argument"]
            print(f"Step {step}: [{arg['speaker'].upper()}] {arg['stage_type']} (Legal Basis: {arg.get('legal_basis')})")
        
        if turn_data.get("is_completed"):
            print("\n--- 5. Trial Resolved & Verdict Deliberated ---")
            vrd = turn_data.get("verdict")
            if vrd:
                print(f"Winner: {vrd.get('winner')}")
                print(f"Decision: {vrd.get('decision')}")
                print(f"Confidence: {vrd.get('confidence')}")
                print(f"Decision Basis: {vrd.get('decision_basis')}")
                print("\nIssue-by-Issue Findings:")
                for fnd in vrd.get("issue_findings", []):
                    print(f"  - {fnd['question']}: [{fnd['finding']}] -> {fnd['rationale']}")
                print("\nLaw Assessments:")
                for law_ass in vrd.get("law_assessments", []):
                    print(f"  - {law_ass['provision']}: [{law_ass['status']}] -> {law_ass['rationale']}")
            break
        
        step += 1
        if step > 10:
            print("Safety break reached.")
            break

    print("\n--- 6. Generating Full Case Markdown Report ---")
    r_rep = requests.get(f"{BASE_URL}/api/cases/{case_id}/export?format=markdown")
    assert r_rep.status_code == 200
    print(f"Export successful ({len(r_rep.text)} chars). First 300 chars:\n")
    print(r_rep.text[:300])
    print("\n=== All Tests Passed Successfully ===")

if __name__ == "__main__":
    test_full_courtroom_flow()
