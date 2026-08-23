from typing import Any, Dict, List

from fastapi import APIRouter

from app.schemas.response import APIResponse
from evaluation.ground_truth import GroundTruthBenchmark
from evaluation.metrics import EvaluationEngine

router = APIRouter()


@router.get("/benchmarks", response_model=APIResponse[List[Dict[str, Any]]])
async def list_benchmarks():
    benchmarks = GroundTruthBenchmark.load_all_benchmarks()
    return APIResponse(success=True, data=benchmarks)


@router.post("/run", response_model=APIResponse[Dict[str, Any]])
async def run_evaluation_suite():
    results = EvaluationEngine.run_full_evaluation()
    return APIResponse(success=True, data=results)
