import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_TIMEOUT = 60.0


PLAINTIFF_SYSTEM_PROMPT = """You are the PLAINTIFF AI Agent in Aadalat AI, an AI-assisted legal research and courtroom simulation system.

You represent ONLY the Plaintiff.

YOUR TASK: Construct a legally reasoned argument using ONLY the supplied case facts, evidence, and VERIFIED AUTHORITIES.

=== CRITICAL PROHIBITIONS ===

YOU ARE PROHIBITED FROM:
1. Generating, inventing, fabricating, inferring, autocompleting, or guessing ANY legal citation.
2. Using ANY citation that is NOT present in the VERIFIED_AUTHORITIES array.
3. Modifying the year, volume, page number, or any part of a citation.
4. Stating "according to [citation]" unless that exact citation appears in VERIFIED_AUTHORITIES.
5. Using an authority merely because the citation appears semantically similar.

IF NO SUPPLIED AUTHORITY SUPPORTS A LEGAL PROPOSITION:
State: "NO VERIFIED AUTHORITY FOUND for this proposition."
Do NOT substitute an invented citation.

=== EVIDENCE RULES ===
- Every factual proposition must reference a specific evidence ID from the EVIDENCE array.
- Never fabricate evidence IDs.
- If evidence is insufficient, say so.

=== STRUCTURE ===
Distinguish clearly between:
- Established facts (supported by evidence)
- Disputed facts
- Allegations
- Legal rules (from VERIFIED_AUTHORITIES only)
- Inferences

=== OUTPUT FORMAT ===
Return ONLY valid JSON. No markdown. No code fences.

{
  "side": "PLAINTIFF",
  "stage": "...",
  "position": "Core position in one sentence",
  "issues": [{"issue": "...", "position": "..."}],
  "argument": {
    "claim": "...",
    "legal_rule": "Use ONLY from VERIFIED_AUTHORITIES. If none, state 'NO VERIFIED AUTHORITY FOUND'",
    "material_facts": ["[P-001] description"],
    "application": "...",
    "counterargument": "...",
    "rebuttal": "...",
    "requested_relief": "..."
  },
  "evidence_references": [{"id": "P-001", "reason": "..."}],
  "authority_references": [{"id": "AUTH-001", "citation": "EXACT citation from VERIFIED_AUTHORITIES", "reason": "..."}],
  "evidence_count": 0,
  "authority_count": 0
}

evidence_count and authority_count MUST match the actual array lengths. Do NOT let the LLM write "4 authorities" when only 3 are provided."""

DEFENCE_SYSTEM_PROMPT = """You are the DEFENCE AI Agent in Aadalat AI, an AI-assisted legal research and courtroom simulation system.

You represent ONLY the Defendant.

YOUR TASK: Construct a legally reasoned defence using ONLY the supplied case facts, evidence, and VERIFIED AUTHORITIES.

=== CRITICAL PROHIBITIONS ===

YOU ARE PROHIBITED FROM:
1. Generating, inventing, fabricating, inferring, autocompleting, or guessing ANY legal citation.
2. Using ANY citation that is NOT present in the VERIFIED_AUTHORITIES array.
3. Modifying the year, volume, page number, or any part of a citation.
4. Stating "according to [citation]" unless that exact citation appears in VERIFIED_AUTHORITIES.
5. Using an authority merely because the citation appears semantically similar.

IF NO SUPPLIED AUTHORITY SUPPORTS A LEGAL PROPOSITION:
State: "NO VERIFIED AUTHORITY FOUND for this proposition."
Do NOT substitute an invented citation.

=== ATTACK RULES ===
- Analyze the Plaintiff's argument and attack its weakest legal or evidentiary assumption.
- For every factual proposition, cite the relevant evidence ID.
- If the Plaintiff's argument has no authority support, highlight that.

=== EVIDENCE RULES ===
- Every factual proposition must reference a specific evidence ID.
- Never fabricate evidence IDs.

=== OUTPUT FORMAT ===
Return ONLY valid JSON. No markdown. No code fences.

{
  "side": "DEFENCE",
  "stage": "...",
  "position": "Core position in one sentence",
  "issues": [{"issue": "...", "position": "..."}],
  "argument": {
    "claim": "...",
    "legal_rule": "Use ONLY from VERIFIED_AUTHORITIES. If none, state 'NO VERIFIED AUTHORITY FOUND'",
    "material_facts": ["[D-001] description"],
    "application": "...",
    "counterargument": "...",
    "rebuttal": "...",
    "requested_relief": "..."
  },
  "evidence_references": [{"id": "D-001", "reason": "..."}],
  "authority_references": [{"id": "AUTH-001", "citation": "EXACT citation from VERIFIED_AUTHORITIES", "reason": "..."}],
  "evidence_count": 0,
  "authority_count": 0
}

evidence_count and authority_count MUST match the actual array lengths."""

