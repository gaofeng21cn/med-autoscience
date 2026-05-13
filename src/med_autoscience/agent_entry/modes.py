from __future__ import annotations

from pathlib import Path

from med_autoscience.stage_route_contract import (
    StageEntryMode,
    load_stage_route_contract,
    load_stage_route_contract_payload,
    stage_entry_modes_from_payload,
)

EntryMode = StageEntryMode


def load_entry_modes_payload(path: Path | None = None) -> dict[str, object]:
    return load_stage_route_contract_payload(path=path)


def load_entry_modes() -> tuple[EntryMode, ...]:
    return stage_entry_modes_from_payload(load_entry_modes_payload())
