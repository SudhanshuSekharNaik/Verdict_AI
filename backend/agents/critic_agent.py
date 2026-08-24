from typing import Any, Dict, List, Optional
from agents.base_agent import BaseCourtroomAgent


class CriticAgent(BaseCourtroomAgent):
    """
    Verification and fact-checking agent.
    Analyzes generated courtroom arguments to ensure strict grounding in the fact pattern
    and detects any self-contradictions across turns.
    """

    def __init__(self, title: str, facts: str, charge_or_dispute: str):
        system_prompt = f"""You are a strict LEGAL FACT-CHECKER and AUDITOR in a courtroom simulation called "{title}".

CANONICAL CASE FACTS (THE ONLY FACTS THAT EXIST):
{facts}

CHARGE / DISPUTE:
{charge_or_dispute}

YOUR TASK:
Analyze the proposed argument produced by counsel. Check for:
1. UNSUPPORTED CLAIMS / HALLUCINATIONS:
   - Did counsel state or assume as fact any item NOT in the record (e.g., invented fingerprints, DNA, internal room video, confessions, phone records, bank statements, extra witnesses)?
   - Note: Reasonable legal inferences from stated facts are acceptable, but asserting new unstated evidence as fact is NOT.
2. CONTRADICTIONS:
   - Does this argument contradict an earlier point made by the same speaker in prior rounds?

Return ONLY a JSON object:
{{
  "is_unsupported": <true|false>,
  "unsupported_note": "<brief note explaining unproven claim, or empty string>",
  "is_contradiction": <true|false>,
  "contradiction_note": "<brief note explaining contradiction, or empty string>",
  "should_regenerate": <true|false>,
  "feedback": "<instruction on what to remove/correct if should_regenerate is true>"
}}"""
        super().__init__(system_prompt)

    def check_argument(
        self,
        speaker: str,
        stage_name: str,
        argument_text: str,
        prior_speaker_arguments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Runs the verification check against the argument text."""
        prior_context = ""
        if prior_speaker_arguments:
            prior_context = f"\nPrior arguments by this same speaker ({speaker}):\n" + "\n---\n".join(
                prior_speaker_arguments
            )

        prompt = f"""Evaluate this proposed argument:
SPEAKER: {speaker.upper()}
STAGE: {stage_name}
ARGUMENT TEXT:
\"{argument_text}\"
{prior_context}

Perform your factual audit and return the specified JSON."""

        res = self.say_json(prompt, max_tokens=400, temperature=0.1)
        return {
            "is_unsupported": bool(res.get("is_unsupported", False)),
            "unsupported_note": str(res.get("unsupported_note", "") or ""),
            "is_contradiction": bool(res.get("is_contradiction", False)),
            "contradiction_note": str(res.get("contradiction_note", "") or ""),
            "should_regenerate": bool(res.get("should_regenerate", False)),
            "feedback": str(res.get("feedback", "") or ""),
        }
