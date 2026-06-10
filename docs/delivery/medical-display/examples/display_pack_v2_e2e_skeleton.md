# Display Pack v2 E2E Skeleton

Owner: `MedAutoScience`
Purpose: `display_pack_v2_minimal_e2e_example`
State: `documentation_example`
Machine boundary: 人读字段关系示例。这里的 payload 片段不是 fixture、golden、真实论文证据、测试输入或 publication authority；真实验证继续归 contracts、source validators、paper artifact refs、lock、submission manifest 和 owner receipts。

本示例展示 evidence figure 从 Display Pack descriptor 到 paper-level quality refs 的最小关系。医学论文 evidence figure 的推荐 renderer family 是 R/ggplot2；`python_plugin` 仍可用于 MAS host-native renderer、轻量 fixture 或内部 materializer。

## 1. Pack Descriptor

`display_pack.toml`

```toml
pack_id = "fenggaolab.org.medical-display-core"
version = "0.2.0"
display_api_version = "1"
source = "repo-local display pack"
owner = "MedAutoScience"
license = "internal-use"

templates = ["roc_curve_binary"]
style_profiles = ["publication_default"]
qc_profiles = ["publication_evidence_curve"]
ai_policy = "ai_visual_audit_only_no_claim_carriage"
goldens = ["templates/roc_curve_binary/goldens/minimal"]
exemplars = ["link-only:paperplot-example"]
provenance = ["contract:display-pack-contract.v2"]

[opl_handoff]
status = "handoff_tail"
tail_status = "opl_pack_os_substrate_landed_external"
target_owner = "OPL Pack OS"

[opl_handoff.external_opl_consumer]
status = "landed_in_opl_repo"
owner_repo = "one-person-lab"
surface = "opl pack os mas-display-smoke"
command = "opl pack os mas-display-smoke --contract <mas_repo>/contracts/display-pack-contract.v2.json --json"
verification_refs = [
  "one-person-lab:src/pack-os.ts",
  "one-person-lab:tests/src/pack-os.test.ts",
  "one-person-lab:tests/src/cli/cases/pack-os-command-surface.test.ts",
]
boundary = "OPL consumer smoke preserves MAS authority and does not land publication authority inside MAS."

[opl_handoff.external_opl_pack_os_substrate]
status = "landed_in_opl_repo"
owner_repo = "one-person-lab"
contract_ref = "one-person-lab:contracts/opl-framework/pack-os-contract.json"
cli_surfaces = [
  "opl pack os install",
  "opl pack os registry",
  "opl pack os cache",
  "opl pack os distribute",
  "opl pack os lock",
  "opl pack os validate",
  "opl pack os mas-display-smoke",
]
verification_refs = [
  "one-person-lab:src/pack-os.ts",
  "one-person-lab:src/pack-os-contract.ts",
  "one-person-lab:contracts/opl-framework/pack-os-contract.json",
  "one-person-lab:tests/src/pack-os.test.ts",
  "one-person-lab:tests/src/cli/cases/pack-os-command-surface.test.ts",
]
boundary = "OPL owns generic Pack OS substrate; MAS only records refs-only handoff and forbidden-authority boundaries."
```

## 2. Template Descriptor

`templates/roc_curve_binary/template.toml`

```toml
template_id = "roc_curve_binary"
full_template_id = "fenggaolab.org.medical-display-core::roc_curve_binary"
kind = "evidence_figure"
display_name = "ROC Curve"
paper_family_ids = ["A"]
audit_family = "Prediction Performance"
renderer_family = "r_ggplot2"
input_schema_ref = "binary_prediction_curve_inputs_v1"
qc_profile_ref = "publication_evidence_curve"
style_profile_ref = "publication_default"
required_exports = ["png", "pdf"]
execution_mode = "subprocess"
entrypoint = "Rscript render.R --request {request_json}"
paper_proven = false
golden_case_paths = ["templates/roc_curve_binary/goldens/minimal"]
exemplar_refs = ["link-only:paperplot-example"]
```

Python plugin 模板使用同一 descriptor contract，但只作为 host-native 兼容路径：

```toml
template_id = "roc_curve_binary_python"
full_template_id = "fenggaolab.org.medical-display-core::roc_curve_binary_python"
kind = "evidence_figure"
display_name = "ROC Curve (Python plugin compatibility)"
paper_family_ids = ["A"]
audit_family = "Prediction Performance"
renderer_family = "python"
input_schema_ref = "binary_prediction_curve_inputs_v1"
qc_profile_ref = "publication_evidence_curve"
style_profile_ref = "publication_default"
required_exports = ["png", "pdf"]
execution_mode = "python_plugin"
entrypoint = "med_autoscience.display_pack_core:render"
paper_proven = false
```

subprocess renderer 通过 `{request_json}` 接收 JSON render request。同一路径也会写入环境变量 `MAS_DISPLAY_RENDER_REQUEST`；必需输出在 request 中是 `output_png_path`、`output_pdf_path`、`layout_sidecar_path`，同时也通过 `MAS_DISPLAY_OUTPUT_PNG`、`MAS_DISPLAY_OUTPUT_PDF`、`MAS_DISPLAY_LAYOUT_SIDECAR` 暴露。runtime 不通过 shell 执行 entrypoint，会记录 request/stdout/stderr refs，并在 deterministic QC 前强制要求 PNG、PDF 和 layout sidecar 都已写出。

## 3. Paper Intent

`paper/figure_intent.json`

```json
{
  "schema_version": 1,
  "figures": [
    {
      "figure_id": "F1",
      "claim_ref": "claim:primary-discrimination",
      "data_ref": "paper/data/frozen/primary_roc.json",
      "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
      "figure_kind": "evidence_figure"
    }
  ]
}
```

