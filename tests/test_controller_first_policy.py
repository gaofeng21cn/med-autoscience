from __future__ import annotations

import importlib


def test_render_controller_first_policy_block_lists_managed_task_domains() -> None:
    module = importlib.import_module("med_autoscience.policies.controller_first")

    text = module.render_controller_first_block()

    assert "## Controller-first execution contract" in text
    assert "portfolio-memory-status" in text
    assert "prepare-external-research" in text
    assert "resolve-reference-papers" in text
    assert "resolve-journal-shortlist" in text
    assert "resolve-submission-targets" in text
    assert "resolve-journal-requirements" in text
    assert "materialize-journal-package" in text
    assert "apply-data-asset-update" in text
    assert "optional enrichment" in text
    assert "scout-first route selection" in text
    assert "proactive public-data discovery pass" in text
    assert "immediate download or materialization follow-through" in text
    assert "Only when the platform does not already provide a stable controller" in text
    assert "Reuse durable study memory and portfolio research memory before starting fresh external rediscovery" in text
    assert "Choose the lightest honest route that can answer the current stage question" in text
    assert "Review and route-back discipline" in text
    assert "route back through `decision` or the named `required_first_anchor`" in text


def test_render_automation_ready_policy_block_describes_autonomous_runtime_transition() -> None:
    module = importlib.import_module("med_autoscience.policies.automation_ready")

    text = module.render_automation_ready_block()

    assert "## Automation-ready execution contract" in text
    assert "when a study boundary is explicit and startup-ready" in text
    assert "create_and_start" in text
    assert "resume" in text
    assert "continue until durable outputs requiring human selection are produced" in text
