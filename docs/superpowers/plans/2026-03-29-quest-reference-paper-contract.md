# Quest Reference Paper Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 quest 引入 agent-first、human-auditable 的 `reference_papers` contract，并将其接入 `scout / idea / write` 的运行时约束。

**Architecture:** 新增独立的 `reference_papers` 解析层与只读 controller，保持 contract 只挂在 `quest.yaml -> startup_contract`。overlay 模板通过通用规则块消费这个 contract，不内嵌具体 quest 内容。startup brief 模板补出显式入口，但不提升为 study 级长期资产。

**Tech Stack:** Python 3.12+, `dataclasses`, `pathlib`, `yaml.safe_load`, existing MedAutoScience overlay installer and CLI, pytest

---

### Task 1: 写 quest reference paper parser 的失败测试

**Files:**
- Create: `tests/test_reference_papers.py`
- Create: `src/med_autoscience/reference_papers.py`

- [ ] **Step 1: 写失败测试，覆盖最小 quest contract 解析**

```python
def test_resolve_reference_papers_reads_startup_contract(tmp_path: Path) -> None:
    ...
    contract = module.resolve_reference_paper_contract(quest_root=quest_root)
    assert contract.paper_count == 2
    assert contract.papers[0].role == "anchor_paper"
    assert contract.stage_requirements["scout"] == "required"
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `pytest tests/test_reference_papers.py -q`
Expected: FAIL with `ModuleNotFoundError` or missing symbol

- [ ] **Step 3: 实现最小 parser**

```python
@dataclass(frozen=True)
class ReferencePaper: ...

@dataclass(frozen=True)
class ReferencePaperContract: ...

def resolve_reference_paper_contract(*, quest_root: Path | None) -> ReferencePaperContract | None:
    ...
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `pytest tests/test_reference_papers.py -q`
Expected: PASS

### Task 2: 覆盖来源归一与非法输入校验

**Files:**
- Modify: `tests/test_reference_papers.py`
- Modify: `src/med_autoscience/reference_papers.py`

- [ ] **Step 1: 写失败测试，覆盖 URL / DOI / PMID / arXiv / pdf_path 支持**

```python
def test_resolve_reference_papers_accepts_remote_and_local_sources(tmp_path: Path) -> None:
    ...
    assert contract.papers[0].source_kind == "url"
    assert contract.papers[1].source_kind == "pdf_path"
```

- [ ] **Step 2: 写失败测试，覆盖缺少 locator 时抛错**

```python
def test_resolve_reference_papers_requires_at_least_one_locator(tmp_path: Path) -> None:
    ...
    with pytest.raises(ValueError):
        module.resolve_reference_paper_contract(quest_root=quest_root)
```

- [ ] **Step 3: 运行测试，确认失败**

Run: `pytest tests/test_reference_papers.py -q`
Expected: FAIL on unsupported source normalization or missing validation

- [ ] **Step 4: 补齐归一与校验实现**

```python
def _normalize_reference_paper(...):
    ...
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `pytest tests/test_reference_papers.py -q`
Expected: PASS

### Task 3: 新增只读 controller 与 CLI 审计入口

**Files:**
- Create: `src/med_autoscience/controllers/reference_papers.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Modify: `src/med_autoscience/cli.py`
- Create: `tests/test_reference_papers_controller.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试，覆盖 controller 摘要输出**

```python
def test_resolve_reference_papers_controller_returns_audit_summary(tmp_path: Path) -> None:
    ...
    assert result["status"] == "resolved"
    assert result["paper_count"] == 2
```

- [ ] **Step 2: 写失败测试，覆盖 CLI 分发**

```python
def test_resolve_reference_papers_command_dispatches_controller(...):
    ...
```

- [ ] **Step 3: 运行相关测试，确认失败**

Run: `pytest tests/test_reference_papers_controller.py tests/test_cli.py -q`
Expected: FAIL because controller / command missing

- [ ] **Step 4: 实现 controller 与 CLI**

```python
def resolve_reference_papers(*, quest_root: Path) -> dict[str, object]:
    ...
```

- [ ] **Step 5: 运行相关测试，确认通过**

Run: `pytest tests/test_reference_papers_controller.py tests/test_cli.py -q`
Expected: PASS

### Task 4: 将 reference paper contract 注入 scout / idea / write overlay

**Files:**
- Modify: `src/med_autoscience/reference_papers.py`
- Modify: `src/med_autoscience/overlay/installer.py`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-scout.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-idea.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-write.SKILL.md`
- Modify: `tests/test_overlay_installer.py`

- [ ] **Step 1: 写失败测试，覆盖 overlay 文本包含 reference paper contract 规则**

```python
def test_load_overlay_skill_text_includes_reference_paper_contract_for_scout_idea_write() -> None:
    ...
    assert "reference papers" in scout_text.lower()
    assert "advisory" in write_text.lower()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `pytest tests/test_overlay_installer.py -q`
Expected: FAIL because token / block missing

- [ ] **Step 3: 实现 overlay block 渲染与模板接入**

```python
REFERENCE_PAPERS_TOKEN = "{{MED_AUTOSCIENCE_REFERENCE_PAPERS}}"
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `pytest tests/test_overlay_installer.py -q`
Expected: PASS

### Task 5: 补 startup brief 入口并做回归验证

**Files:**
- Modify: `templates/startup_brief.template.md`
- Modify: `tests/test_reference_papers.py`

- [ ] **Step 1: 写失败测试，覆盖 startup brief 入口存在**

```python
def test_startup_brief_template_mentions_reference_papers() -> None:
    ...
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `pytest tests/test_reference_papers.py -q`
Expected: FAIL because template section missing

- [ ] **Step 3: 修改模板**

```markdown
## Reference papers
```

- [ ] **Step 4: 运行局部测试，确认通过**

Run: `pytest tests/test_reference_papers.py -q`
Expected: PASS

### Task 6: 运行目标回归测试

**Files:**
- Modify: `docs/superpowers/plans/2026-03-29-quest-reference-paper-contract.md`

- [ ] **Step 1: 运行 reference paper 相关测试**

Run: `pytest tests/test_reference_papers.py tests/test_reference_papers_controller.py tests/test_overlay_installer.py tests/test_cli.py -q`
Expected: PASS

- [ ] **Step 2: 若 CLI 或 overlay 相关已有测试被影响，修复并重跑**

Run: `pytest tests/test_submission_targets.py tests/test_submission_targets_controller.py tests/test_profiles.py -q`
Expected: PASS

- [ ] **Step 3: 记录实际验证结果到最终说明**

Run: `git diff --stat`
Expected: show parser/controller/overlay/template/test deltas only
