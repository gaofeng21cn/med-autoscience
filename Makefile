.PHONY: test test-smoke test-regression test-ci-preflight test-fast test-meta test-display test-submission test-soak-golden test-full test-family test-paths line-budget line-budget-strict test-structure test-structure-strict test-control-plane test-medical-paper-ops test-medical-quality-regression

MAS_PYTEST_WORKERS ?= auto
MAS_PYTEST_DIST ?= loadscope
MAS_PYTEST_XDIST_ARGS := -n $(MAS_PYTEST_WORKERS) --dist=$(MAS_PYTEST_DIST)

CONTROL_PLANE_TESTS := \
	tests/test_control_plane_regression.py \
	tests/test_control_plane_structure.py \
	tests/test_domain_authority_snapshot.py \
	tests/test_autonomy_state_surface.py \
	tests/test_study_runtime_typed_surface_cases/test_status_type_cases.py \
	tests/test_authority_route_gate.py \
	tests/test_delivery_artifact_authority.py \
	tests/test_storage_governance_policy_kernel.py \
	tests/test_delivery_artifact_resolution.py \
	tests/test_study_delivery_sync.py \
	tests/test_delivery_authority_backfill_apply.py \
	tests/test_truth_projection_surfaces.py \
	tests/study_progress_cases \
	--ignore=tests/study_progress_cases/current_owner_handoff_projection_cases \
	--ignore=tests/study_progress_cases/test_medical_writing_surfaces.py

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
	tests/test_line_budget.py \
	tests/test_test_lane_governance.py

test: test-smoke

test-smoke:
	@$(call run_isolated_python,-m pytest tests/test_smoke_entrypoints.py tests/test_line_budget.py -q)

test-regression:
	@$(call run_isolated_python,-m pytest -q $(MAS_PYTEST_XDIST_ARGS) -m "not meta and not display_heavy and not submission_heavy and not materialization_heavy and not family and not soak_or_golden")

test-ci-preflight:
	@if [ -z "$${BASE_REF:-}" ]; then echo "BASE_REF is required, for example: BASE_REF=HEAD~1 make test-ci-preflight" >&2; exit 2; fi
	@$(call run_isolated_python,-m med_autoscience.dev_preflight --base-ref "$${BASE_REF}")

test-fast:
	@$(call run_isolated_python,-m pytest $(FAST_TESTS) -q)

test-meta:
	@$(call run_isolated_python,-m pytest -q -m meta)

test-display:
	@$(call run_isolated_python,-m pytest -q $(MAS_PYTEST_XDIST_ARGS) -m display_heavy)

test-submission:
	@$(call run_isolated_python,-m pytest -q $(MAS_PYTEST_XDIST_ARGS) -m "submission_heavy or materialization_heavy")

test-soak-golden:
	@$(call run_isolated_python,-m pytest -q $(MAS_PYTEST_XDIST_ARGS) -m soak_or_golden)

test-family:
	@$(call run_isolated_python,-m pytest tests/test_foundry_agent_series_consumer_contract.py tests/test_framework_python_carrier.py tests/test_dev_preflight_contract.py tests/test_dev_preflight.py -q)
	@$(call run_isolated_python,-m pytest tests/test_opl_agent_lab_longline_migration.py -q)

test-paths:
	@test -n "$(TESTS)$(filter tests/%,$(MAKECMDGOALS))" || { echo "TESTS or test paths are required" >&2; exit 2; }
	@$(call run_isolated_python,-m pytest $(TESTS) $(filter tests/%,$(MAKECMDGOALS)))

tests/%:
	@:

-q:
	@:

line-budget:
	@$(call run_isolated_python,scripts/line_budget.py)

line-budget-strict: line-budget

test-control-plane:
	@$(call run_isolated_python,-m pytest -q $(CONTROL_PLANE_TESTS))

test-medical-paper-ops:
	@$(call run_isolated_python,-m pytest -q tests/test_medical_paper_ops_health.py)

test-medical-quality-regression:
	@$(call run_isolated_python,-m pytest -q tests/test_medical_quality_regression_lane.py tests/test_agent_lab_medical_manuscript_quality.py tests/test_agent_lab_medical_manuscript_quality_cases/test_owner_chain_regression_family.py tests/test_paper_progress_state.py tests/test_progress_first_global_contract.py)

test-structure:
	@$(call run_isolated_python,scripts/line_budget.py)
	scripts/run-structure-quality-gate.sh

test-structure-strict:
	@$(call run_isolated_python,scripts/line_budget.py)
	scripts/run-structure-quality-gate.sh

test-full:
	+$(MAKE) -j6 test-regression test-meta test-display test-submission test-soak-golden test-family
