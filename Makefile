.PHONY: test test-smoke test-fast test-meta test-regression test-full test-family test-structure test-structure-strict line-budget line-budget-strict

define run_isolated_python
tmp=$$(mktemp -d "$${TMPDIR:-/tmp}/mas-python.XXXXXX"); \
trap 'rm -rf "$$tmp"' EXIT; \
uv export --quiet --frozen --no-emit-project --group dev --format requirements-txt > "$$tmp/requirements.txt"; \
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$$tmp/pycache" \
PYTEST_ADDOPTS="-p no:cacheprovider -o cache_dir=$$tmp/pytest-cache" \
uv run --isolated --frozen --no-project --with-requirements "$$tmp/requirements.txt" python $(1)
endef

FAST_TESTS := \
	tests/test_smoke_entrypoints.py \
	tests/test_standard_agent_boundary.py \
	tests/test_package_contracts.py \
	tests/test_paper_mission_authority_handler_v2.py \
	tests/test_stage_quality_cycle_policy.py \
	tests/test_stage_manifest_contract_extensions.py \
	tests/test_standard_agent_conformance_profile.py \
	tests/test_opl_standard_pack_cases/test_stage_contract_cases.py \
	tests/test_codex_plugin.py \
	tests/test_codex_plugin_scaffold.py \
	tests/test_codex_plugin_installer.py \
	tests/test_test_lane_governance.py

test: test-smoke

test-smoke:
	@$(call run_isolated_python,-m pytest tests/test_smoke_entrypoints.py -q)

test-fast:
	@$(call run_isolated_python,-m pytest $(FAST_TESTS) -q)

test-meta:
	@$(call run_isolated_python,-m pytest -q -m meta)

test-regression:
	@$(call run_isolated_python,-m pytest -q -m "not meta")

test-full:
	@$(call run_isolated_python,-m pytest tests -q)

test-family: test-fast

line-budget:
	@$(call run_isolated_python,scripts/line_budget.py)

line-budget-strict: line-budget

test-structure: line-budget
	scripts/run-structure-quality-gate.sh

test-structure-strict: test-structure
