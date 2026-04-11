# 医学绘图模板包 Phase 1-2 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在当前仓库内建立模板包宿主骨架，将当前内置模板库全量迁入 `fenggaolab.org.medical-display-core`，并用 `001/003` 作为首轮强验收锚点，跑通完整命名空间模板标识下的 materialize / submission / publication 链路。

**Architecture:** 宿主平台继续留在 `med-autoscience` 仓库内，但模板能力不再以内嵌注册表为唯一真相，而是通过本地目录模板包加载。Phase 1 先完成包 contract、加载器、repo/paper 级配置和完整命名空间模板标识；Phase 2 再把当前内置模板库全量迁入 `fenggaolab.org.medical-display-core`，让现有控制器、catalog、submission 和 publication gate 全部消费包化后的模板真相。

**Tech Stack:** Python 3.11、`tomllib`、现有 `med_autoscience` CLI / controller、`pytest`、`uv`

---

## 文件结构与职责

### 新增文件

- `config/display_packs.toml`
  - 仓库级默认模板包配置；声明默认启用的本地包源。
- `src/med_autoscience/display_pack_contract.py`
  - 模板包与模板清单的 dataclass 契约、TOML 解析与基础校验。
- `src/med_autoscience/display_pack_loader.py`
  - 本地目录包加载器；读取 `display_pack.toml` 与 `template.toml`。
- `src/med_autoscience/display_pack_resolver.py`
  - 活动模板包解析器；把 pack config 转成可查询的活动模板集合。
- `src/med_autoscience/display_pack_lock.py`
  - 生成与写出 `paper/build/display_pack_lock.json`。
- `tests/test_display_pack_contract.py`
  - 覆盖 manifest 解析、字段约束与 namespaced id 校验。
- `tests/test_display_pack_loader.py`
  - 覆盖本地目录包装载、模板发现、源路径解析。
- `tests/test_display_pack_resolver.py`
  - 覆盖 repo-level / paper-level 配置合并与活动模板解析。
- `tests/fixtures/display_packs/minimal_valid_pack/...`
  - 最小有效模板包 fixture。
- `display-packs/fenggaolab.org.medical-display-core/display_pack.toml`
  - 内置核心包清单。
- `display-packs/fenggaolab.org.medical-display-core/README.md`
  - 核心包说明。
- `display-packs/fenggaolab.org.medical-display-core/CHANGELOG.md`
  - 核心包变更历史。

### 修改文件

- `src/med_autoscience/display_registry.py`
  - 从中心硬编码注册表切成“活动模板集合查询门面”。
- `src/med_autoscience/display_schema_contract.py`
  - 输入契约改为从活动模板定义和 schema ref 读取，而不是只依赖硬编码 tuple。
- `src/med_autoscience/display_template_catalog.py`
  - 从活动模板包生成目录。
- `src/med_autoscience/figure_renderer_contract.py`
  - 用完整模板名查询活动模板 spec。
- `src/med_autoscience/controllers/display_surface_materialization.py`
  - materialize 入口改为消费 pack-backed template spec，并写出 pack provenance。
- `src/med_autoscience/controllers/submission_minimal.py`
  - `submission_manifest.json` 直接写完整模板名，并消费 lock/provenance。
- `src/med_autoscience/controllers/medical_publication_surface.py`
  - manuscript-facing surface 校验完整模板名与 pack metadata。
- `tests/test_display_registry.py`
  - 断言改成 namespaced id。
- `tests/test_display_schema_contract.py`
  - 断言改成 namespaced id 与 pack-backed schema coverage。
- `tests/test_display_surface_materialization.py`
  - 断言 figure/table catalog 写出完整模板名；增加 lock 文件断言。
- `tests/test_submission_minimal_display_surface.py`
  - 断言 `submission_manifest.json` 使用完整模板名。
- `tests/test_medical_publication_surface.py`
  - 断言 publication surface 对完整模板名、pack provenance 与 manuscript-facing contract 兼容。
