from __future__ import annotations

import argparse


def register_paper_mission_parsers(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("paper-mission")
    mission_subparsers = parser.add_subparsers(dest="paper_mission_command", required=True)

    inspect_parser = mission_subparsers.add_parser("inspect")
    _add_common_args(inspect_parser)
    inspect_parser.add_argument("--one-shot-migration", action="store_true")
    inspect_parser.add_argument("--study-progress-payload")
    inspect_parser.add_argument("--runtime-readback-payload", dest="runtime_readback_payload")
    inspect_parser.add_argument("--output-root")
    inspect_parser.add_argument("--request-opl-runtime-readback", action="store_true")

    package_parser = mission_subparsers.add_parser("package-candidate")
    _add_common_args(package_parser)
    package_parser.add_argument("--output-root", required=True)
    package_parser.add_argument("--paper-facing-delta-ref")

    drive_parser = mission_subparsers.add_parser("drive")
    _add_common_args(drive_parser)
    drive_parser.add_argument("--run-id")
    drive_parser.add_argument("--output-root")
    drive_parser.add_argument(
        "--submit-opl-runtime",
        dest="submit_opl_runtime",
        action="store_true",
        default=None,
    )
    drive_parser.add_argument(
        "--no-submit-opl-runtime",
        dest="submit_opl_runtime",
        action="store_false",
    )
    drive_parser.add_argument("--opl-bin")

    terminalize_parser = mission_subparsers.add_parser("terminalize-stage")
    _add_common_args(terminalize_parser)
    terminalize_parser.add_argument("--stage-packet")
    terminalize_parser.add_argument("--output-root")
    terminalize_parser.add_argument("--dry-run", action="store_true")

    start_parser = mission_subparsers.add_parser("start")
    _add_common_args(start_parser)
    start_parser.add_argument("--objective")
    _add_dry_run_only(start_parser)

    resume_parser = mission_subparsers.add_parser("resume")
    _add_common_args(resume_parser)
    resume_parser.add_argument("--mission-id")
    _add_dry_run_only(resume_parser)

    consume_parser = mission_subparsers.add_parser("consume-candidate")
    _add_common_args(consume_parser)
    consume_parser.add_argument("--candidate")
    consume_mode = consume_parser.add_mutually_exclusive_group(required=True)
    consume_mode.add_argument("--dry-run", action="store_true")
    consume_mode.add_argument("--output-root")

    receipt_parser = mission_subparsers.add_parser("receipt-owner-consumption")
    _add_common_args(receipt_parser)
    receipt_parser.add_argument("--paper-mission-readback-file", required=True)
    receipt_parser.add_argument("--output-root")
    receipt_apply = receipt_parser.add_mutually_exclusive_group()
    receipt_apply.add_argument("--apply-typed-blocker", action="store_true")
    receipt_apply.add_argument("--apply-route-checkpoint", action="store_true")

    typed_resolution_parser = mission_subparsers.add_parser("typed-blocker-resolution")
    _add_common_args(typed_resolution_parser)
    typed_resolution_parser.add_argument("--paper-mission-readback-file", required=True)
    typed_resolution_parser.add_argument("--output-root")
    typed_resolution_apply = typed_resolution_parser.add_mutually_exclusive_group()
    typed_resolution_apply.add_argument("--apply-owner-decision", action="store_true")
    typed_resolution_apply.add_argument("--apply-human-gate", action="store_true")
    typed_resolution_apply.add_argument("--apply-route-redesign", action="store_true")


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", required=True)
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--format", choices=("json",), default="json")


def _add_dry_run_only(parser: argparse.ArgumentParser) -> None:
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")


__all__ = ["register_paper_mission_parsers"]
