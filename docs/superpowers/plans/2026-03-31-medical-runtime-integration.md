# Medical Runtime Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改 `DeepScientist core` 的前提下，为 `MedAutoScience` 落地医学实验 contract、PubMed/PMC/DOI 文献层、quest hydration 启动链路，以及交付前医学审计 gate。

**Architecture:** 先把医学研究要求编译成 `medical_analysis_contract` 与 `medical_reporting_contract`，再把这些 contract 与 literature 资产通过 `create_only -> hydrate -> validate -> start_or_resume` 注入 quest。runtime 继续由 `DeepScientist` 负责，`MedAutoScience` 则通过 overlay、hydration controller、runtime watch controller 和审计 controller 控制实验方向、文献补给和交付 gate。

**Tech Stack:** Python 3.12, `dataclasses`, `pathlib`, `json`, `urllib.request`, `urllib.parse`, `xml.etree.ElementTree`, `PyYAML`, existing `study_runtime_router`, `report_store`, `runtime_watch`, `medical_publication_surface`, pytest

---

### Task 1: 建立医学运行 contract 编译层

**Files:**
- Create: `src/med_autoscience/policies/medical_analysis_contract.py`
- Create: `src/med_autoscience/policies/medical_reporting_contract.py`
- Modify: `src/med_autoscience/policies/__init__.py`
- Create: `tests/test_medical_analysis_contract.py`
- Create: `tests/test_medical_reporting_contract.py`

- [ ] **Step 1: 写失败测试，覆盖 clinical classifier 的 analysis contract**

```python
from __future__ import annotations

import importlib


def test_resolve_medical_analysis_contract_for_clinical_classifier() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_analysis_contract")

    contract = module.resolve_medical_analysis_contract(
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        submission_target_family="general_medical_journal",
    )

    assert contract.study_archetype == "clinical_classifier"
    assert "calibration_assessment" in contract.required_analysis_packages
    assert "decision_curve_analysis" in contract.required_analysis_packages
    assert "subgroup_heterogeneity" in contract.required_analysis_packages
    assert "figure_by_figure_results_narration" in contract.forbidden_default_routes
```

- [ ] **Step 2: 写失败测试，覆盖 reporting contract 的 cohort flow / baseline / guideline 要求**

```python
from __future__ import annotations

import importlib


def test_resolve_medical_reporting_contract_for_prediction_manuscript() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_reporting_contract")

    contract = module.resolve_medical_reporting_contract(
        study_archetype="clinical_classifier",
        manuscript_family="prediction_model",
        submission_target_family="general_medical_journal",
    )

    assert contract.reporting_guideline_family == "TRIPOD"
    assert contract.cohort_flow_required is True
    assert contract.baseline_characteristics_required is True
    assert "table1_baseline_characteristics" in contract.table_shell_requirements
```

- [ ] **Step 3: 运行测试，确认当前失败**

Run: `pytest tests/test_medical_analysis_contract.py tests/test_medical_reporting_contract.py -q`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: 实现最小 policy 模块与导出**

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MedicalAnalysisContract:
    study_archetype: str
    endpoint_type: str
    submission_target_family: str
    required_analysis_packages: tuple[str, ...]
    required_reporting_items: tuple[str, ...]
    forbidden_default_routes: tuple[str, ...]


def resolve_medical_analysis_contract(
    *,
    study_archetype: str,
    endpoint_type: str,
    submission_target_family: str,
) -> MedicalAnalysisContract:
    packages = {
        "clinical_classifier": (
            "discrimination_metrics",
            "calibration_assessment",
            "decision_curve_analysis",
            "subgroup_heterogeneity",
        ),
    }
    return MedicalAnalysisContract(
        study_archetype=study_archetype,
        endpoint_type=endpoint_type,
        submission_target_family=submission_target_family,
        required_analysis_packages=packages[study_archetype],
        required_reporting_items=("paper_experiment_matrix", "derived_analysis_manifest"),
        forbidden_default_routes=("figure_by_figure_results_narration",),
    )
