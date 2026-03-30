from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers import sidecar_provider as sidecar_provider_controller


PROVIDER_ID = "autofigure_edit"


def recommend_autofigure_edit_sidecar(
    *,
    quest_root: Path,
    payload: dict[str, object],
    figure_id: str | None = None,
) -> dict[str, object]:
    return sidecar_provider_controller.recommend_sidecar(
        quest_root=quest_root,
        provider_id=PROVIDER_ID,
        payload=payload,
        instance_id=figure_id,
    )


def provision_autofigure_edit_sidecar(
    *,
    quest_root: Path,
    payload: dict[str, object],
    figure_id: str | None = None,
) -> dict[str, object]:
    return sidecar_provider_controller.provision_sidecar(
        quest_root=quest_root,
        provider_id=PROVIDER_ID,
        payload=payload,
        instance_id=figure_id,
    )


def import_autofigure_edit_sidecar_result(
    *,
    quest_root: Path,
    figure_id: str,
) -> dict[str, object]:
    return sidecar_provider_controller.import_sidecar_result(
        quest_root=quest_root,
        provider_id=PROVIDER_ID,
        instance_id=figure_id,
    )


def resolve_autofigure_edit_sidecar_artifacts(
    *,
    quest_root: Path,
    figure_id: str,
) -> dict[str, object]:
    return sidecar_provider_controller.resolve_sidecar_artifacts(
        quest_root=quest_root,
        provider_id=PROVIDER_ID,
        instance_id=figure_id,
    )
