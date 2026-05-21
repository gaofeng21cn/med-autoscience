from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def handle_stage_memory_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    stage_knowledge_plane: Any,
    publication_route_memory_inventory: Any,
    real_paper_autonomy_soak_inventory: Any,
    load_json_object_file: Any,
) -> int | None:
    if args.command == "publication-route-memory-apply-seed":
        if args.seed_library:
            result = stage_knowledge_plane.apply_publication_route_memory_seed_library(
                workspace_root=Path(args.workspace_root),
                seed_library_path=Path(args.seed_library),
                apply=bool(args.apply),
            )
        else:
            result = stage_knowledge_plane.apply_publication_route_memory_seed_fixture(
                workspace_root=Path(args.workspace_root),
                seed_fixture_path=Path(args.seed_fixture),
                apply=bool(args.apply),
            )
        _print_json(result)
        return 0

    if args.command == "publication-route-memory-inventory":
        result = publication_route_memory_inventory.build_publication_route_memory_inventory(
            workspace_root=Path(args.workspace_root),
            stage=args.stage,
            route_family_tags=args.route_families,
            statuses=args.statuses,
            include_card_body=bool(args.include_card_body),
        )
        _print_json(result)
        return 0

    if args.command == "stage-knowledge-packet":
        result = stage_knowledge_plane.materialize_stage_knowledge_packet(
            study_id=args.study_id,
            stage=args.stage,
            study_root=Path(args.study_root),
            workspace_root=Path(args.workspace_root),
            quest_root=Path(args.quest_root) if args.quest_root else None,
        )
        _print_json(result)
        return 0

    if args.command == "stage-memory-closeout-route":
        if args.closeout_packet:
            closeout_packet = load_json_object_file(args.closeout_packet)
            closeout_packet_ref = str(Path(args.closeout_packet))
        else:
            if not args.materialize_closeout_packet:
                parser.error("--closeout-payload requires --materialize-closeout-packet")
            if not args.study_id or not args.stage:
                parser.error("--closeout-payload requires --study-id and --stage")
            closeout_packet = stage_knowledge_plane.materialize_stage_memory_closeout_packet(
                study_id=args.study_id,
                stage=args.stage,
                study_root=Path(args.study_root),
                workspace_root=Path(args.workspace_root),
                closeout_payload=load_json_object_file(args.closeout_payload),
            )
            closeout_packet_ref = str(closeout_packet.get("artifact_path") or "")

        result = stage_knowledge_plane.route_stage_memory_closeout(
            closeout_packet=closeout_packet,
            study_root=Path(args.study_root),
            workspace_root=Path(args.workspace_root),
            apply=bool(args.apply),
        )
        if closeout_packet_ref:
            result = {**result, "closeout_packet_ref": closeout_packet_ref}
        _print_json(result)
        return 0

    if args.command == "paper-soak-memory-proof":
        result = stage_knowledge_plane.materialize_paper_soak_memory_apply_proof(
            study_id=args.study_id,
            stage=args.stage,
            study_root=Path(args.study_root),
            workspace_root=Path(args.workspace_root),
        )
        _print_json(result)
        return 0

    if args.command == "real-paper-autonomy-soak-projection":
        result = real_paper_autonomy_soak_inventory.build_real_paper_autonomy_soak_projection(
            yang_root=Path(args.yang_root),
            profile_paths=[Path(path) for path in args.profiles] if args.profiles else None,
            target_studies=tuple(args.target_studies or ("DM002", "DM003", "Obesity")),
        )
        _print_json(result)
        return 0

    if args.command == "real-paper-autonomy-provider-hosted-paper-proof":
        result = real_paper_autonomy_soak_inventory.build_real_paper_autonomy_provider_hosted_paper_proof(
            yang_root=Path(args.yang_root),
            profile_paths=[Path(path) for path in args.profiles] if args.profiles else None,
            target_studies=tuple(args.target_studies or ("DM002", "DM003", "Obesity")),
        )
        _print_json(result)
        return 0

    if args.command == "real-paper-autonomy-guarded-apply-proof":
        result = real_paper_autonomy_soak_inventory.build_real_paper_autonomy_guarded_apply_proof(
            yang_root=Path(args.yang_root),
            profile_paths=[Path(path) for path in args.profiles] if args.profiles else None,
            target_studies=tuple(args.target_studies or ("DM002", "DM003", "Obesity")),
        )
        _print_json(result)
        return 0

    return None


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_stage_memory_command"]
