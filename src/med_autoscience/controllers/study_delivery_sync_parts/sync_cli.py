from __future__ import annotations

import argparse
from pathlib import Path

from .staging_and_sources import SYNC_STAGES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync finalized paper deliverables into the study shallow path.")
    parser.add_argument("--paper-root", type=Path, required=True)
    parser.add_argument("--stage", choices=SYNC_STAGES, required=True)
    parser.add_argument("--publication-profile", default="general_medical_journal")
    parser.add_argument("--promote-to-final", action="store_true")
    return parser.parse_args()


def main() -> int:
    from .sync_orchestration import sync_study_delivery

    args = parse_args()
    sync_study_delivery(
        paper_root=args.paper_root,
        stage=args.stage,
        publication_profile=args.publication_profile,
        promote_to_final=args.promote_to_final,
    )
    return 0