```

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MedicalReportingContract:
    reporting_guideline_family: str
    cohort_flow_required: bool
    baseline_characteristics_required: bool
    table_shell_requirements: tuple[str, ...]


def resolve_medical_reporting_contract(
    *,
    study_archetype: str,
    manuscript_family: str,
    submission_target_family: str,
) -> MedicalReportingContract:
    guideline = "TRIPOD" if manuscript_family == "prediction_model" else "STROBE"
    return MedicalReportingContract(
        reporting_guideline_family=guideline,
        cohort_flow_required=True,
        baseline_characteristics_required=True,
        table_shell_requirements=("table1_baseline_characteristics", "cohort_flow_figure"),
    )
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `pytest tests/test_medical_analysis_contract.py tests/test_medical_reporting_contract.py -q`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add tests/test_medical_analysis_contract.py tests/test_medical_reporting_contract.py src/med_autoscience/policies/medical_analysis_contract.py src/med_autoscience/policies/medical_reporting_contract.py src/med_autoscience/policies/__init__.py
git commit -m "feat: add medical runtime contract policies"
```

### Task 2: 把医学 contract 编译进 startup_contract

**Files:**
- Create: `src/med_autoscience/controllers/medical_analysis_contract.py`
- Create: `src/med_autoscience/controllers/medical_reporting_contract.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Modify: `src/med_autoscience/controllers/study_runtime_router.py`
- Modify: `tests/test_study_runtime_router.py`

- [ ] **Step 1: 写失败测试，覆盖 startup_contract 扩容字段**

```python
def test_ensure_study_runtime_includes_medical_runtime_contracts(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        paper_framing_summary="Prediction framing is fixed.",
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )

    monkeypatch.setattr(module, "inspect_workspace_contracts", lambda profile: {"overall_ready": True})
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(module.daemon_api, "create_quest", lambda *, runtime_root, payload: {"ok": True, "payload": payload})

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")
    startup_contract = result["create_payload"]["startup_contract"]

    assert startup_contract["medical_analysis_contract_summary"]["study_archetype"] == "clinical_classifier"
    assert startup_contract["medical_reporting_contract_summary"]["reporting_guideline_family"] == "TRIPOD"
    assert startup_contract["reporting_guideline_family"] == "TRIPOD"
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `pytest tests/test_study_runtime_router.py -q`
Expected: FAIL because startup contract keys are missing

- [ ] **Step 3: 实现 controller 编译接口**

```python
from __future__ import annotations

from pathlib import Path

from med_autoscience.policies.medical_analysis_contract import resolve_medical_analysis_contract


def resolve_medical_analysis_contract_for_study(*, study_root: Path, study_payload: dict[str, object]) -> dict[str, object]:
    archetype = str((study_payload.get("preferred_study_archetype") or "clinical_classifier"))
    contract = resolve_medical_analysis_contract(
        study_archetype=archetype,
        endpoint_type="binary",
        submission_target_family="general_medical_journal",
    )
    return {
        "study_archetype": contract.study_archetype,
        "required_analysis_packages": list(contract.required_analysis_packages),
        "forbidden_default_routes": list(contract.forbidden_default_routes),
    }
```

- [ ] **Step 4: 在 `study_runtime_router._build_startup_contract` 中接入 contract summary 与 required paths**

```python
medical_analysis_contract = medical_analysis_contract_controller.resolve_medical_analysis_contract_for_study(
    study_root=study_root,
    study_payload=study_payload,
)
medical_reporting_contract = medical_reporting_contract_controller.resolve_medical_reporting_contract_for_study(
    study_root=study_root,
    study_payload=study_payload,
)

return {
    "schema_version": 4,
    "user_language": "zh",
    "need_research_paper": True,
    "launch_mode": "custom",
    "medical_analysis_contract_summary": medical_analysis_contract,
    "medical_reporting_contract_summary": medical_reporting_contract,
    "reporting_guideline_family": medical_reporting_contract["reporting_guideline_family"],
}
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `pytest tests/test_study_runtime_router.py -q`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add tests/test_study_runtime_router.py src/med_autoscience/controllers/medical_analysis_contract.py src/med_autoscience/controllers/medical_reporting_contract.py src/med_autoscience/controllers/study_runtime_router.py src/med_autoscience/controllers/__init__.py
git commit -m "feat: compile medical runtime contracts into startup contract"
```

### Task 3: 引入 `create_only -> hydrate -> validate -> start_or_resume` 链路

