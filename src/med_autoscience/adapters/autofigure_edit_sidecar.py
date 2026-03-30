from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.adapters import sidecar_provider as generic_adapter
from med_autoscience.sidecars import get_provider


PROVIDER_ID = "autofigure_edit"
DOMAIN_ID = "figures"


def sidecar_root(quest_root: Path, *, figure_id: str) -> Path:
    return generic_adapter.sidecar_root(quest_root, provider_id=PROVIDER_ID, instance_id=figure_id)


def handoff_root(quest_root: Path, *, figure_id: str) -> Path:
    return generic_adapter.handoff_root(quest_root, provider_id=PROVIDER_ID, instance_id=figure_id)


def artifact_root(quest_root: Path, *, figure_id: str) -> Path:
    return generic_adapter.artifact_root(
        quest_root,
        domain_id=DOMAIN_ID,
        provider_id=PROVIDER_ID,
        instance_id=figure_id,
    )


def dump_json(path: Path, payload: Any) -> None:
    generic_adapter.dump_json(path, payload)


def load_json(path: Path, default: Any = None) -> Any:
    return generic_adapter.load_json(path, default)


def build_contract_hash(payload: Mapping[str, Any]) -> str:
    return generic_adapter.build_contract_hash(payload)


def required_handoff_files() -> tuple[str, ...]:
    return get_provider(PROVIDER_ID).required_handoff_files


def copy_file(*, source: Path, destination: Path) -> None:
    generic_adapter.copy_file(source=source, destination=destination)
