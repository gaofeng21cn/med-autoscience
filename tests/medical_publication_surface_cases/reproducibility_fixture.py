from __future__ import annotations

from pathlib import Path

from .shared_base import dump_json


def write_reproducibility_supplement_fixture(paper_root: Path, *, missing_data_policy_id: str) -> None:
    dump_json(
        paper_root / "manuscript_safe_reproducibility_supplement.json",
        {
            "schema_version": 1,
            "software_versions": [
                {"package": "python", "version": "3.12"},
                {"package": "scikit-learn", "version": "1.5.0"},
            ],
            "random_seed_policy": "Fixed seeds across repeated nested validation with the manifest recorded in the experiment package.",
            "key_hyperparameters": [
                {"model_id": "M1", "parameters": {"max_depth": 3, "learning_rate": 0.05}}
            ],
            "missing_data_strategy": "Median imputation plus missingness indicators where prespecified.",
            "missing_data_policy_id": missing_data_policy_id,
            "metric_definitions": [
                {"metric": "AUC", "definition": "Area under the ROC curve."},
                {"metric": "Net benefit", "definition": "Decision-curve net benefit across prespecified thresholds."},
            ],
        },
    )
