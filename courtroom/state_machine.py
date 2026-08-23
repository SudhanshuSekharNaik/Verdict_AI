import enum
from typing import List, Optional


class CourtStage(str, enum.Enum):
    CASE_OPENED = "CASE_OPENED"
    CASE_PREPARATION = "CASE_PREPARATION"
    EVIDENCE_SUBMISSION = "EVIDENCE_SUBMISSION"
    OPENING_ARGUMENTS = "OPENING_ARGUMENTS"
    PLAINTIFF_ARGUMENT = "PLAINTIFF_ARGUMENT"
    DEFENCE_ARGUMENT = "DEFENCE_ARGUMENT"
    CROSS_EXAMINATION = "CROSS_EXAMINATION"
    PLAINTIFF_REBUTTAL = "PLAINTIFF_REBUTTAL"
    DEFENCE_REBUTTAL = "DEFENCE_REBUTTAL"
    FINAL_SUBMISSIONS = "FINAL_SUBMISSIONS"
    JUDGE_QUESTIONS = "JUDGE_QUESTIONS"
    JUDGE_DELIBERATION = "JUDGE_DELIBERATION"
    VERDICT = "VERDICT"
    CASE_CLOSED = "CASE_CLOSED"


class CourtroomStateMachine:
    """Deterministic, rule-bound state machine for judicial simulation."""

    TRANSITIONS = {
        CourtStage.CASE_OPENED: [CourtStage.CASE_PREPARATION],
        CourtStage.CASE_PREPARATION: [CourtStage.EVIDENCE_SUBMISSION],
        CourtStage.EVIDENCE_SUBMISSION: [CourtStage.OPENING_ARGUMENTS],
        CourtStage.OPENING_ARGUMENTS: [CourtStage.PLAINTIFF_ARGUMENT],
        CourtStage.PLAINTIFF_ARGUMENT: [CourtStage.DEFENCE_ARGUMENT],
        CourtStage.DEFENCE_ARGUMENT: [CourtStage.CROSS_EXAMINATION, CourtStage.PLAINTIFF_REBUTTAL],
        CourtStage.CROSS_EXAMINATION: [CourtStage.PLAINTIFF_REBUTTAL, CourtStage.JUDGE_QUESTIONS],
        CourtStage.PLAINTIFF_REBUTTAL: [CourtStage.DEFENCE_REBUTTAL],
        CourtStage.DEFENCE_REBUTTAL: [CourtStage.FINAL_SUBMISSIONS, CourtStage.JUDGE_QUESTIONS],
        CourtStage.FINAL_SUBMISSIONS: [CourtStage.JUDGE_QUESTIONS, CourtStage.JUDGE_DELIBERATION],
        CourtStage.JUDGE_QUESTIONS: [CourtStage.JUDGE_DELIBERATION, CourtStage.FINAL_SUBMISSIONS],
        CourtStage.JUDGE_DELIBERATION: [CourtStage.VERDICT],
        CourtStage.VERDICT: [CourtStage.CASE_CLOSED],
        CourtStage.CASE_CLOSED: [],
    }

    @classmethod
    def can_transition(cls, current_stage: CourtStage, next_stage: CourtStage) -> bool:
        allowed = cls.TRANSITIONS.get(current_stage, [])
        return next_stage in allowed

    @classmethod
    def get_next_stage(cls, current_stage: CourtStage) -> Optional[CourtStage]:
        allowed = cls.TRANSITIONS.get(current_stage, [])
        return allowed[0] if allowed else None