## 4. Medical Figure Spec

`paper/figure_spec.json`

```json
{
  "schema_version": 1,
  "figure_id": "F1",
  "intent_ref": "paper/figure_intent.json#/figures/F1",
  "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
  "figure_kind": "evidence_figure",
  "medical_semantics": {
    "cohort_ref": "study/cohorts/validation",
    "endpoint_ref": "endpoint:mace",
    "model_ref": "model:primary",
    "risk_horizon": "5y",
    "claim_role": "primary_evidence"
  },
  "panels": [
    {
      "panel_id": "A",
      "data_role": "discrimination",
      "mark_role": "roc_curve"
    }
  ]
}
```

多图批量物化使用 `paper/figure_specs.json`：

```json
{
  "schema_version": 1,
  "figures": [
    {
      "figure_id": "F1",
      "intent_ref": "paper/figure_intent.json#/figures/F1",
      "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
      "figure_kind": "evidence_figure",
      "medical_semantics": {
        "cohort_ref": "study/cohorts/validation",
        "endpoint_ref": "endpoint:mace",
        "model_ref": "model:primary",
        "risk_horizon": "5y",
        "claim_role": "primary_evidence"
      }
    },
    {
      "figure_id": "F2",
      "intent_ref": "paper/figure_intent.json#/figures/F2",
      "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary_ggplot2",
      "figure_kind": "evidence_figure",
      "medical_semantics": {
        "cohort_ref": "study/cohorts/external_validation",
        "endpoint_ref": "endpoint:mace",
        "model_ref": "model:primary",
        "risk_horizon": "5y",
        "claim_role": "secondary_evidence"
      }
    }
  ]
}
```

`paper/figure_spec.json` 继续作为单图兼容面。存在 `figure_specs.json` 时，`medautosci publication display-pack-e2e` 默认物化其中所有 figure；可重复传 `--figure-id <id>` 选择子集。

## 5. Visual Audit Receipt

`paper/figure_visual_audit_receipt.json`

```json
{
  "schema_version": 1,
  "receipt_id": "visual-audit-F1-20260610",
  "audit_mode": "vlm_visual_verification",
  "inspected_artifacts": [
    {
      "figure_id": "F1",
      "artifact_path": "paper/figures/generated/F1.png",
      "artifact_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ],
  "findings": [
    {
      "figure_id": "F1",
      "observed_issue": "Legend competes with the curve annotation in the upper left panel area.",
      "paper_facing_impact": "The primary discrimination result is harder to read in manuscript layout.",
      "suspected_layer": ["layout_qc", "publication_style_profile"],
      "proposed_action": "Move the legend outside the plotting area and rerun layout QC.",
      "promotion_decision": "promote_to_qc",
      "verification_plan": "Rerender F1, rerun publication_evidence_curve QC, and re-audit the PNG."
    }
  ],
  "reviewer": {
    "provider": "openai",
    "model": "gpt-5-vlm",
    "prompt_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  },
  "final_status": "findings_open"
}
```

## 6. AI/VLM Polish Lifecycle

`paper/figure_polish_lifecycle.json`

```json
{
  "schema_version": 1,
  "lifecycle_id": "fig-F1-polish",
  "relationship_refs": {
    "figure_visual_audit_receipt": "paper/figure_visual_audit_receipt.json",
    "display_pack_lock_publication_figure_quality_refs": "paper/build/display_pack_lock.json#/publication_figure_quality_refs"
  },
  "events": [
    {
      "state": "draft_rendered",
      "figure_id": "F1",
      "artifact_ref": "paper/figures/generated/F1.png",
      "actor": "display_pack_builder",
      "evidence_ref": "paper/build/display_pack_lock.json"
    },
    {
      "state": "deterministic_qc_clear",
      "figure_id": "F1",
      "artifact_ref": "paper/figures/generated/F1.png",
      "actor": "deterministic_qc",
      "evidence_ref": "paper/qc/F1.layout.json"
    },
    {
      "state": "visual_audit_findings",
      "figure_id": "F1",
      "artifact_ref": "paper/figures/generated/F1.png",
      "actor": "vlm_visual_auditor",
      "evidence_ref": "paper/figure_visual_audit_receipt.json",
      "model_ref": "openai:gpt-5-vlm:2026-06-10"
    }
  ]
}
```

The lifecycle is allowed to stop at any ordered prefix. It cannot skip from `draft_rendered` to `visual_audit_findings`, and `publication_manifested` requires prior `audit_clear`.

## 7. Lock And Submission Preservation

`paper/build/display_pack_lock.json` records pack source/version/hash plus:

```json
{
  "publication_figure_quality_refs": {
    "figure_intent": {
      "path": "paper/figure_intent.json",
      "status": "present",
      "sha256": "<sha256>"
    },
    "medical_figure_spec": {
      "path": "paper/figure_spec.json",
      "status": "present",
      "sha256": "<sha256>"
    },
    "medical_figure_specs": {
      "path": "paper/figure_specs.json",
      "status": "missing"
    },
    "figure_visual_audit_receipt": {
      "path": "paper/figure_visual_audit_receipt.json",
      "status": "present",
      "sha256": "<sha256>"
    },
    "figure_polish_lifecycle": {
      "path": "paper/figure_polish_lifecycle.json",
      "status": "present",
      "sha256": "<sha256>"
    },
    "ai_illustration_receipt": {
      "path": "paper/ai_illustration_receipt.json",
      "status": "missing"
    }
  }
}
```

`paper/submission_minimal/submission_manifest.json` preserves the same refs block. Preservation is audit evidence only; MAS owner receipt, independent reviewer/auditor and publication gate still decide publication readiness.