**Files:**
- Create: `src/med_autoscience/controllers/quest_hydration.py`
- Create: `src/med_autoscience/controllers/startup_hydration_validation.py`
- Modify: `src/med_autoscience/controllers/study_runtime_router.py`
- Create: `tests/test_quest_hydration.py`
- Create: `tests/test_startup_hydration_validation.py`
- Modify: `tests/test_study_runtime_router.py`

- [ ] **Step 1: 写失败测试，覆盖 hydration 写入基础文件**

```python
def test_run_quest_hydration_writes_required_medical_runtime_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quest_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)

    report = module.run_hydration(
        quest_root=quest_root,
        hydration_payload={
            "medical_analysis_contract": {"study_archetype": "clinical_classifier"},
            "medical_reporting_contract": {"reporting_guideline_family": "TRIPOD"},
            "entry_state_summary": "Study root: /tmp/studies/001-risk",
        },
    )

    assert (quest_root / "paper" / "medical_analysis_contract.json").exists()
    assert (quest_root / "paper" / "medical_reporting_contract.json").exists()
    assert (quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json").exists()
    assert report["status"] == "hydrated"
```

- [ ] **Step 2: 写失败测试，覆盖 validation 会阻断缺失 reporting surfaces**

```python
def test_startup_hydration_validation_blocks_missing_reporting_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_hydration_validation")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)
    (quest_root / "paper" / "medical_analysis_contract.json").write_text("{}", encoding="utf-8")

    report = module.run_validation(quest_root=quest_root)

    assert report["status"] == "blocked"
    assert "missing_medical_reporting_contract" in report["blockers"]
```

- [ ] **Step 3: 写失败测试，覆盖 router 改为先 create_only 再 resume**

```python
def test_ensure_study_runtime_hydrates_before_resume(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk", paper_framing_summary="Prediction framing is fixed.")

    monkeypatch.setattr(module, "inspect_workspace_contracts", lambda profile: {"overall_ready": True})
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    calls: list[tuple[str, object]] = []

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        calls.append(("create", payload["auto_start"]))
        return {"ok": True, "snapshot": {"quest_id": "001-risk", "quest_root": str(runtime_root / "001-risk")}}

    monkeypatch.setattr(module.daemon_api, "create_quest", fake_create_quest)
    monkeypatch.setattr(module.quest_hydration_controller, "run_hydration", lambda **kwargs: {"status": "hydrated"})
    monkeypatch.setattr(module.startup_hydration_validation_controller, "run_validation", lambda **kwargs: {"status": "clear", "blockers": []})
    monkeypatch.setattr(module.daemon_api, "resume_quest", lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"})

    module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")
    assert calls == [("create", False)]
```

- [ ] **Step 4: 运行测试，确认当前失败**

Run: `pytest tests/test_quest_hydration.py tests/test_startup_hydration_validation.py tests/test_study_runtime_router.py -q`
Expected: FAIL because controllers and staged start flow are missing

- [ ] **Step 5: 实现 hydration / validation controller 与 router 集成**

```python
def run_hydration(*, quest_root: Path, hydration_payload: dict[str, object]) -> dict[str, object]:
    _write_json(quest_root / "paper" / "medical_analysis_contract.json", hydration_payload["medical_analysis_contract"])
    _write_json(quest_root / "paper" / "medical_reporting_contract.json", hydration_payload["medical_reporting_contract"])
    _write_json(
        quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json",
        {"status": "hydrated", "quest_root": str(quest_root)},
    )
    return {"status": "hydrated", "quest_root": str(quest_root)}
```

```python
def run_validation(*, quest_root: Path) -> dict[str, object]:
    blockers: list[str] = []
    if not (quest_root / "paper" / "medical_analysis_contract.json").exists():
        blockers.append("missing_medical_analysis_contract")
    if not (quest_root / "paper" / "medical_reporting_contract.json").exists():
        blockers.append("missing_medical_reporting_contract")
    return {"status": "blocked" if blockers else "clear", "blockers": blockers}
```

