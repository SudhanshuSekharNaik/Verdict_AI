from models.schemas import CaseDetail, Case
from orchestration import trial_orchestrator


def run_case(case: Case) -> CaseDetail:
    """
    Executes the full courtroom trial sequentially through the trial orchestrator state machine.
    Maintained for backward compatibility with existing batch runners.
    """
    return trial_orchestrator.execute_full_case_sync(case.id)
