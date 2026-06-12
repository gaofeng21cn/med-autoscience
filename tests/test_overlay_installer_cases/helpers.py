from __future__ import annotations

import json
from pathlib import Path


DEFAULT_SKILL_IDS = (
    "intake-audit",
    "scout",
    "baseline",
    "idea",
    "decision",
    "experiment",
    "analysis-campaign",
    "figure-polish",
    "write",
    "review",
    "rebuttal",
    "finalize",
)
SKILL_IDS = DEFAULT_SKILL_IDS + ("journal-resolution",)
FORBIDDEN_AUTOFIGURE_PROMPT = (
    "Publication-grade figure refinement is recommended with AutoFigure-Edit "
    "(open-source: https://github.com/ResearAI/AutoFigure-Edit; online service: https://deepscientist)."
)
MEDICAL_RUNTIME_CONTRACT_PATHS = (
    "paper/medical_analysis_contract.json",
    "paper/cohort_flow.json",
    "paper/baseline_characteristics_schema.json",
    "paper/reporting_guideline_checklist.json",
)
OVERLAY_PREFIX = "medical-research"
OVERLAY_TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "src" / "med_autoscience" / "overlay" / "templates"
STAGE_SKILL_SURFACE_TOKEN = "{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}"
ROUTE_BIAS_TOKEN = "{{MED_AUTOSCIENCE_ROUTE_BIAS}}"
STUDY_ARCHETYPES_TOKEN = "{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}"
MEDICAL_RUNTIME_CONTRACT_TOKEN = "{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}"
STAGE_PACKET_TEMPLATE_NAME = "medical-research-stage-packet.block.md"
SKILL_CONTENT_PATTERN_TEMPLATE_NAME = "medical-research-skill-content-patterns.block.md"
CITATION_LOCATOR_AUDIT_TEMPLATE_NAME = "medical-research-citation-locator-audit.template.md"
PRISMA_FLOW_TEMPLATE_NAME = "medical-research-prisma-flow.template.md"
FIGURE_INTEGRITY_TEMPLATE_NAME = "medical-research-figure-integrity.template.md"
HELPER_TEMPLATE_NAMES = (
    SKILL_CONTENT_PATTERN_TEMPLATE_NAME,
    CITATION_LOCATOR_AUDIT_TEMPLATE_NAME,
    PRISMA_FLOW_TEMPLATE_NAME,
    FIGURE_INTEGRITY_TEMPLATE_NAME,
)
COMPANION_EXPECTATIONS = (
    ("scout", HELPER_TEMPLATE_NAMES[:3]),
    ("analysis-campaign", HELPER_TEMPLATE_NAMES),
    ("write", (STAGE_PACKET_TEMPLATE_NAME, *HELPER_TEMPLATE_NAMES)),
    ("review", HELPER_TEMPLATE_NAMES),
    ("finalize", (STAGE_PACKET_TEMPLATE_NAME, *HELPER_TEMPLATE_NAMES)),
    ("journal-resolution", HELPER_TEMPLATE_NAMES[:2]),
)
STAGE_SKILL_TEMPLATE_FILES = {
    "analysis-campaign": "medical-research-analysis-campaign.SKILL.md",
    "baseline": "medical-research-baseline.SKILL.md",
    "decision": "medical-research-decision.SKILL.md",
    "experiment": "medical-research-experiment.SKILL.md",
    "finalize": "medical-research-finalize.SKILL.md",
    "idea": "medical-research-idea.SKILL.md",
    "journal-resolution": "medical-research-journal-resolution.SKILL.md",
    "review": "medical-research-review.SKILL.md",
    "scout": "medical-research-scout.SKILL.md",
    "write": "medical-research-write.SKILL.md",
}
EXISTING_FULL_STAGE_SKILL_IDS = (
    "scout",
    "idea",
    "decision",
    "write",
    "finalize",
    "journal-resolution",
)
NEW_FULL_STAGE_SKILL_IDS = ("baseline", "experiment", "analysis-campaign", "review")
FULL_STAGE_IDS = tuple(STAGE_SKILL_TEMPLATE_FILES)
APPEND_STAGE_IDS = ("intake-audit", "rebuttal")


def write_skill(root: Path, skill_id: str, body: str) -> Path:
    target_root = root / f"{OVERLAY_PREFIX}-{skill_id}"
    target_root.mkdir(parents=True, exist_ok=True)
    skill_path = target_root / "SKILL.md"
    skill_path.write_text(body, encoding="utf-8")
    return skill_path


def write_runtime_skill(repo_root: Path, skill_id: str, body: str) -> Path:
    skill_path = repo_root / "src" / "skills" / skill_id / "SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(body, encoding="utf-8")
    return skill_path


def read_manifest(target_root: Path) -> dict:
    return json.loads((target_root / ".med_autoscience_overlay.json").read_text(encoding="utf-8"))


def read_stage_packet_template() -> str:
    return (OVERLAY_TEMPLATE_ROOT / STAGE_PACKET_TEMPLATE_NAME).read_text(encoding="utf-8")


def stage_packet_path(root: Path, skill_id: str) -> Path:
    return root / ".codex" / "skills" / f"{OVERLAY_PREFIX}-{skill_id}" / STAGE_PACKET_TEMPLATE_NAME


def companion_path(root: Path, skill_id: str, template_name: str) -> Path:
    return root / ".codex" / "skills" / f"{OVERLAY_PREFIX}-{skill_id}" / template_name


def write_system_prompt(root: Path, body: str) -> Path:
    prompt_path = root / ".codex" / "prompts" / "system.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(body, encoding="utf-8")
    return prompt_path