```python
create_payload = _build_create_payload(
    profile=profile,
    study_id=study_id,
    study_root=study_root,
    study_payload=study_payload,
    execution=execution,
)
create_payload["auto_start"] = False
create_result = daemon_api.create_quest(runtime_root=profile.deepscientist_runtime_root, payload=create_payload)
quest_hydration_controller.run_hydration(quest_root=quest_root, hydration_payload=hydration_payload)
validation = startup_hydration_validation_controller.run_validation(quest_root=quest_root)
if validation["status"] != "clear":
    return {"decision": "blocked", "reason": "hydration_validation_failed", "validation": validation}
resume_result = daemon_api.resume_quest(runtime_root=profile.deepscientist_runtime_root, quest_id=quest_id, source=source)
```

- [ ] **Step 6: 运行测试，确认通过**

Run: `pytest tests/test_quest_hydration.py tests/test_startup_hydration_validation.py tests/test_study_runtime_router.py -q`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add tests/test_quest_hydration.py tests/test_startup_hydration_validation.py tests/test_study_runtime_router.py src/med_autoscience/controllers/quest_hydration.py src/med_autoscience/controllers/startup_hydration_validation.py src/med_autoscience/controllers/study_runtime_router.py
git commit -m "feat: add quest hydration startup flow"
```

### Task 4: 建立 normalized literature record 与 PubMed / PMC / DOI adapters

**Files:**
- Create: `src/med_autoscience/literature_records.py`
- Create: `src/med_autoscience/adapters/literature/__init__.py`
- Create: `src/med_autoscience/adapters/literature/pubmed.py`
- Create: `src/med_autoscience/adapters/literature/pmc.py`
- Create: `src/med_autoscience/adapters/literature/doi.py`
- Create: `tests/test_literature_records.py`
- Create: `tests/test_pubmed_adapter.py`
- Create: `tests/test_pmc_adapter.py`
- Create: `tests/test_doi_adapter.py`

- [ ] **Step 1: 写失败测试，覆盖 literature record 归一与 source priority**

```python
from __future__ import annotations

import importlib


def test_literature_record_prefers_pubmed_over_arxiv() -> None:
    module = importlib.import_module("med_autoscience.literature_records")

    record = module.LiteratureRecord(
        record_id="pmid:12345",
        title="Prediction model paper",
        authors=("A. Author",),
        year=2024,
        journal="BMC Medicine",
        doi="10.1000/example",
        pmid="12345",
        pmcid=None,
        arxiv_id="2401.12345",
        abstract="Structured abstract",
        full_text_availability="abstract_only",
        source_priority=2,
        citation_payload={"journal": "BMC Medicine"},
        local_asset_paths=(),
        relevance_role="anchor",
        claim_support_scope=("primary_claim",),
    )

    assert record.primary_source == "pubmed"