- `docs/capabilities/medical-display/medical_display_template_catalog.md`
  - 改为从活动模板包真相重新生成。
- `docs/capabilities/medical-display/medical_display_arsenal.md`
  - 军火库总账新增“当前内置核心包”口径。
- `docs/capabilities/medical-display/medical_display_arsenal_history.md`
  - 记录“当前内置模板库全量包化迁移”这一里程碑。

## 任务 1：定义模板包 contract 与最小 fixture

**Files:**

- Create: `src/med_autoscience/display_pack_contract.py`
- Create: `tests/test_display_pack_contract.py`
- Create: `tests/fixtures/display_packs/minimal_valid_pack/display_pack.toml`
- Create: `tests/fixtures/display_packs/minimal_valid_pack/templates/roc_curve_binary/template.toml`

- [ ] **Step 1: 写失败测试，固定包与模板清单的最低 contract**

```python
from pathlib import Path

from med_autoscience.display_pack_contract import load_display_pack_manifest


def test_load_display_pack_manifest_parses_minimal_valid_pack() -> None:
    pack_root = (
        Path(__file__).parent
        / "fixtures"
        / "display_packs"
        / "minimal_valid_pack"
    )
    manifest = load_display_pack_manifest(pack_root / "display_pack.toml")

    assert manifest.pack_id == "fenggaolab.org.medical-display-core"
    assert manifest.version == "0.1.0"
    assert manifest.display_api_version == "1"
    assert manifest.default_execution_mode == "python_plugin"


def test_load_display_pack_manifest_rejects_non_namespaced_pack_id(tmp_path: Path) -> None:
    manifest_path = tmp_path / "display_pack.toml"
    manifest_path.write_text(
        'pack_id = "medical-display-core"\nversion = "0.1.0"\ndisplay_api_version = "1"\n',
        encoding="utf-8",
    )

    try:
        load_display_pack_manifest(manifest_path)
    except ValueError as exc:
        assert "pack_id" in str(exc)
    else:
        raise AssertionError("expected ValueError for non-namespaced pack_id")
```

- [ ] **Step 2: 运行测试，确认当前缺少实现**

Run:

```bash
uv run pytest -q tests/test_display_pack_contract.py
```

Expected:

```text
E   ModuleNotFoundError: No module named 'med_autoscience.display_pack_contract'
```

- [ ] **Step 3: 实现最小 contract 解析器**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class DisplayPackManifest:
    pack_id: str
    version: str
    display_api_version: str
    default_execution_mode: str


def load_display_pack_manifest(path: Path) -> DisplayPackManifest:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    pack_id = str(payload["pack_id"])
    if "." not in pack_id:
        raise ValueError("pack_id must be namespaced")
    return DisplayPackManifest(
        pack_id=pack_id,
        version=str(payload["version"]),
        display_api_version=str(payload["display_api_version"]),
        default_execution_mode=str(payload.get("default_execution_mode", "python_plugin")),
    )
```

- [ ] **Step 4: 写最小 fixture**

`tests/fixtures/display_packs/minimal_valid_pack/display_pack.toml`

```toml
pack_id = "fenggaolab.org.medical-display-core"
version = "0.1.0"
display_api_version = "1"
default_execution_mode = "python_plugin"
summary = "Minimal valid display pack fixture"
```

`tests/fixtures/display_packs/minimal_valid_pack/templates/roc_curve_binary/template.toml`

```toml
template_id = "roc_curve_binary"
full_template_id = "fenggaolab.org.medical-display-core::roc_curve_binary"
kind = "evidence_figure"
display_name = "ROC Curve (Binary Outcome)"
paper_family_ids = ["A"]
audit_family = "Prediction Performance"
renderer_family = "r_ggplot2"
input_schema_ref = "binary_prediction_curve_inputs_v1"
qc_profile_ref = "publication_evidence_curve"
required_exports = ["png", "pdf"]
execution_mode = "python_plugin"
entrypoint = "med_autoscience_pack_core.roc:render"
paper_proven = false
```

- [ ] **Step 5: 重跑测试**

Run:

```bash
uv run pytest -q tests/test_display_pack_contract.py
```

Expected:

```text
2 passed
```

- [ ] **Step 6: 提交**

```bash
git add src/med_autoscience/display_pack_contract.py tests/test_display_pack_contract.py tests/fixtures/display_packs/minimal_valid_pack
git commit -m "Add the medical display pack contract parser"
```

## 任务 2：实现本地目录包装载与仓库级配置

**Files:**

- Create: `src/med_autoscience/display_pack_loader.py`
- Create: `tests/test_display_pack_loader.py`
- Create: `config/display_packs.toml`

- [ ] **Step 1: 写失败测试，固定 repo-level pack config 的最小行为**

```python
from pathlib import Path