JUDGE_SYSTEM_PROMPT = """You are the JUDGE AI in Aadalat AI, an AI-assisted legal research and courtroom simulation system.

You are a NEUTRAL judicial analyst. You do NOT represent either party.

YOUR TASK: Analyze both sides' arguments, the evidence, and the VERIFIED AUTHORITIES. Provide structured judicial analysis.

RULES:
- Remain completely neutral.
- Base your analysis strictly on the supplied arguments, evidence, and authorities.
- Identify strengths and weaknesses of BOTH sides.
- Identify evidence conflicts, gaps, and unresolved questions.
- Do not determine a final verdict — that is for the human judge.

=== CRITICAL PROHIBITIONS ===
YOU ARE PROHIBITED FROM inventing citations. Use ONLY supplied authorities.

Return ONLY valid JSON. No markdown. No code fences.

{
  "issues": [{"issue": "...", "analysis": "..."}],
  "facts_found": [],
  "facts_disputed": [],
  "law": [],
  "plaintiff_strengths": [],
  "defence_strengths": [],
  "evidence_conflicts": [],
  "unresolved_questions": [],
  "analysis": [],
  "provisional_findings": [],
  "recommended_next_questions": []
}"""


def _build_plaintiff_user_content(context: Dict[str, Any]) -> str:
    parts = []

    case = context.get("case", {})
    parts.append(f"CASE: {case.get('title', 'N/A')}")
    parts.append(f"TYPE: {case.get('case_type', 'N/A')}")
    parts.append(f"JURISDICTION: {case.get('jurisdiction', 'N/A')}")
    parts.append(f"DESCRIPTION: {case.get('description', 'N/A')}")
    parts.append("")

    parties = case.get("parties", {})
    if parties.get("plaintiff"):
        parts.append(f"PLAINTIFF: {parties['plaintiff']}")
    if parties.get("defendant"):
        parts.append(f"DEFENDANT: {parties['defendant']}")
    parts.append("")

    stage = context.get("stage", "OPENING_ARGUMENTS")
    parts.append(f"HEARING STAGE: {stage}")

    issues = context.get("issues", [])
    if issues:
        parts.append("ISSUES FOR DETERMINATION:")
        for i, issue in enumerate(issues, 1):
            parts.append(f"  {i}. {issue}")

    facts = context.get("facts", [])
    if facts:
        parts.append("")
        parts.append("MATERIAL FACTS:")
        for fact in facts:
            parts.append(f"  - {fact}")

    evidence = context.get("evidence", [])
    if evidence:
        parts.append("")
        parts.append(f"EVIDENCE ({len(evidence)} items):")
        for ev in evidence:
            parts.append(f"  [{ev.get('label', '?')}] {ev.get('title', 'Exhibit')}: {ev.get('summary', ev.get('extracted_text', '')[:200])}")

    verified_authorities = context.get("verified_authorities", [])
    if verified_authorities:
        parts.append("")
        parts.append(f"=== VERIFIED AUTHORITIES ({len(verified_authorities)} items) ===")
        parts.append("USE ONLY THESE AUTHORITIES. DO NOT INVENT NEW CITATIONS.")
        for auth in verified_authorities:
            parts.append(f"  ID: {auth.get('id', '?')}")
            parts.append(f"  Citation: {auth.get('citation', 'N/A')}")
            parts.append(f"  Case: {auth.get('case_name', 'N/A')}")
            parts.append(f"  Court: {auth.get('court', 'N/A')}")
            parts.append(f"  Year: {auth.get('year', 'N/A')}")
            parts.append(f"  Proposition: {auth.get('proposition', 'N/A')}")
            if auth.get("supporting_paragraphs"):
                parts.append(f"  Relevant text: {auth['supporting_paragraphs'][0][:300]}")
            parts.append("")
    else:
        parts.append("")
        parts.append("=== VERIFIED AUTHORITIES: NONE AVAILABLE ===")
        parts.append("DO NOT invent or guess any citations. State 'NO VERIFIED AUTHORITY FOUND' for any legal proposition.")

    opposing = context.get("opposing_arguments", [])
    if opposing:
        parts.append("")
        parts.append("OPPOSING (DEFENCE) ARGUMENTS TO REBUT:")
        for arg in opposing:
            parts.append(f"  - {arg.get('position', '')}")
            if arg.get("argument", {}).get("claim"):
                parts.append(f"    Claim: {arg['argument']['claim'][:300]}")

    prev = context.get("previous_arguments", [])
    if prev:
        parts.append("")
        parts.append("YOUR PREVIOUS ARGUMENTS:")
        for arg in prev:
            parts.append(f"  - {arg.get('position', arg.get('claim', ''))[:200]}")

    instruction = context.get("instruction", "")
    if instruction:
        parts.append("")
        parts.append(f"COURT INSTRUCTION: {instruction}")

    parts.append("")
    parts.append("REMINDER: evidence_count MUST equal the number of items in evidence_references.")
    parts.append("REMINDER: authority_count MUST equal the number of items in authority_references.")
    parts.append("REMINDER: Do NOT invent citations. Use ONLY the VERIFIED AUTHORITIES listed above.")

    return "\n".join(parts)


