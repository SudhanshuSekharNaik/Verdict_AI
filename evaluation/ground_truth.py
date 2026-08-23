import json
from pathlib import Path
from typing import Any, Dict, List


class GroundTruthBenchmark:
    """Loads benchmark ground truth data for the 5 demo cases."""

    @staticmethod
    def load_all_benchmarks() -> List[Dict[str, Any]]:
        cases_dir = Path(__file__).resolve().parents[1] / "cases"
        benchmarks = []

        for case_folder in sorted(cases_dir.glob("case_*")):
            gt_file = case_folder / "ground_truth.json"
            meta_file = case_folder / "case_metadata.json"
            if gt_file.exists() and meta_file.exists():
                try:
                    gt_data = json.loads(gt_file.read_text(encoding="utf-8"))
                    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
                    benchmarks.append({
                        "case_folder": case_folder.name,
                        "metadata": meta_data,
                        "ground_truth": gt_data,
                    })
                except Exception:
                    pass
        return benchmarks
