# Runtime supervisor dispatch executor helper shim retirement closeout 2026-06-06

Owner: `MedAutoScience`
Purpose: `runtime_supervisor_dispatch_executor_helper_shim_retirement_closeout`
State: `history_provenance`
Machine boundary: 本文是人读退役 closeout。当前 owner action dispatch 测试 helper truth 继续归 `tests/domain_owner_action_dispatch_helpers.py`、调用方测试、`tests/test_adapter_retirement_boundary.py` 和 repo-native verification。

## Scope

本轮物理退役 `tests/runtime_supervisor_dispatch_executor_helpers.py`。该文件只从 `tests/domain_owner_action_dispatch_helpers.py` re-export `dispatch`、`owner_route`、`write_current_dispatch` 和 `write_json`，没有独立行为、fixture 或 active caller。

这是测试兼容 shim 清理；不改变 MAS controller、owner-route、domain-action request、runtime truth、publication truth、owner receipt、typed blocker 或 live study workspace。

## Current Contract

当前 dispatch 测试 helper canonical 入口为：

```python
from tests.domain_owner_action_dispatch_helpers import (
    dispatch,
    owner_route,
    write_current_dispatch,
    write_json,
)
```

`tests/runtime_supervisor_dispatch_executor_helpers.py` 已退役。新测试不得通过旧 runtime-supervisor filename 引入 dispatch helper；需要 helper 时直接使用 `tests.domain_owner_action_dispatch_helpers`。

## Changes

- 删除 `tests/runtime_supervisor_dispatch_executor_helpers.py`。
- `tests/test_adapter_retirement_boundary.py` 增加防复活 guard，确认旧 helper 文件不会重新出现。
- `docs/history/program/README.md` 增加本 closeout 索引。

## Verification

本轮验证入口：

```bash
rtk rg -n "runtime_supervisor_dispatch_executor_helpers" src tests contracts docs --glob '!docs/history/program/runtime_supervisor_dispatch_executor_helper_shim_retirement_closeout_2026_06_06.md' --glob '!docs/history/program/README.md'
rtk scripts/run-pytest-clean.sh tests/test_adapter_retirement_boundary.py tests/test_domain_owner_action_dispatch.py tests/test_domain_owner_action_dispatch_owner_route.py tests/test_domain_owner_action_dispatch_stall_currentness.py -q
rtk ./scripts/verify.sh
rtk git diff --check
rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" tests/test_adapter_retirement_boundary.py docs/history/program/README.md docs/history/program/runtime_supervisor_dispatch_executor_helper_shim_retirement_closeout_2026_06_06.md
rtk /Users/gaofeng/.local/bin/opl-doc-doctor doctor . --format json
```

Expected active scan result: only the no-resurrection guard in `tests/test_adapter_retirement_boundary.py` may mention `runtime_supervisor_dispatch_executor_helpers` outside this closeout and its index.

Observed results:

- retired helper scan: only `tests/test_adapter_retirement_boundary.py` no-resurrection guard remained outside this closeout and `docs/history/program/README.md`
- focused pytest: `97 passed`
- default `scripts/verify.sh`: pass; smoke `7 passed`; pre-existing line-budget advisory for `src/med_autoscience/controllers/domain_owner_action_dispatch_parts/action_execution/__init__.py` remained advisory and did not fail the gate
- `git diff --check`: pass
- conflict marker scan: no matches
- OPL doc doctor: `finding_count=0`

## Remaining Risk

历史 policy、ledger 或 closeout 文档仍可提到 `runtime_supervisor_dispatch_executor` 作为 provenance 或旧测试命令记录。它们不是当前测试 helper 入口。当前 active tests 已直接使用 `tests.domain_owner_action_dispatch_helpers`。