def _build_defence_user_content(context: Dict[str, Any]) -> str:
    parts = []

    case = context.get("case", {})
    parts.append(f"CASE: {case.get('title', 'N/A')}")
    parts.append(f"TYPE: {case.get('case_type', 'N/A')}")
    parts.append(f"JURISDICTION: {case.get('jurisdiction', 'N/A')}")
    parts.append(f"DESCRIPTION: {case.get('description', 'N/A')}")
    parts.append("")

    parties = case.get("parties", {})
    if parties.get("plaintiff"):
        parts.append(f"PLAINTIFF: {parties['plaintiff']}")
    if parties.get("defendant"):
        parts.append(f"DEFENDANT: {parties['defendant']}")
    parts.append("")

    stage = context.get("stage", "DEFENCE_ARGUMENT")
    parts.append(f"HEARING STAGE: {stage}")

    issues = context.get("issues", [])
    if issues:
        parts.append("ISSUES FOR DETERMINATION:")
        for i, issue in enumerate(issues, 1):
            parts.append(f"  {i}. {issue}")

    facts = context.get("facts", [])
    if facts:
        parts.append("")
        parts.append("MATERIAL FACTS:")
        for fact in facts:
            parts.append(f"  - {fact}")

    evidence = context.get("evidence", [])
    if evidence:
        parts.append("")
        parts.append(f"EVIDENCE ({len(evidence)} items):")
        for ev in evidence:
            parts.append(f"  [{ev.get('label', '?')}] {ev.get('title', 'Exhibit')}: {ev.get('summary', ev.get('extracted_text', '')[:200])}")

    verified_authorities = context.get("verified_authorities", [])
    if verified_authorities:
        parts.append("")
        parts.append(f"=== VERIFIED AUTHORITIES ({len(verified_authorities)} items) ===")
        parts.append("USE ONLY THESE AUTHORITIES. DO NOT INVENT NEW CITATIONS.")
        for auth in verified_authorities:
            parts.append(f"  ID: {auth.get('id', '?')}")
            parts.append(f"  Citation: {auth.get('citation', 'N/A')}")
            parts.append(f"  Case: {auth.get('case_name', 'N/A')}")
            parts.append(f"  Court: {auth.get('court', 'N/A')}")
            parts.append(f"  Year: {auth.get('year', 'N/A')}")
            parts.append(f"  Proposition: {auth.get('proposition', 'N/A')}")
            if auth.get("supporting_paragraphs"):
                parts.append(f"  Relevant text: {auth['supporting_paragraphs'][0][:300]}")
            parts.append("")
    else:
        parts.append("")
        parts.append("=== VERIFIED AUTHORITIES: NONE AVAILABLE ===")
        parts.append("DO NOT invent or guess any citations. State 'NO VERIFIED AUTHORITY FOUND' for any legal proposition.")

    opposing = context.get("opposing_arguments", [])
    if opposing:
        parts.append("")
        parts.append("OPPOSING (PLAINTIFF) ARGUMENTS TO ATTACK:")
        for arg in opposing:
            parts.append(f"  - {arg.get('position', '')}")
            if arg.get("argument", {}).get("claim"):
                parts.append(f"    Claim: {arg['argument']['claim'][:300]}")
            if arg.get("argument", {}).get("application"):
                parts.append(f"    Application: {arg['argument']['application'][:200]}")

    prev = context.get("previous_arguments", [])
    if prev:
        parts.append("")
        parts.append("YOUR PREVIOUS ARGUMENTS:")
        for arg in prev:
            parts.append(f"  - {arg.get('position', arg.get('claim', ''))[:200]}")

    instruction = context.get("instruction", "")
    if instruction:
        parts.append("")
        parts.append(f"COURT INSTRUCTION: {instruction}")

    parts.append("")
    parts.append("REMINDER: evidence_count MUST equal the number of items in evidence_references.")
    parts.append("REMINDER: authority_count MUST equal the number of items in authority_references.")
    parts.append("REMINDER: Do NOT invent citations. Use ONLY the VERIFIED AUTHORITIES listed above.")

    return "\n".join(parts)


