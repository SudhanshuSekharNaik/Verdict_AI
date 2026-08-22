from typing import List, Optional
from models.schemas import CaseDetail, Case
from services import database

# Persistent SQLite store
def save(case: Case) -> None:
    # database is updated via specific entity functions or state updates
    database.update_case_state(
        case.id,
        status=case.status,
        current_stage=case.current_stage,
        current_speaker=case.current_speaker,
        current_round=case.current_round,
    )


def get(case_id: str) -> Optional[CaseDetail]:
    return database.get_case_by_id(case_id)


def list_all(status_filter: Optional[str] = None) -> List[CaseDetail]:
    return database.list_all_cases(status_filter)


def list_pending() -> List[CaseDetail]:
    return database.list_pending_cases()
