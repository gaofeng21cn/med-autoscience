from __future__ import annotations


def render_medical_runtime_contract_block() -> str:
    return (
        "## Medical runtime contract\n\n"
        "- Read `paper/medical_analysis_contract.json` before deciding follow-up analyses, manuscript rewrites, or review responses.\n"
        "- Treat `paper/cohort_flow.json`, `paper/baseline_characteristics_schema.json`, and `paper/reporting_guideline_checklist.json` as required truth sources when present.\n"
        "- If `paper/display_registry.json` declares official shells such as `cohort_flow_figure` or `table1_baseline_characteristics`, materialize them through `medautosci materialize-display-surface --paper-root paper` before polishing captions or exporting submission assets.\n"
        "- If the runtime contract calls for calibration, transportability, cohort flow, or baseline characteristics evidence, do not treat ablation-heavy follow-up as sufficient.\n"
        "- Keep TRIPOD / STROBE / CONSORT family requirements explicit in durable manuscript-facing artifacts.\n"
    )