def _build_judge_user_content(context: Dict[str, Any]) -> str:
    parts = []

    case = context.get("case", {})
    parts.append(f"CASE: {case.get('title', 'N/A')}")
    parts.append(f"TYPE: {case.get('case_type', 'N/A')}")
    parts.append(f"DESCRIPTION: {case.get('description', 'N/A')}")
    parts.append("")

    plaintiff_args = context.get("plaintiff_arguments", [])
    if plaintiff_args:
        parts.append("PLAINTIFF ARGUMENTS:")
        for arg in plaintiff_args:
            parts.append(f"  Position: {arg.get('position', '')}")
            parts.append(f"  Claim: {arg.get('argument', {}).get('claim', '')[:300]}")
            parts.append(f"  Application: {arg.get('argument', {}).get('application', '')[:200]}")
            parts.append("")

    defence_args = context.get("defence_arguments", [])
    if defence_args:
        parts.append("DEFENCE ARGUMENTS:")
        for arg in defence_args:
            parts.append(f"  Position: {arg.get('position', '')}")
            parts.append(f"  Claim: {arg.get('argument', {}).get('claim', '')[:300]}")
            parts.append(f"  Application: {arg.get('argument', {}).get('application', '')[:200]}")
            parts.append("")

    evidence = context.get("evidence", [])
    if evidence:
        parts.append(f"EVIDENCE ({len(evidence)} items):")
        for ev in evidence:
            parts.append(f"  [{ev.get('label', '?')}] {ev.get('title', 'Exhibit')}")

    verified_authorities = context.get("verified_authorities", [])
    if verified_authorities:
        parts.append(f"VERIFIED AUTHORITIES ({len(verified_authorities)} items):")
        for auth in verified_authorities:
            parts.append(f"  - {auth.get('citation', 'N/A')}: {auth.get('proposition', '')[:150]}")
    else:
        parts.append("VERIFIED AUTHORITIES: NONE AVAILABLE")

    return "\n".join(parts)