from med_autoscience.display_pack_loader import load_enabled_local_display_packs


def test_load_enabled_local_display_packs_reads_repo_config(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config_dir = repo_root / "config"
    config_dir.mkdir()
    (config_dir / "display_packs.toml").write_text(
        """
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "display-packs/fenggaolab.org.medical-display-core"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    pack_root = repo_root / "display-packs" / "fenggaolab.org.medical-display-core"
    (pack_root / "templates").mkdir(parents=True)
    (pack_root / "display_pack.toml").write_text(
        'pack_id = "fenggaolab.org.medical-display-core"\nversion = "0.1.0"\ndisplay_api_version = "1"\n',
        encoding="utf-8",
    )

    manifests = load_enabled_local_display_packs(repo_root)

    assert [item.pack_id for item in manifests] == ["fenggaolab.org.medical-display-core"]
```

- [ ] **Step 2: 运行测试，确认当前缺少 loader**

Run:

```bash
uv run pytest -q tests/test_display_pack_loader.py
```

Expected:

```text
E   ModuleNotFoundError: No module named 'med_autoscience.display_pack_loader'
```

- [ ] **Step 3: 实现 loader**

```python
from __future__ import annotations

from pathlib import Path
import tomllib

from med_autoscience.display_pack_contract import DisplayPackManifest, load_display_pack_manifest


def load_enabled_local_display_packs(repo_root: Path) -> list[DisplayPackManifest]:
    config = tomllib.loads((repo_root / "config" / "display_packs.toml").read_text(encoding="utf-8"))
    enabled = set(config.get("default_enabled_packs", []))
    manifests: list[DisplayPackManifest] = []
    for source in config.get("sources", []):
        if source.get("kind") != "local_dir":
            continue
        if source.get("pack_id") not in enabled:
            continue
        pack_root = repo_root / str(source["path"])
        manifests.append(load_display_pack_manifest(pack_root / "display_pack.toml"))
    return manifests
```

- [ ] **Step 4: 写入仓库默认配置**

`config/display_packs.toml`

```toml
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "display-packs/fenggaolab.org.medical-display-core"
```

- [ ] **Step 5: 跑 contract + loader 两组测试**

Run:

```bash
uv run pytest -q tests/test_display_pack_contract.py tests/test_display_pack_loader.py
```

Expected:

```text
3 passed
```

- [ ] **Step 6: 提交**

```bash
git add config/display_packs.toml src/med_autoscience/display_pack_loader.py tests/test_display_pack_loader.py
git commit -m "Add local display-pack loading from repo config"
```

## 任务 3：实现活动模板解析器与完整模板名门面

**Files:**

- Create: `src/med_autoscience/display_pack_resolver.py`
- Modify: `src/med_autoscience/display_registry.py`
- Modify: `tests/test_display_registry.py`
- Create: `tests/test_display_pack_resolver.py`

- [ ] **Step 1: 写失败测试，固定完整模板名解析**

```python
from med_autoscience.display_pack_resolver import split_full_template_id


def test_split_full_template_id_returns_pack_and_template() -> None:
    pack_id, template_id = split_full_template_id(
        "fenggaolab.org.medical-display-core::roc_curve_binary"
    )

    assert pack_id == "fenggaolab.org.medical-display-core"
    assert template_id == "roc_curve_binary"
```

- [ ] **Step 2: 写失败测试，固定 registry 查询完整模板名**

```python
from med_autoscience import display_registry


def test_get_evidence_figure_spec_accepts_namespaced_template_id() -> None:
    spec = display_registry.get_evidence_figure_spec(
        "fenggaolab.org.medical-display-core::roc_curve_binary"
    )

    assert spec.template_id == "fenggaolab.org.medical-display-core::roc_curve_binary"
```

- [ ] **Step 3: 运行相关测试，确认门面尚未支持**

Run:

```bash
uv run pytest -q tests/test_display_pack_resolver.py tests/test_display_registry.py -k 'namespaced or split_full_template_id'
```

Expected:

```text
FAIL
```

- [ ] **Step 4: 实现解析器与 registry 门面**

```python
from __future__ import annotations


def split_full_template_id(full_template_id: str) -> tuple[str, str]:
    if "::" not in full_template_id:
        raise ValueError("full template id must use '<pack_id>::<template_id>'")
    pack_id, template_id = full_template_id.split("::", 1)
    return pack_id, template_id
```

`src/med_autoscience/display_registry.py` 中将 `template_id` 写成完整模板名，并保留查询 API：

```python
def get_evidence_figure_spec(template_id: str) -> EvidenceFigureSpec:
    canonical_id = _canonicalize_template_id(template_id)
    ...
    return _EVIDENCE_FIGURE_SPEC_BY_ID[canonical_id]
```

- [ ] **Step 5: 把现有 registry tests 改成完整模板名断言**

```python
assert display_registry.get_evidence_figure_spec(
    "fenggaolab.org.medical-display-core::time_to_event_decision_curve"
).template_id == "fenggaolab.org.medical-display-core::time_to_event_decision_curve"
```

- [ ] **Step 6: 跑 resolver + registry 测试**

Run:

```bash
uv run pytest -q tests/test_display_pack_resolver.py tests/test_display_registry.py
```

Expected:

```text
PASS
```

- [ ] **Step 7: 提交**

```bash
git add src/med_autoscience/display_pack_resolver.py src/med_autoscience/display_registry.py tests/test_display_pack_resolver.py tests/test_display_registry.py
git commit -m "Switch display registry to namespaced template ids"
```

## 任务 4：建立内置核心包骨架，并全量导出当前内置模板清单

**Files:**

- Create: `display-packs/fenggaolab.org.medical-display-core/display_pack.toml`
- Create: `display-packs/fenggaolab.org.medical-display-core/README.md`
- Create: `display-packs/fenggaolab.org.medical-display-core/CHANGELOG.md`
- Create: `src/med_autoscience/display_pack_bootstrap.py`
- Create: `tests/test_display_pack_bootstrap.py`

- [ ] **Step 1: 写失败测试，固定“当前内置模板库全量导出”的覆盖率**

```python
from med_autoscience import display_registry
from med_autoscience.display_pack_bootstrap import export_core_pack_template_manifests


def test_export_core_pack_template_manifests_covers_all_current_specs(tmp_path) -> None:
    export_core_pack_template_manifests(tmp_path)
    manifest_paths = sorted(tmp_path.glob("templates/*/template.toml"))

    expected = {
        *(spec.template_id for spec in display_registry.list_evidence_figure_specs()),
        *(spec.shell_id for spec in display_registry.list_illustration_shell_specs()),
        *(spec.shell_id for spec in display_registry.list_table_shell_specs()),
    }

    actual = {path.parent.name for path in manifest_paths}
    assert actual == {item.split("::", 1)[1] for item in expected}
```

- [ ] **Step 2: 运行测试，确认导出器尚未存在**

Run:

```bash
uv run pytest -q tests/test_display_pack_bootstrap.py
```

Expected:

```text
E   ModuleNotFoundError
```

- [ ] **Step 3: 实现导出器**

```python
from __future__ import annotations

from pathlib import Path

from med_autoscience import display_registry


CORE_PACK_ID = "fenggaolab.org.medical-display-core"


def export_core_pack_template_manifests(pack_root: Path) -> None:
    templates_root = pack_root / "templates"
    templates_root.mkdir(parents=True, exist_ok=True)
    for spec in display_registry.list_evidence_figure_specs():
        template_dir = templates_root / spec.template_id.split("::", 1)[1]
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "template.toml").write_text(
            "\n".join(
                [
                    f'template_id = "{spec.template_id.split("::", 1)[1]}"',
                    f'full_template_id = "{spec.template_id}"',
                    'kind = "evidence_figure"',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
```

- [ ] **Step 4: 创建核心包清单**

`display-packs/fenggaolab.org.medical-display-core/display_pack.toml`

```toml
pack_id = "fenggaolab.org.medical-display-core"
version = "0.1.0"
display_api_version = "1"
default_execution_mode = "python_plugin"
summary = "Built-in medical display core pack"
maintainer = "FengGaoLab"
source = "repo-local"
paper_family_coverage = ["A", "B", "C", "D", "E", "F", "G", "H"]
recommended_templates = []
```

- [ ] **Step 5: 用导出器生成核心包模板清单，并提交结果**

Run:

```bash
uv run python - <<'PY'
from pathlib import Path
from med_autoscience.display_pack_bootstrap import export_core_pack_template_manifests

export_core_pack_template_manifests(
    Path("display-packs/fenggaolab.org.medical-display-core")
)
PY
```

Expected:

```text
display-packs/fenggaolab.org.medical-display-core/templates/*/template.toml created
```

- [ ] **Step 6: 跑导出覆盖测试**

Run:

```bash
uv run pytest -q tests/test_display_pack_bootstrap.py tests/test_display_registry.py tests/test_display_schema_contract.py
```

Expected:

```text
PASS
```

- [ ] **Step 7: 提交**

```bash
git add display-packs/fenggaolab.org.medical-display-core src/med_autoscience/display_pack_bootstrap.py tests/test_display_pack_bootstrap.py
git commit -m "Bootstrap the built-in medical display core pack"
```

## 任务 5：让 catalog、materialize、submission、publication 链路消费包化模板真相

**Files:**

- Modify: `src/med_autoscience/display_template_catalog.py`
- Modify: `src/med_autoscience/display_schema_contract.py`
- Modify: `src/med_autoscience/figure_renderer_contract.py`
- Modify: `src/med_autoscience/controllers/display_surface_materialization.py`
- Modify: `src/med_autoscience/controllers/submission_minimal.py`
- Modify: `src/med_autoscience/controllers/medical_publication_surface.py`
- Modify: `tests/test_display_schema_contract.py`
- Modify: `tests/test_display_surface_materialization.py`
- Modify: `tests/test_submission_minimal_display_surface.py`
- Modify: `tests/test_medical_publication_surface.py`

- [ ] **Step 1: 写失败测试，固定 figure/table catalog 输出完整模板名**

```python
def test_materialize_display_surface_writes_namespaced_template_ids(tmp_path):
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    result = module.materialize_display_surface(paper_root=paper_root)

    catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert result["status"] == "clear"
    assert catalog["figures"][0]["template_id"].startswith("fenggaolab.org.medical-display-core::")
```

- [ ] **Step 2: 写失败测试，固定 submission manifest 输出完整模板名**

```python
def test_submission_manifest_uses_namespaced_template_ids(tmp_path):
    paper_root = make_workspace(tmp_path)
    result = create_submission_minimal_package(paper_root=paper_root)
    manifest = json.loads((paper_root / "submission_minimal" / "submission_manifest.json").read_text(encoding="utf-8"))

    assert result["status"] == "clear"
    assert manifest["figures"][0]["template_id"].startswith("fenggaolab.org.medical-display-core::")
```

- [ ] **Step 3: 写失败测试，固定 publication surface 接受完整模板名**

```python
def test_medical_publication_surface_accepts_namespaced_template_ids(tmp_path):
    quest_root = build_medical_publication_surface_workspace(tmp_path)
    result = module.run_controller(quest_root=quest_root, apply=False)
    assert result["status"] == "clear"
```

- [ ] **Step 4: 把活动模板包接入 catalog 与 schema contract**

`src/med_autoscience/display_template_catalog.py`

```python
from med_autoscience.display_pack_resolver import list_active_template_specs


def _template_metadata_by_id() -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    for spec in list_active_template_specs():
        metadata[spec.template_id] = {
            "display_name": spec.display_name,
            "renderer_family": spec.renderer_family,
            "input_schema_id": spec.input_schema_id,
            "qc_profile": spec.layout_qc_profile,
        }
    return metadata
```

- [ ] **Step 5: 把控制器改成写完整模板名并保留包 provenance**

`src/med_autoscience/controllers/display_surface_materialization.py`

```python
figure_entry = {
    "figure_id": display_id,
    "template_id": spec.template_id,
    "pack_id": spec.pack_id,
    "input_schema_id": spec.input_schema_id,
    "qc_profile": spec.layout_qc_profile,
}
```

`src/med_autoscience/controllers/submission_minimal.py`

```python
manifest_figure = {
    "figure_id": figure["figure_id"],
    "template_id": figure["template_id"],
    "pack_id": figure["pack_id"],
    "input_schema_id": figure["input_schema_id"],
}
```

- [ ] **Step 6: 重跑 repo 回归**

Run:

```bash
uv run pytest -q tests/test_display_registry.py tests/test_display_schema_contract.py tests/test_display_surface_materialization.py tests/test_submission_minimal_display_surface.py tests/test_medical_publication_surface.py
```

Expected:

```text
PASS
```

- [ ] **Step 7: 提交**

```bash
git add src/med_autoscience/display_template_catalog.py src/med_autoscience/display_schema_contract.py src/med_autoscience/figure_renderer_contract.py src/med_autoscience/controllers/display_surface_materialization.py src/med_autoscience/controllers/submission_minimal.py src/med_autoscience/controllers/medical_publication_surface.py tests/test_display_schema_contract.py tests/test_display_surface_materialization.py tests/test_submission_minimal_display_surface.py tests/test_medical_publication_surface.py
git commit -m "Route display controllers through namespaced template-pack truth"
```

## 任务 6：增加 paper-level pack lock，并用 `001/003` 做首轮强验收

**Files:**

- Create: `src/med_autoscience/display_pack_lock.py`
- Modify: `src/med_autoscience/controllers/display_surface_materialization.py`
- Modify: `tests/test_display_surface_materialization.py`
- Modify: `docs/capabilities/medical-display/medical_display_template_catalog.md`
- Modify: `docs/capabilities/medical-display/medical_display_arsenal.md`
- Modify: `docs/capabilities/medical-display/medical_display_arsenal_history.md`

- [ ] **Step 1: 写失败测试，固定 `paper/build/display_pack_lock.json`**

```python
def test_materialize_display_surface_writes_display_pack_lock(tmp_path):
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    module.materialize_display_surface(paper_root=paper_root)

    lock = json.loads((paper_root / "build" / "display_pack_lock.json").read_text(encoding="utf-8"))
    assert lock["enabled_packs"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
```

- [ ] **Step 2: 实现 lock writer**

```python
from __future__ import annotations

from pathlib import Path
import json


def write_display_pack_lock(*, paper_root: Path, enabled_packs: list[dict[str, str]]) -> Path:
    path = paper_root / "build" / "display_pack_lock.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"enabled_packs": enabled_packs}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
```

- [ ] **Step 3: 更新文档入口**

Run:

```bash
uv run python - <<'PY'
from pathlib import Path
from med_autoscience.display_template_catalog import render_display_template_catalog_markdown

Path("docs/capabilities/medical-display/medical_display_template_catalog.md").write_text(
    render_display_template_catalog_markdown(),
    encoding="utf-8",
)
PY
```

Expected:

```text
docs/capabilities/medical-display/medical_display_template_catalog.md regenerated
```

- [ ] **Step 4: 跑仓库级强回归**

Run:

```bash
uv run pytest -q tests/test_display_registry.py tests/test_display_schema_contract.py tests/test_display_layout_qc.py tests/test_display_surface_materialization.py tests/test_display_surface_materialization_cli.py tests/test_publication_display_contract.py tests/test_submission_minimal_display_surface.py tests/test_medical_publication_surface.py
```

Expected:

```text
PASS
```

- [ ] **Step 5: 跑 `001` 真实 paper root 强验收**

Run:

```bash
uv run python -m med_autoscience.cli materialize-display-surface --paper-root /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk/paper
uv run python -m med_autoscience.cli export-submission-minimal --paper-root /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk/paper
uv run python -m med_autoscience.cli medical-reporting-audit --quest-root /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/med-deepscientist/runtime/quests/001-dm-cvd-mortality-risk-reentry-20260331 --apply
uv run python -m med_autoscience.cli medical-publication-surface --quest-root /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/med-deepscientist/runtime/quests/001-dm-cvd-mortality-risk-reentry-20260331 --apply
uv run python -m med_autoscience.cli publication-gate --quest-root /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/med-deepscientist/runtime/quests/001-dm-cvd-mortality-risk-reentry-20260331 --apply
```

Expected:

```text
materialize-display-surface => clear
export-submission-minimal => clear
medical-reporting-audit => clear
medical-publication-surface => clear
publication-gate => clear
```

- [ ] **Step 6: 跑 `003` 真实 paper root 强验收**

Run:

```bash
uv run python -m med_autoscience.cli materialize-display-surface --paper-root /Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup/paper
uv run python -m med_autoscience.cli export-submission-minimal --paper-root /Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup/paper
uv run python -m med_autoscience.cli medical-reporting-audit --quest-root /Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/003-endocrine-burden-followup-managed-20260402 --apply
uv run python -m med_autoscience.cli medical-publication-surface --quest-root /Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/003-endocrine-burden-followup-managed-20260402 --apply
uv run python -m med_autoscience.cli publication-gate --quest-root /Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/003-endocrine-burden-followup-managed-20260402 --apply
```

Expected:

```text
materialize-display-surface => clear
export-submission-minimal => clear
medical-reporting-audit => clear
medical-publication-surface => clear
publication-gate => clear
```

- [ ] **Step 7: 提交**

```bash
git add src/med_autoscience/display_pack_lock.py src/med_autoscience/controllers/display_surface_materialization.py tests/test_display_surface_materialization.py docs/capabilities/medical-display/medical_display_template_catalog.md docs/capabilities/medical-display/medical_display_arsenal.md docs/capabilities/medical-display/medical_display_arsenal_history.md
git commit -m "Lock template-pack provenance and reverify 001 003 acceptance"
```

## 自检清单

- [ ] 当前内置模板库是否已全量进入 `display-packs/fenggaolab.org.medical-display-core/`，而不是只迁论文用过的子集
- [ ] `display_registry` / `display_schema_contract` / `display_template_catalog` 是否都已把完整模板名当成唯一正式真相
- [ ] `figure_catalog.json`、`table_catalog.json`、`submission_manifest.json` 是否都写出完整模板名与 `pack_id`
- [ ] `paper/build/display_pack_lock.json` 是否存在并记录了实际启用包
- [ ] `001/003` 的 materialize / submission / publication 强验收是否都重新 clear

## 完成定义

以下条件全部满足，才能认为本计划完成：

1. `med-autoscience` 已能从本地目录模板包加载活动模板。
2. `fenggaolab.org.medical-display-core` 已承载当前内置模板库的全量迁移结果。
3. 系统不再以平面 `template_id` 作为正式真相。
4. 当前 `docs/capabilities/medical-display/medical_display_template_catalog.md` 已由包化真相重新生成。
5. `001/003` 已在完整模板名和 pack provenance 下重新通过首轮强验收。