```

- [ ] **Step 2: 写失败测试，覆盖 PubMed / PMC / DOI 解析**

```python
def test_fetch_pubmed_summary_parses_esummary_json(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.adapters.literature.pubmed")
    payload = b'{"result": {"uids": ["12345"], "12345": {"uid": "12345", "title": "Paper title", "pubdate": "2024 Jan", "fulljournalname": "BMC Medicine"}}}'
    monkeypatch.setattr(module, "_fetch_bytes", lambda url: payload)

    records = module.fetch_pubmed_summary(pmids=["12345"])

    assert records[0].pmid == "12345"
    assert records[0].journal == "BMC Medicine"
```

```python
def test_fetch_crossref_work_parses_doi_json(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.adapters.literature.doi")
    payload = b'{"message": {"DOI": "10.1000/example", "title": ["Paper title"], "container-title": ["Journal of Clinical Study"], "published-print": {"date-parts": [[2023]]}}}'
    monkeypatch.setattr(module, "_fetch_bytes", lambda url: payload)

    record = module.fetch_crossref_work(doi="10.1000/example")

    assert record.doi == "10.1000/example"
    assert record.journal == "Journal of Clinical Study"
```

- [ ] **Step 3: 运行测试，确认当前失败**

Run: `pytest tests/test_literature_records.py tests/test_pubmed_adapter.py tests/test_pmc_adapter.py tests/test_doi_adapter.py -q`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: 实现 record 模型与 adapter**

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiteratureRecord:
    record_id: str
    title: str
    authors: tuple[str, ...]
    year: int | None
    journal: str | None
    doi: str | None
    pmid: str | None
    pmcid: str | None
    arxiv_id: str | None
    abstract: str | None
    full_text_availability: str
    source_priority: int
    citation_payload: dict[str, object]
    local_asset_paths: tuple[str, ...]
    relevance_role: str
    claim_support_scope: tuple[str, ...]

    @property
    def primary_source(self) -> str:
        if self.pmid:
            return "pubmed"
        if self.pmcid:
            return "pmc"
        if self.doi:
            return "doi"
        if self.arxiv_id:
            return "arxiv"
        return "local"
```

```python
PUBMED_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def fetch_pubmed_summary(*, pmids: list[str]) -> list[LiteratureRecord]:
    query = urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "json"})
    payload = json.loads(_fetch_bytes(f"{PUBMED_ESUMMARY_URL}?{query}").decode("utf-8"))
    return [
        LiteratureRecord(
            record_id=f"pmid:{uid}",
            title=str(payload["result"][uid]["title"]),
            authors=(),
            year=int(str(payload["result"][uid]["pubdate"]).split()[0]),
            journal=str(payload["result"][uid]["fulljournalname"]),
            doi=None,
            pmid=uid,
            pmcid=None,
            arxiv_id=None,
            abstract=None,
            full_text_availability="abstract_only",
            source_priority=2,
            citation_payload={"journal": payload["result"][uid]["fulljournalname"]},
            local_asset_paths=(),
            relevance_role="candidate",
            claim_support_scope=(),
        )
        for uid in payload["result"]["uids"]
    ]
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `pytest tests/test_literature_records.py tests/test_pubmed_adapter.py tests/test_pmc_adapter.py tests/test_doi_adapter.py -q`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add tests/test_literature_records.py tests/test_pubmed_adapter.py tests/test_pmc_adapter.py tests/test_doi_adapter.py src/med_autoscience/literature_records.py src/med_autoscience/adapters/literature/__init__.py src/med_autoscience/adapters/literature/pubmed.py src/med_autoscience/adapters/literature/pmc.py src/med_autoscience/adapters/literature/doi.py
git commit -m "feat: add medical literature adapters"
```

### Task 5: 建立 literature hydration、BibTeX 导出与 reference coverage 报告

**Files:**
- Create: `src/med_autoscience/controllers/literature_hydration.py`
- Modify: `src/med_autoscience/controllers/quest_hydration.py`
- Modify: `src/med_autoscience/reference_papers.py`
- Create: `tests/test_literature_hydration.py`
- Modify: `tests/test_quest_hydration.py`
- Modify: `tests/test_reference_papers.py`

- [ ] **Step 1: 写失败测试，覆盖 startup hydration 产出 literature surfaces**

```python
def test_literature_hydration_exports_records_bib_and_coverage_report(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    quest_root.mkdir(parents=True, exist_ok=True)

    report = module.run_literature_hydration(
        quest_root=quest_root,
        records=[
            {
                "record_id": "pmid:12345",
                "title": "Prediction model paper",
                "authors": ["A. Author"],
                "year": 2024,
                "journal": "BMC Medicine",
                "doi": "10.1000/example",
                "pmid": "12345",
                "pmcid": None,
                "arxiv_id": None,
                "abstract": "Structured abstract",
                "full_text_availability": "abstract_only",
                "source_priority": 2,
                "citation_payload": {"journal": "BMC Medicine"},
                "local_asset_paths": [],
                "relevance_role": "anchor",
                "claim_support_scope": ["primary_claim"],
            }
        ],
    )

    assert (quest_root / "literature" / "pubmed" / "records.jsonl").exists()
    assert (quest_root / "paper" / "references.bib").exists()
    assert (quest_root / "paper" / "reference_coverage_report.json").exists()
    assert report["record_count"] == 1
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `pytest tests/test_literature_hydration.py tests/test_quest_hydration.py tests/test_reference_papers.py -q`
Expected: FAIL because controller and output files are missing

- [ ] **Step 3: 实现 literature hydration controller**

```python
def run_literature_hydration(*, quest_root: Path, records: list[dict[str, object]]) -> dict[str, object]:
    records_path = quest_root / "literature" / "pubmed" / "records.jsonl"
    references_bib_path = quest_root / "paper" / "references.bib"
    coverage_path = quest_root / "paper" / "reference_coverage_report.json"
    records_path.parent.mkdir(parents=True, exist_ok=True)
    references_bib_path.parent.mkdir(parents=True, exist_ok=True)
    records_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
        encoding="utf-8",
    )
    references_bib_path.write_text(
        "".join(
            f"@article{{{item['record_id']}},\n  title = {{{item['title']}}},\n  journal = {{{item['journal']}}}\n}\n\n"
            for item in records
        ),
        encoding="utf-8",
    )
    coverage_path.write_text(
        json.dumps({"record_count": len(records), "high_priority_missing": []}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "status": "hydrated",
        "record_count": len(records),
        "records_path": str(records_path),
        "references_bib_path": str(references_bib_path),
        "coverage_path": str(coverage_path),
    }
```

- [ ] **Step 4: 在 `quest_hydration.run_hydration` 中调用 literature hydration，并将路径写入 hydration report**

```python
literature_report = literature_hydration_controller.run_literature_hydration(
    quest_root=quest_root,
    records=hydration_payload.get("literature_records") or [],
)
_write_json(
    quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json",
    {
        "status": "hydrated",
        "quest_root": str(quest_root),
        "literature_report": literature_report,
    },
)
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `pytest tests/test_literature_hydration.py tests/test_quest_hydration.py tests/test_reference_papers.py -q`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add tests/test_literature_hydration.py tests/test_quest_hydration.py tests/test_reference_papers.py src/med_autoscience/controllers/literature_hydration.py src/med_autoscience/controllers/quest_hydration.py src/med_autoscience/reference_papers.py
git commit -m "feat: hydrate medical literature into quests"
```

### Task 6: 让 runtime 在实验、分析、写作、review 阶段消费医学 contract

**Files:**
- Modify: `src/med_autoscience/overlay/installer.py`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-experiment.block.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-analysis-campaign.block.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-write.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-review.block.md`
- Modify: `tests/test_overlay_installer.py`
- Modify: `tests/test_policy_integration.py`

- [ ] **Step 1: 写失败测试，覆盖 overlay 注入医学 contract 与 reporting checklist 提示**

```python
def test_overlay_includes_medical_runtime_contract_blocks() -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")

    experiment_text = module.load_overlay_skill_text("experiment")
    review_text = module.load_overlay_skill_text("review")

    assert "medical_analysis_contract" in experiment_text
    assert "cohort flow" in review_text.lower()
    assert "baseline characteristics" in review_text.lower()
    assert "TRIPOD" in review_text or "STROBE" in review_text or "CONSORT" in review_text
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `pytest tests/test_overlay_installer.py tests/test_policy_integration.py -q`
Expected: FAIL because blocks and tokens are missing

- [ ] **Step 3: 在 overlay installer 中新增 token 与 block 渲染**

```python
MEDICAL_RUNTIME_CONTRACT_TOKEN = "{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}"


def render_medical_runtime_contract_block() -> str:
    return (
        "## Medical runtime contract\\n\\n"
        "- Read `paper/medical_analysis_contract.json` before deciding follow-up analyses.\\n"
        "- Treat `paper/cohort_flow.json`, `paper/baseline_characteristics_schema.json`, and "
        "`paper/reporting_guideline_checklist.json` as required truth sources when present.\\n"
    )
```

- [ ] **Step 4: 将 block 接入实验、analysis-campaign、write、review 模板**

```markdown
{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}

Do not treat ablation-heavy follow-up as sufficient when the medical runtime contract requires calibration,
transportability, cohort accounting, or reporting-guideline coverage.
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `pytest tests/test_overlay_installer.py tests/test_policy_integration.py -q`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add tests/test_overlay_installer.py tests/test_policy_integration.py src/med_autoscience/overlay/installer.py src/med_autoscience/overlay/templates/deepscientist-experiment.block.md src/med_autoscience/overlay/templates/deepscientist-analysis-campaign.block.md src/med_autoscience/overlay/templates/deepscientist-write.SKILL.md src/med_autoscience/overlay/templates/deepscientist-review.block.md
git commit -m "feat: inject medical runtime contracts into overlay"
```

### Task 7: 新增 write/review 期医学文献补引 loop 与 reporting 审计 controller，并接入 runtime watch

**Files:**
- Create: `src/med_autoscience/controllers/medical_literature_audit.py`
- Create: `src/med_autoscience/controllers/medical_reporting_audit.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Modify: `src/med_autoscience/controllers/runtime_watch.py`
- Create: `tests/test_medical_literature_audit.py`
- Create: `tests/test_medical_reporting_audit.py`
- Modify: `tests/test_runtime_watch.py`

- [ ] **Step 1: 写失败测试，覆盖 `medical_literature_audit(apply=True)` 会触发补引 hydration**

```python
def test_medical_literature_audit_apply_triggers_literature_hydration(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_literature_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper" / "review").mkdir(parents=True, exist_ok=True)
    (quest_root / "paper" / "review" / "reference_gap_report.json").write_text(
        '{"missing_queries": ["residual disease prediction"], "missing_pmids": ["12345"]}',
        encoding="utf-8",
    )
    called: dict[str, object] = {}

    monkeypatch.setattr(
        module.pubmed_adapter,
        "fetch_pubmed_summary",
        lambda *, pmids: [{"record_id": "pmid:12345", "title": "Paper title", "pmid": "12345"}],
    )
    monkeypatch.setattr(
        module.literature_hydration_controller,
        "run_literature_hydration",
        lambda *, quest_root, records: called.update({"quest_root": quest_root, "records": records}) or {"status": "hydrated"},
    )

    report = module.run_controller(quest_root=quest_root, apply=True)

    assert report["status"] == "blocked"
    assert report["action"] == "supplemented"
    assert called["quest_root"] == quest_root
    assert called["records"][0]["record_id"] == "pmid:12345"
```

- [ ] **Step 2: 写失败测试，覆盖 reporting audit 阻断缺失 cohort flow / checklist**

```python
def test_medical_reporting_audit_blocks_missing_population_accounting(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)
    (quest_root / "paper" / "medical_reporting_contract.json").write_text('{"reporting_guideline_family": "TRIPOD"}', encoding="utf-8")

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "missing_cohort_flow" in report["blockers"]
    assert "missing_reporting_guideline_checklist" in report["blockers"]
```

- [ ] **Step 3: 写失败测试，覆盖 runtime_watch 注册新 controller**

```python
def test_runtime_watch_registers_medical_runtime_audits() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runners = module.build_default_controller_runners()

    assert "medical_literature_audit" in runners
    assert "medical_reporting_audit" in runners
```

- [ ] **Step 4: 运行测试，确认当前失败**

Run: `pytest tests/test_medical_literature_audit.py tests/test_medical_reporting_audit.py tests/test_runtime_watch.py -q`
Expected: FAIL because controllers and watch registration are missing

- [ ] **Step 5: 实现文献补引 apply 分支、reporting audit 与 runtime watch 集成**

```python
def run_controller(*, quest_root: Path, apply: bool) -> dict[str, object]:
    gap_report_path = quest_root / "paper" / "review" / "reference_gap_report.json"
    payload = json.loads(gap_report_path.read_text(encoding="utf-8")) if gap_report_path.exists() else {}
    missing_pmids = list(payload.get("missing_pmids") or [])
    action = "clear"
    if apply and missing_pmids:
        fetched_records = pubmed_adapter.fetch_pubmed_summary(pmids=missing_pmids)
        literature_hydration_controller.run_literature_hydration(
            quest_root=quest_root,
            records=[record if isinstance(record, dict) else asdict(record) for record in fetched_records],
        )
        action = "supplemented"
    blockers = ["reference_gaps_present"] if missing_pmids else []
    return {
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "action": action,
        "quest_root": str(quest_root),
    }
```

```python
def run_controller(*, quest_root: Path, apply: bool) -> dict[str, object]:
    blockers: list[str] = []
    if not (quest_root / "paper" / "cohort_flow.json").exists():
        blockers.append("missing_cohort_flow")
    if not (quest_root / "paper" / "reporting_guideline_checklist.json").exists():
        blockers.append("missing_reporting_guideline_checklist")
    report = {"status": "blocked" if blockers else "clear", "blockers": blockers, "quest_root": str(quest_root)}
    return report
```

```python
def build_default_controller_runners() -> dict[str, ControllerRunner]:
    return {
        "data_asset_gate": data_asset_gate.run_controller,
        "publication_gate": publication_gate.run_controller,
        "medical_publication_surface": medical_publication_surface.run_controller,
        "medical_literature_audit": medical_literature_audit.run_controller,
        "medical_reporting_audit": medical_reporting_audit.run_controller,
        "figure_loop_guard": figure_loop_guard.run_controller,
    }
```

- [ ] **Step 6: 运行测试，确认通过**

Run: `pytest tests/test_medical_literature_audit.py tests/test_medical_reporting_audit.py tests/test_runtime_watch.py -q`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add tests/test_medical_literature_audit.py tests/test_medical_reporting_audit.py tests/test_runtime_watch.py src/med_autoscience/controllers/medical_literature_audit.py src/med_autoscience/controllers/medical_reporting_audit.py src/med_autoscience/controllers/runtime_watch.py src/med_autoscience/controllers/__init__.py
git commit -m "feat: add medical runtime audit controllers"
```

### Task 8: 暴露 direct CLI / MCP 审计入口并完成端到端回归

**Files:**
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/mcp_server.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_mcp_server.py`
- Modify: `docs/superpowers/plans/2026-03-31-medical-runtime-integration.md`

- [ ] **Step 1: 写失败测试，覆盖 CLI 直接调用新的 audit controller**

```python
def test_medical_reporting_audit_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_controller(*, quest_root: Path, apply: bool) -> dict[str, object]:
        called["quest_root"] = quest_root
        called["apply"] = apply
        return {"status": "clear", "quest_root": str(quest_root)}

    monkeypatch.setattr(cli.medical_reporting_audit, "run_controller", fake_run_controller)

    exit_code = cli.main(["medical-reporting-audit", "--quest-root", str(tmp_path / "quest")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "quest"
    assert '"status": "clear"' in captured.out
```

- [ ] **Step 2: 写失败测试，覆盖 MCP tool 暴露**

```python
def test_mcp_server_exposes_medical_reporting_audit_tool() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = module.build_tool_manifest()
    tool_names = {tool["name"] for tool in tools}
    assert "medical_reporting_audit" in tool_names
    assert "medical_literature_audit" in tool_names
```

- [ ] **Step 3: 运行测试，确认当前失败**

Run: `pytest tests/test_cli.py tests/test_mcp_server.py -q`
Expected: FAIL because commands and tools are missing

- [ ] **Step 4: 实现 CLI / MCP 接线**

```python
medical_reporting_audit_parser = subparsers.add_parser("medical-reporting-audit")
medical_reporting_audit_parser.add_argument("--quest-root", required=True)
medical_reporting_audit_parser.add_argument("--apply", action="store_true")

medical_literature_audit_parser = subparsers.add_parser("medical-literature-audit")
medical_literature_audit_parser.add_argument("--quest-root", required=True)
medical_literature_audit_parser.add_argument("--apply", action="store_true")
```

```python
{
    "name": "medical_reporting_audit",
    "description": "Run the medical reporting audit controller for a quest.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "quest_root": {"type": "string"},
            "apply": {"type": "boolean"},
        },
        "required": ["quest_root"],
    },
}
```

- [ ] **Step 5: 运行目标回归测试**

Run: `pytest tests/test_medical_analysis_contract.py tests/test_medical_reporting_contract.py tests/test_study_runtime_router.py tests/test_quest_hydration.py tests/test_startup_hydration_validation.py tests/test_literature_records.py tests/test_pubmed_adapter.py tests/test_pmc_adapter.py tests/test_doi_adapter.py tests/test_literature_hydration.py tests/test_overlay_installer.py tests/test_policy_integration.py tests/test_medical_literature_audit.py tests/test_medical_reporting_audit.py tests/test_medical_publication_surface.py tests/test_runtime_watch.py tests/test_cli.py tests/test_mcp_server.py -q`
Expected: PASS

- [ ] **Step 6: 运行一轮更宽的 managed runtime 回归**

Run: `pytest tests/test_reference_papers.py tests/test_reference_papers_controller.py tests/test_submission_targets.py tests/test_submission_targets_controller.py tests/test_runtime_reentry_gate.py tests/test_publication_gate.py -q`
Expected: PASS

- [ ] **Step 7: 记录验证结果并提交**

Run: `git diff --stat`
Expected: show medical contract, hydration, literature, overlay, audit, CLI/MCP deltas only

```bash
git add src/med_autoscience/cli.py src/med_autoscience/mcp_server.py tests/test_cli.py tests/test_mcp_server.py
git commit -m "feat: expose medical runtime audit entrypoints"
```