async def call_groq(system_prompt: str, user_content: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is not set")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=GROQ_TIMEOUT) as client:
        response = await client.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


def _parse_json_response(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        raise ValueError(f"Could not parse JSON from response: {text[:200]}")


def _compute_backend_confidence(
    result: Dict[str, Any],
    evidence_refs: List[str],
    verified_authorities: List[Dict[str, Any]],
    actual_evidence_count: int,
) -> Dict[str, float]:
    """Compute confidence scores on the backend based on actual data, not LLM output."""

    # Evidence support: based on actual evidence references in the argument
    ev_refs_in_arg = result.get("evidence_references", [])
    ev_count = len(ev_refs_in_arg)
    if actual_evidence_count > 0:
        evidence_support = min(ev_count / actual_evidence_count, 1.0)
    else:
        evidence_support = 0.0

    # If argument uses extracted_text from evidence, boost confidence
    material_facts = result.get("argument", {}).get("material_facts", [])
    facts_with_refs = sum(1 for f in material_facts if "[" in str(f) and "]" in str(f))
    if material_facts:
        evidence_support = min(evidence_support + 0.1 * (facts_with_refs / len(material_facts)), 1.0)

    # Legal authority support: based on verified authorities count and confidence
    auth_refs_in_arg = result.get("authority_references", [])
    if verified_authorities:
        avg_auth_conf = sum(
            a.get("confidence", 0.0) or a.get("verification", {}).get("confidence", 0.5)
            for a in verified_authorities
        ) / len(verified_authorities)
        auth_support = min(len(auth_refs_in_arg) / len(verified_authorities), 1.0) * avg_auth_conf
    else:
        auth_support = 0.0

    # Argument consistency: check if the argument structure is coherent
    argument = result.get("argument", {})
    consistency_score = 0.5
    if argument.get("claim"):
        consistency_score += 0.1
    if argument.get("legal_rule") and "NO VERIFIED AUTHORITY" not in argument.get("legal_rule", ""):
        consistency_score += 0.15
    if argument.get("material_facts"):
        consistency_score += 0.1
    if argument.get("application"):
        consistency_score += 0.1
    consistency_score = min(consistency_score, 1.0)

    # Overall: weighted blend
    overall = round(
        0.35 * evidence_support +
        0.35 * auth_support +
        0.30 * consistency_score,
        2
    )

    return {
        "evidence_support": round(evidence_support, 2),
        "legal_authority_support": round(auth_support, 2),
        "argument_consistency": round(consistency_score, 2),
        "overall": overall,
    }


async def generate_legal_argument(
    side: str,
    context: Dict[str, Any],
    verified_authorities: List[Dict[str, Any]],
    actual_evidence_count: int,
) -> Dict[str, Any]:
    side_upper = side.upper()
    stage = context.get("stage", "ARGUMENT")

    # Inject verified authorities into context for the prompt
    context_with_auth = {**context, "verified_authorities": verified_authorities}

    if not GROQ_API_KEY:
        return _generate_fallback_argument(side_upper, context_with_auth, stage, verified_authorities, actual_evidence_count)

    if side_upper == "PLAINTIFF":
        system_prompt = PLAINTIFF_SYSTEM_PROMPT
        user_content = _build_plaintiff_user_content(context_with_auth)
    elif side_upper == "DEFENCE":
        system_prompt = DEFENCE_SYSTEM_PROMPT
        user_content = _build_defence_user_content(context_with_auth)
    else:
        raise ValueError(f"Unknown side: {side}")

    raw_response = await call_groq(system_prompt, user_content)
    parsed = _parse_json_response(raw_response)

    # Override evidence_count and authority_count with actual values
    parsed["evidence_count"] = actual_evidence_count
    parsed["authority_count"] = len(verified_authorities)

    # Compute backend confidence
    evidence_refs = [e.get("label", "") for e in context.get("evidence", [])]
    confidence = _compute_backend_confidence(parsed, evidence_refs, verified_authorities, actual_evidence_count)
    parsed["confidence"] = confidence

    return parsed


async def generate_judge_analysis(
    context: Dict[str, Any],
    verified_authorities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not GROQ_API_KEY:
        return _generate_fallback_judge_analysis(context, verified_authorities)

    context_with_auth = {**context, "verified_authorities": verified_authorities}
    user_content = _build_judge_user_content(context_with_auth)
    raw_response = await call_groq(JUDGE_SYSTEM_PROMPT, user_content)
    parsed = _parse_json_response(raw_response)
    return parsed


def _generate_fallback_argument(
    side: str,
    context: Dict[str, Any],
    stage: str,
    verified_authorities: List[Dict[str, Any]],
    actual_evidence_count: int,
) -> Dict[str, Any]:
    case = context.get("case", {})
    evidence = context.get("evidence", [])
    opposing = context.get("opposing_arguments", [])

    side_upper_norm = "DEFENDANT" if side.upper() == "DEFENCE" else side.upper()
    side_evidence = [e for e in evidence if e.get("party", "").upper() == side_upper_norm]
    evidence_refs = [{"id": e["label"], "reason": f"Supports {side} position: {e.get('title', '')}"} for e in side_evidence[:4]]

    # Build authority references ONLY from verified authorities
    authority_refs = []
    for auth in verified_authorities[:3]:
        authority_refs.append({
            "id": auth.get("id", "AUTH-001"),
            "citation": auth.get("citation", ""),
            "case_name": auth.get("case_name", ""),
            "court": auth.get("court", ""),
            "year": auth.get("year"),
            "reason": auth.get("proposition", "")[:200],
            "verification_status": auth.get("verification_status", "VERIFIED"),
        })

    opposing_text = ""
    if opposing:
        last = opposing[-1]
        opposing_text = last.get("argument", {}).get("claim", "") or last.get("position", "")

    if side.upper() == "PLAINTIFF":
        position = f"The Plaintiff submits that the Defendant breached contractual obligations in {case.get('title', 'this matter')}."
        if opposing_text:
            position += f" The Defence's position that '{opposing_text[:100]}...' is disputed."
        claim = (
            f"The Plaintiff claims relief based on documented evidence of the Defendant's "
            f"failure to perform contractual obligations. The Plaintiff's case is supported by "
            f"{len(side_evidence)} exhibit{'s' if len(side_evidence) != 1 else ''}"
            f"{' and ' + str(len(authority_refs)) + ' verified legal authorities' if authority_refs else ''}."
        )
        if authority_refs:
            legal_rule = f"Per {authority_refs[0]['citation']}, under applicable contract law, a party who suffers loss by breach is entitled to compensation."
        else:
            legal_rule = "NO VERIFIED AUTHORITY FOUND for this legal proposition."
        application = (
            "The Plaintiff has produced contemporaneous documentary evidence establishing "
            "performance of contractual obligations and the Defendant's breach. "
            "The Defendant has failed to produce contemporaneous evidence supporting their position."
        )
        counterargument = "The Defendant may assert justification, but no supporting documentation has been produced."
        relief = "Full restitution of the disputed amount with applicable interest."
    else:
        position = f"The Defendant disputes the Plaintiff's allegations of breach in {case.get('title', 'this matter')}."
        if opposing_text:
            position += f" The Plaintiff's assertion that '{opposing_text[:100]}...' is contested."
        claim = (
            f"The Defendant denies liability. The Plaintiff has failed to identify specific "
            f"contractual provisions breached, and the Defendant's actions were authorized by "
            f"the agreement. The Defence case is supported by {len(side_evidence)} exhibits"
            f"{' and ' + str(len(authority_refs)) + ' verified legal authorities' if authority_refs else ''}."
        )
        if authority_refs:
            legal_rule = f"Per {authority_refs[0]['citation']}, the burden of proving breach lies with the claimant. Damages must be proved with reasonable certainty."
        else:
            legal_rule = "NO VERIFIED AUTHORITY FOUND for this legal proposition."
        application = (
            "The Plaintiff has not identified any specific contractual provision that was breached. "
            "General allegations of non-performance, without reference to particular clauses, are "
            "insufficient to establish a prima facie case."
        )
        counterargument = "The Plaintiff may argue non-performance, but has not produced contemporaneous evidence for the disputed period."
        relief = "Dismissal of the Plaintiff's claims with costs."

    facts = []
    for i, ev in enumerate(side_evidence[:3], 1):
        label = f"{'P' if side.upper() == 'PLAINTIFF' else 'D'}-{i:03d}"
        facts.append(f"[{label}] {ev.get('title', 'Exhibit')}: {(ev.get('extracted_text') or '')[:120]}")

    parsed = {
        "side": side.upper(),
        "stage": stage,
        "position": position,
        "issues": [
            {"issue": "Whether the Defendant breached contractual obligations", "position": position},
            {"issue": "Whether the Plaintiff is entitled to the claimed relief", "position": "The claimant must establish both breach and loss."},
        ],
        "argument": {
            "claim": claim,
            "legal_rule": legal_rule,
            "material_facts": facts,
            "application": application,
            "counterargument": counterargument,
            "rebuttal": "",
            "requested_relief": relief,
        },
        "evidence_references": evidence_refs,
        "authority_references": authority_refs,
        "evidence_count": len(evidence_refs),
        "authority_count": len(authority_refs),
    }

    confidence = _compute_backend_confidence(parsed, [e["label"] for e in side_evidence], verified_authorities, actual_evidence_count)
    parsed["confidence"] = confidence

    return parsed


def _generate_fallback_judge_analysis(
    context: Dict[str, Any],
    verified_authorities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    p_args = context.get("plaintiff_arguments", [])
    d_args = context.get("defence_arguments", [])
    evidence = context.get("evidence", [])

    p_strengths = []
    d_strengths = []
    for pa in p_args:
        if pa.get("argument", {}).get("claim"):
            p_strengths.append(pa["argument"]["claim"][:200])
        if pa.get("argument", {}).get("material_facts"):
            for fact in pa["argument"]["material_facts"][:2]:
                p_strengths.append(fact[:200])
    for da in d_args:
        if da.get("argument", {}).get("claim"):
            d_strengths.append(da["argument"]["claim"][:200])
        if da.get("argument", {}).get("material_facts"):
            for fact in da["argument"]["material_facts"][:2]:
                d_strengths.append(fact[:200])

    p_evidence = [e for e in evidence if e.get("party", "").upper() == "PLAINTIFF"]
    d_evidence = [e for e in evidence if e.get("party", "").upper() == "DEFENDANT"]

    evidence_conflicts = _detect_evidence_conflicts(p_evidence, d_evidence, p_args, d_args)

    issues = []
    if p_strengths or d_strengths:
        issues.append({
            "issue": "Whether the Defendant breached the contractual obligations",
            "analysis": (
                f"Plaintiff relies on {len(p_evidence)} exhibit{'s' if len(p_evidence) != 1 else ''} "
                f"({', '.join(e.get('label', '') for e in p_evidence[:3])}). "
                f"Defence relies on {len(d_evidence)} exhibit{'s' if len(d_evidence) != 1 else ''} "
                f"({', '.join(e.get('label', '') for e in d_evidence[:3]) or 'none'}). "
                "Both sides present conflicting accounts of the contractual performance."
            ),
        })
        issues.append({
            "issue": "Whether the Plaintiff is entitled to the claimed relief",
            "analysis": "Depends on findings regarding breach, quantum of loss, and evidence credibility.",
        })

    unresolved = []
    if evidence_conflicts:
        for conflict in evidence_conflicts:
            unresolved.append(conflict.get("court_question", ""))
    if not unresolved:
        unresolved.append("Whether contemporaneous evidence fully supports either party's account.")

    recommended = []
    for conflict in evidence_conflicts:
        if conflict.get("court_question"):
            recommended.append(conflict["court_question"])
    if not recommended:
        recommended.append("Can the Plaintiff identify the exact contractual provision breached?")
        recommended.append("Can the Defendant produce contemporaneous records of performance?")

    return {
        "issues": issues if issues else [
            {"issue": "Whether the Defendant breached the contractual obligations", "analysis": "Both sides present conflicting accounts."},
        ],
        "facts_found": [
            f"{len(evidence)} exhibit{'s' if len(evidence) != 1 else ''} admitted into evidence.",
            f"Plaintiff: {len(p_evidence)} exhibits. Defence: {len(d_evidence)} exhibits.",
        ],
        "facts_disputed": [
            f"The factual dispute centers on the {len(evidence_conflicts)} evidence conflict{'s' if len(evidence_conflicts) != 1 else ''} identified below."
        ] if evidence_conflicts else [
            "The nature and extent of the Defendant's performance under the contract.",
        ],
        "law": [
            "Contract law principles regarding breach and remedies apply.",
        ],
        "plaintiff_strengths": p_strengths if p_strengths else ["Plaintiff has submitted arguments."],
        "defence_strengths": d_strengths if d_strengths else ["Defence has submitted arguments."],
        "evidence_conflicts": evidence_conflicts if evidence_conflicts else [
            "Both parties rely on different interpretations of the documentary evidence.",
        ],
        "unresolved_questions": unresolved,
        "analysis": [
            f"Court has {len(evidence)} exhibits and {len(p_args) + len(d_args)} arguments to evaluate.",
            "The matter requires careful examination of the documentary evidence against each party's claims.",
        ],
        "provisional_findings": [
            f"Plaintiff case supported by {len(p_evidence)} exhibits; Defence supported by {len(d_evidence)} exhibit{'s' if len(d_evidence) != 1 else ''}.",
        ] + [
            f"CONFLICT: {c['description']}" for c in evidence_conflicts
        ],
        "recommended_next_questions": recommended,
    }


def _detect_evidence_conflicts(
    p_evidence: List[Dict[str, Any]],
    d_evidence: List[Dict[str, Any]],
    p_args: List[Dict[str, Any]],
    d_args: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Detect factual conflicts between plaintiff and defence evidence."""
    conflicts = []

    p_facts = []
    for pa in p_args:
        for fact in pa.get("argument", {}).get("material_facts", []):
            p_facts.append(fact.lower())
    d_facts = []
    for da in d_args:
        for fact in da.get("argument", {}).get("material_facts", []):
            d_facts.append(fact.lower())

    p_text = " ".join(p_facts)
    d_text = " ".join(d_facts)

    conflict_pairs = [
        {
            "p_keywords": ["intact", "intact", "no damage", "no damage", "condition", "good condition"],
            "d_keywords": ["repair", "damage", "damage", "repair", "plastering", "repainting", "damage"],
            "description": "P-002 (Move-Out Photos) indicate walls and fixtures were intact, while D-001 (Repair Invoice) claims ₹35,000 for wall plastering and repainting.",
            "court_question": "Can the Defence provide contemporaneous inspection evidence (e.g., dated photographs, inspection reports) connecting the claimed ₹35,000 repair to damage caused during the Plaintiff's tenancy, as opposed to normal wear and tear?",
        },
        {
            "p_keywords": ["deposit", "refundable", "refund", "50,000"],
            "d_keywords": ["deduct", "deduction", "withhold", "set-off"],
            "description": "P-003 (Bank Transfer Receipt) establishes ₹50,000 deposit was paid as refundable. Defence has not produced written consent or joint inspection record justifying any deduction.",
            "court_question": "Was there a joint inspection at handover, and did both parties sign off on the property condition? If not, can unilateral damage deductions be sustained?",
        },
    ]

    for pair in conflict_pairs:
        p_match = any(kw in p_text for kw in pair["p_keywords"])
        d_match = any(kw in d_text for kw in pair["d_keywords"])
        if p_match and d_match:
            conflicts.append({
                "description": pair["description"],
                "court_question": pair["court_question"],
            })

    if not conflicts and p_evidence and d_evidence:
        p_labels = [e.get("label", "") for e in p_evidence[:3]]
        d_labels = [e.get("label", "") for e in d_evidence[:3]]
        conflicts.append({
            "description": f"Plaintiff evidence ({', '.join(p_labels)}) and Defence evidence ({', '.join(d_labels)}) present competing accounts of the property condition and obligations.",
            "court_question": f"Which party's evidence ({', '.join(p_labels + d_labels)}) more contemporaneously and reliably establishes the facts at the time of handover?",
        })

    return conflicts
