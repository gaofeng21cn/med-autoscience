from __future__ import annotations

import argparse


def register_product_entry_parsers(subparsers: argparse._SubParsersAction) -> None:
    product_frontdesk_parser = subparsers.add_parser("product-frontdesk")
    product_frontdesk_parser.add_argument("--profile", required=True)
    product_frontdesk_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    product_preflight_parser = subparsers.add_parser("product-preflight")
    product_preflight_parser.add_argument("--profile", required=True)
    product_preflight_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    product_start_parser = subparsers.add_parser("product-start")
    product_start_parser.add_argument("--profile", required=True)
    product_start_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    product_entry_manifest_parser = subparsers.add_parser("product-entry-manifest")
    product_entry_manifest_parser.add_argument("--profile", required=True)
    product_entry_manifest_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    skill_catalog_parser = subparsers.add_parser("skill-catalog")
    skill_catalog_parser.add_argument("--profile", required=True)
    skill_catalog_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    build_product_entry_parser = subparsers.add_parser("build-product-entry")
    build_product_entry_parser.add_argument("--profile", required=True)
    build_product_entry_parser.add_argument("--study-id", type=str)
    build_product_entry_parser.add_argument("--study-root", type=str)
    build_product_entry_parser.add_argument("--entry-mode", choices=("direct", "opl-handoff"), default="direct")
    build_product_entry_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    launch_study_parser = subparsers.add_parser("launch-study")
    launch_study_parser.add_argument("--profile", required=True)
    launch_study_parser.add_argument("--study-id", type=str)
    launch_study_parser.add_argument("--study-root", type=str)
    launch_study_parser.add_argument("--entry-mode", type=str)
    launch_study_parser.add_argument("--allow-stopped-relaunch", action="store_true")
    launch_study_parser.add_argument("--force", action="store_true")
    launch_study_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    submit_study_task_parser = subparsers.add_parser("submit-study-task")
    submit_study_task_parser.add_argument("--profile", required=True)
    submit_study_task_parser.add_argument("--study-id", type=str)
    submit_study_task_parser.add_argument("--study-root", type=str)
    submit_study_task_parser.add_argument("--task-intent", required=True)
    submit_study_task_parser.add_argument("--entry-mode", type=str)
    submit_study_task_parser.add_argument("--journal-target", type=str)
    submit_study_task_parser.add_argument("--constraint", action="append", default=[])
    submit_study_task_parser.add_argument("--evidence-boundary", action="append", default=[])
    submit_study_task_parser.add_argument("--trusted-input", action="append", default=[])
    submit_study_task_parser.add_argument("--reference-paper", action="append", default=[])
    submit_study_task_parser.add_argument("--first-cycle-output", action="append", default=[])
    submit_study_task_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
