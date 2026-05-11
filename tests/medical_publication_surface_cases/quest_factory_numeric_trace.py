from __future__ import annotations

from pathlib import Path

from .shared_base import dump_json


def write_numeric_trace_fixture(paper_root: Path) -> None:
    dump_json(
        paper_root / "numeric_trace.json",
        {
            "schema_version": 1,
            "traces": [
                {
                    "trace_id": "NT1",
                    "claim_id": "C1",
                    "reported_value": "n=312",
                    "statistic_kind": "sample_size",
                    "source_paths": ["paper/tables/T1_baseline.csv"],
                    "source_field": "baseline.n",
                    "rounding_rule": "integer_count_no_rounding",
                    "manuscript_refs": ["results:threshold-interpretation"],
                    "verification_status": "verified",
                    "evidence_refs": ["EXP-001"],
                }
            ],
        },
    )
