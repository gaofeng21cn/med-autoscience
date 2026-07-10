from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.display_pack_contract import (
    load_display_pack_manifest,
    load_display_template_manifest,
)
from med_autoscience.display_pack_loader import (
    DisplayPackSourceConfig,
    LoadedDisplayTemplate,
)
from med_autoscience.display_pack_opl_adapter import (
    DESCRIPTOR_MEDIA_TYPE,
    build_display_pack_opl_adapter_contract,
    build_opl_generic_pack_descriptors,
    write_opl_generic_pack_descriptors,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "tests" / "fixtures" / "display_packs" / "minimal_valid_pack"


def _template_record() -> LoadedDisplayTemplate:
    pack_manifest = load_display_pack_manifest(PACK_ROOT / "display_pack.toml")
    template_path = PACK_ROOT / "templates" / "roc_curve_binary" / "template.toml"
    source = DisplayPackSourceConfig(
        pack_id=pack_manifest.pack_id,
        kind="local_dir",
        path=str(PACK_ROOT),
        package=None,
        pack_subdir=".",
        version=pack_manifest.version,
        source_owner="MAS Scholar Skills Display",
        source_ref="mas-scholar-skills:packs/medical-display-core",
        source_version=pack_manifest.version,
        source_role="generic_template_renderer_pack",
        source_authority=False,
        fallback=False,
        declared_in="test_fixture",
        config_path=PACK_ROOT / "display_pack.toml",
        resolved_source_root=PACK_ROOT,
        resolved_root=PACK_ROOT,
    )
    return LoadedDisplayTemplate(
        pack_root=PACK_ROOT,
        template_path=template_path,
        pack_manifest=pack_manifest,
        template_manifest=load_display_template_manifest(
            template_path,
            expected_pack_id=pack_manifest.pack_id,
        ),
        source_config=source,
    )


def test_display_pack_v2_adapter_emits_generic_opl_pack_descriptor() -> None:
    descriptor = build_opl_generic_pack_descriptors([_template_record()])[0]

    assert descriptor["surface_kind"] == "opl_generic_capability_pack_descriptor"
    assert descriptor["schema_version"] == 1
    assert descriptor["descriptor_media_type"] == DESCRIPTOR_MEDIA_TYPE
    assert descriptor["pack_kind"] == "display_pack"
    assert descriptor["capabilities"] == [
        {
            "capability_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
            "capability_kind": "evidence_figure",
            "entrypoint_ref": (
                "mas-scholar-skills:packs/medical-display-core/"
                "templates/roc_curve_binary/template.toml"
            ),
            "input_contract_ref": "mas-schema:binary_prediction_curve_inputs_v1",
            "output_contract_ref": "mas:contracts/publication_figure_quality_contract.json",
        }
    ]
    assert descriptor["review_transport"]["receipt_transport_only"] is True
    assert descriptor["authority_boundary"]["can_write_domain_truth"] is False
    assert descriptor["authority_boundary"]["can_authorize_visual_export_readiness"] is False


def test_display_pack_adapter_materializes_descriptor_for_generic_pack_os(tmp_path: Path) -> None:
    descriptor = build_opl_generic_pack_descriptors([_template_record()])[0]
    refs = write_opl_generic_pack_descriptors(
        descriptors=[descriptor],
        output_dir=tmp_path,
    )

    assert len(refs) == 1
    descriptor_path = Path(refs[0]["descriptor_ref"])
    assert descriptor_path.is_file()
    assert refs[0]["descriptor_media_type"] == DESCRIPTOR_MEDIA_TYPE
    assert json.loads(descriptor_path.read_text(encoding="utf-8")) == descriptor


def test_display_pack_adapter_contract_targets_only_generic_pack_os() -> None:
    contract = build_display_pack_opl_adapter_contract()

    assert contract["target_contract_ref"].endswith("pack-os-contract.json#descriptor_contract")
    assert contract["domain_action"] == "display-pack-capability-discover"
    assert contract["domain_action_output_field"] == "opl_pack_descriptor_refs"
    assert contract["authority_boundary"]["can_authorize_publication_readiness"] is False
