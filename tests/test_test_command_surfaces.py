from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import subprocess
import tomllib
from pathlib import Path

import pytest
from med_autoscience.control_plane_command_catalog import CONTROL_PLANE_OPERATIONS_COMMANDS


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_LANE_MANIFEST_PATH = "contracts/test-lane-manifest.json"
REQUIRED_OPL_SHARED_RUNTIME_CONTINUITY_COMMIT = "2b08c7efd8acd80355e870087d4ce5be7b45d4d1"
REQUIRED_CONTROL_PLANE_TESTS = (
    "tests/test_control_plane_regression.py",
    "tests/test_control_plane_structure.py",
    "tests/test_study_control_plane_kernel.py",
    "tests/test_control_plane_state_machine.py",
    "tests/test_study_runtime_typed_surface_cases/status_type_cases.py",
    "tests/test_control_plane_route_gate.py",
    "tests/test_artifact_lifecycle_inventory.py",
    "tests/test_artifact_retention_operations_plan.py",
    "tests/test_artifact_lifecycle_operations_report.py",
    "tests/test_runtime_protocol_paper_artifacts.py",
    "tests/test_study_delivery_sync.py",
    "tests/test_runtime_storage_maintenance.py",
    "tests/test_control_plane_cleanup_apply.py",
    "tests/test_control_plane_migration_audit.py",
    "tests/test_cli_cases/public_entry_commands.py::test_migration_audit_command_dispatches_read_only_controller",
    "tests/test_cli_cases/public_entry_commands.py::test_cleanup_apply_command_dispatches_controller",
    "tests/test_cli_cases/public_entry_commands.py::test_lifecycle_report_command_dispatches_read_only_controller_options",
    "tests/test_cli_cases/control_plane_operation_commands.py",
    "tests/test_mcp_server.py::test_mcp_product_entry_description_documents_control_plane_operations_surfaces",
    "tests/test_mcp_server.py::test_mcp_product_entry_schema_accepts_control_plane_operations_options",
    "tests/test_mcp_server.py::test_mcp_product_entry_can_call_migration_audit",
    "tests/test_mcp_server.py::test_mcp_product_entry_can_call_cleanup_apply",
    "tests/test_mcp_server.py::test_mcp_product_entry_can_call_lifecycle_report_with_scan_options",
    "tests/test_test_command_surfaces.py::test_control_plane_operation_command_catalog_guards_cli_mcp_manifest_and_schema_surfaces",
    "tests/test_installed_mcp_smoke.py::test_installed_medautosci_mcp_lists_control_plane_operation_modes",
    "tests/test_installed_mcp_smoke.py::test_installed_medautosci_cli_lists_control_plane_operation_commands",
    "tests/test_installed_mcp_smoke.py::test_installed_medautosci_mcp_calls_continuous_soak_summary",
    "tests/test_installed_mcp_smoke.py::test_installed_medautosci_cli_calls_continuous_soak_summary",
    "tests/test_truth_projection_surfaces.py",
)
PARALLEL_FULL_LANES = (
    "test-regression",
    "test-meta",
    "test-display",
    "test-submission",
    "test-family",
)


def _test_lane_manifest() -> dict[str, object]:
    return json.loads(_read(TEST_LANE_MANIFEST_PATH))


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _assert_command_surface_matches_catalog(
    *,
    surface: str,
    expected_commands: set[str],
    actual_commands: set[str],
) -> None:
    assert expected_commands == actual_commands, (
        f"control-plane command catalog/{surface} drift: "
        f"missing_from_{surface}={sorted(expected_commands - actual_commands)} "
        f"missing_from_catalog={sorted(actual_commands - expected_commands)}"
    )


def _assert_mcp_modes_cover_catalog(*, expected: tuple[object, ...], actual_modes: set[str]) -> None:
    missing_commands = [
        getattr(spec, "command")
        for spec in expected
        if getattr(spec, "mcp_mode") not in actual_modes
    ]
    unexpected_modes = sorted(
        mode
        for mode in actual_modes
        if mode.startswith(("migration_", "governance_", "backfill_", "cleanup_", "safe_cache_", "lifecycle_"))
        and mode not in {getattr(spec, "mcp_mode") for spec in expected}
    )
    assert not missing_commands and not unexpected_modes, (
        "control-plane command catalog/mcp drift: "
        f"missing_commands_from_mcp={missing_commands} "
        f"unexpected_control_plane_mcp_modes={unexpected_modes}"
    )


def test_makefile_exposes_layered_test_entrypoints() -> None:
    makefile = _read("Makefile")
    manifest = _test_lane_manifest()
    smoke_paths = " ".join(manifest["lanes"]["smoke"]["paths"])

    assert "MAS_PYTEST_WORKERS ?= auto" in makefile
    assert "MAS_PYTEST_DIST ?= loadscope" in makefile
    assert "MAS_PYTEST_XDIST_ARGS := -n $(MAS_PYTEST_WORKERS) --dist=$(MAS_PYTEST_DIST)" in makefile
    assert "test-control-plane:" in makefile
    assert "CONTROL_PLANE_TESTS :=" in makefile
    for test_path in REQUIRED_CONTROL_PLANE_TESTS:
        assert test_path in makefile
    assert "PYTHONPATH=src uv run pytest -q $(CONTROL_PLANE_TESTS)" in makefile
    assert "test: test-smoke" in makefile
    assert "test-smoke:" in makefile
    assert f"uv run pytest {smoke_paths} -q" in makefile
    assert "test-regression:" in makefile
    assert (
        'uv run pytest -q $(MAS_PYTEST_XDIST_ARGS) '
        '-m "not meta and not display_heavy and not submission_heavy '
        'and not materialization_heavy and not family"'
    ) in makefile
    assert "test-ci-preflight:" in makefile
    assert 'uv run python -m med_autoscience.cli doctor preflight --base-ref "$${BASE_REF}"' in makefile
    assert "test-fast: test-regression" in makefile
    assert "test-meta:" in makefile
    assert "uv run pytest -q -m meta" in makefile
    assert "test-display:" in makefile
    assert "uv run pytest -q $(MAS_PYTEST_XDIST_ARGS) -m display_heavy" in makefile
    assert "test-submission:" in makefile
    assert 'uv run pytest -q $(MAS_PYTEST_XDIST_ARGS) -m "submission_heavy or materialization_heavy"' in makefile
    assert "test-family:" in makefile
    assert (
        "uv run pytest tests/test_family_shared_release.py tests/test_editable_shared_bootstrap.py "
        "tests/test_dev_preflight_contract.py tests/test_dev_preflight.py -q"
    ) in makefile
    assert "test-structure:" in makefile
    assert "uv run python scripts/line_budget.py" in makefile
    assert "scripts/run-structure-quality-gate.sh" in makefile
    assert "test-full:" in makefile
    assert "./scripts/run-parallel-test-lanes.sh full" in makefile


def test_structure_lane_keeps_line_budget_and_quality_gate_wrapper() -> None:
    makefile = _read("Makefile")
    structure_block = makefile.split("test-structure:", maxsplit=1)[1].split(
        "\ntest-full:", maxsplit=1
    )[0]

    assert "\tuv run python scripts/line_budget.py" in structure_block
    assert "\tscripts/run-structure-quality-gate.sh" in structure_block


def test_only_heavy_make_lanes_use_xdist() -> None:
    makefile = _read("Makefile")
    lane_names = (
        "test-smoke",
        "test-regression",
        "test-meta",
        "test-display",
        "test-submission",
        "test-family",
        "test-control-plane",
        "test-medical-paper-ops",
    )
    lane_blocks = {
        lane: makefile.split(f"{lane}:", maxsplit=1)[1].split("\ntest-", maxsplit=1)[0]
        for lane in lane_names
    }

    for lane in ("test-regression", "test-display", "test-submission"):
        assert "$(MAS_PYTEST_XDIST_ARGS)" in lane_blocks[lane]
    for lane in (
        "test-smoke",
        "test-meta",
        "test-family",
        "test-control-plane",
        "test-medical-paper-ops",
    ):
        assert "$(MAS_PYTEST_XDIST_ARGS)" not in lane_blocks[lane]


def test_structure_quality_gate_wrapper_runs_sentrux_and_opl_compare_ref_on_failure() -> None:
    script = _read("scripts/run-structure-quality-gate.sh")

    assert 'compare_ref="${OPL_QUALITY_DETAILS_COMPARE_REF:-origin/main}"' in script
    assert 'opl_bin="${OPL_QUALITY_DETAILS_BIN:-/Users/gaofeng/workspace/one-person-lab/bin/opl}"' in script
    assert 'run_sentrux_command "sentrux gate" sentrux gate' in script
    assert 'run_sentrux_command "sentrux check" sentrux check' in script
    assert '--compare-ref "${compare_ref}"' in script
    assert 'return "${exit_code}"' in script


def test_structure_quality_gate_wrapper_preserves_sentrux_failure_code(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    capture_path = tmp_path / "opl.args"
    fake_sentrux = fake_bin / "sentrux"
    fake_sentrux.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "if [[ \"$1\" == \"gate\" ]]; then exit 33; fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_sentrux.chmod(0o755)
    fake_opl = fake_bin / "opl"
    fake_opl.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$@\" >\"${MAS_TEST_CAPTURE_PATH}\"\n",
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["MAS_TEST_CAPTURE_PATH"] = str(capture_path)
    env["OPL_QUALITY_DETAILS_BIN"] = str(fake_opl)

    result = subprocess.run(
        ["bash", "scripts/run-structure-quality-gate.sh"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 33, result.stdout + result.stderr
    opl_args = capture_path.read_text(encoding="utf-8")
    assert "quality\n" in opl_args
    assert "details\n" in opl_args
    assert "--root\n" in opl_args
    assert f"{REPO_ROOT}\n" in opl_args
    assert "--compare-ref\norigin/main\n" in opl_args


def test_structure_quality_gate_wrapper_runs_opl_for_sentrux_check_failures(tmp_path: Path) -> None:
    rules_path = REPO_ROOT / ".sentrux" / "rules.toml"
    rules_path.write_text("[constraints]\n", encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    capture_path = tmp_path / "opl.args"
    sentrux_calls_path = tmp_path / "sentrux.calls"
    fake_sentrux = fake_bin / "sentrux"
    fake_sentrux.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$1\" >>\"${MAS_TEST_SENTRUX_CALLS_PATH}\"\n"
        "if [[ \"$1\" == \"check\" ]]; then exit 44; fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_sentrux.chmod(0o755)
    fake_opl = fake_bin / "opl"
    fake_opl.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$@\" >\"${MAS_TEST_CAPTURE_PATH}\"\n",
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["MAS_TEST_CAPTURE_PATH"] = str(capture_path)
    env["MAS_TEST_SENTRUX_CALLS_PATH"] = str(sentrux_calls_path)
    env["OPL_QUALITY_DETAILS_COMPARE_REF"] = "HEAD~1"
    env["OPL_QUALITY_DETAILS_BIN"] = str(fake_opl)

    try:
        result = subprocess.run(
            ["bash", "scripts/run-structure-quality-gate.sh"],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        rules_path.unlink(missing_ok=True)

    assert result.returncode == 44, result.stdout + result.stderr
    assert sentrux_calls_path.read_text(encoding="utf-8").splitlines() == ["gate", "check"]
    assert "--compare-ref\nHEAD~1\n" in capture_path.read_text(encoding="utf-8")


def test_pyproject_registers_meta_display_and_submission_markers() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    markers = pyproject["tool"]["pytest"]["ini_options"]["markers"]
    marker_names = {marker.split(":", maxsplit=1)[0] for marker in markers}

    assert "meta: repo-tracked docs, workflow, packaging, and command-surface checks" in markers
    assert "display_heavy: display materialization and golden-regression tests that dominate wall-clock time" in markers
    assert "submission_heavy: submission package materialization tests that dominate fast-lane wall-clock time" in markers
    assert "family: family shared boundary tests that depend on cross-repo shared-module topology" in markers
    for marker_name in _test_lane_manifest()["marker_registry"]:
        assert marker_name in marker_names


def test_pyproject_dev_dependencies_include_xdist_for_heavy_lanes() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    dev_dependencies = pyproject["dependency-groups"]["dev"]

    assert "pytest-xdist>=3.6" in dev_dependencies


def test_pyproject_pins_opl_harness_shared_to_a_full_commit() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    dependency = next(
        item
        for item in pyproject["project"]["dependencies"]
        if item.startswith("opl-harness-shared @ ")
    )

    assert re.fullmatch(
        r"opl-harness-shared @ git\+https://github\.com/gaofeng21cn/one-person-lab\.git@[0-9a-f]{40}#subdirectory=python/opl-harness-shared",
        dependency,
    )


@pytest.mark.meta
def test_locked_opl_harness_shared_exports_runtime_continuity_contracts() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    dependency = next(
        item
        for item in pyproject["project"]["dependencies"]
        if item.startswith("opl-harness-shared @ ")
    )
    lockfile = _read("uv.lock")

    assert REQUIRED_OPL_SHARED_RUNTIME_CONTINUITY_COMMIT in dependency
    assert f"rev={REQUIRED_OPL_SHARED_RUNTIME_CONTINUITY_COMMIT}" in lockfile
    assert f"#{REQUIRED_OPL_SHARED_RUNTIME_CONTINUITY_COMMIT}" in lockfile

    from opl_harness_shared import product_entry_companions, runtime_task_companions

    for helper_name in (
        "build_session_continuity",
        "build_progress_projection",
        "build_artifact_inventory",
    ):
        assert callable(getattr(runtime_task_companions, helper_name))

    manifest_parameters = inspect.signature(
        product_entry_companions.build_family_product_entry_manifest
    ).parameters
    assert {
        "session_continuity",
        "progress_projection",
        "artifact_inventory",
    }.issubset(manifest_parameters)


def test_verify_script_exposes_named_lanes_for_ci_workflows() -> None:
    verify_script = _read("scripts/verify.sh")

    assert 'repo_root="$(git rev-parse --show-toplevel)"' in verify_script
    assert 'cd "${repo_root}"' in verify_script
    assert "export PYTHONDONTWRITEBYTECODE=1" in verify_script
    assert 'export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:-} -p no:cacheprovider"' in verify_script
    assert "run_sanity_checks() {" in verify_script
    assert "python scripts/repo_hygiene_audit.py" in verify_script
    assert 'PYTHONPATH="${repo_root}/src${PYTHONPATH:+:${PYTHONPATH}}" python scripts/line_budget.py' in verify_script
    assert "git grep -n -I -E '^(<<<<<<< |=======|>>>>>>> |\\|\\|\\|\\|\\|\\|\\| )' -- ." in verify_script
    assert "while IFS= read -r python_file; do" in verify_script
    assert "python_files+=(\"${python_file}\")" in verify_script
    assert "done < <(git ls-files '*.py')" in verify_script
    assert "mapfile" not in verify_script
    assert 'python - "${python_files[@]}" <<\'PY\'' in verify_script
    assert "py_compile.compile(python_file, cfile=str(bytecode_path), doraise=True)" in verify_script
    assert "cleanup_project_entrypoint_artifacts() {" in verify_script
    assert 'rm -rf "${repo_root}/src/med_autoscience.egg-info"' in verify_script
    assert "install_project_entrypoints() {" in verify_script
    assert "trap cleanup_project_entrypoint_artifacts EXIT" in verify_script
    assert "uv pip install --editable . --no-deps" in verify_script
    assert "run_sanity_checks" in verify_script
    assert 'if [[ -z "${lane}" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "smoke" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "regression" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "ci-preflight" ]]; then' in verify_script
    assert 'Usage: scripts/verify.sh ci-preflight <base-ref>' in verify_script
    assert (
        'BASE_REF="${base_ref}" run_with_optional_summary "ci-preflight" '
        '"BASE_REF=${base_ref} make test-ci-preflight" make test-ci-preflight'
    ) in verify_script
    assert 'if [[ "${lane}" == "fast" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "meta" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "display" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "submission" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "structure" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "control-plane" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "full" ]]; then' in verify_script
    assert "MAS_TEST_LANE_SUMMARY_PATH" in verify_script
    assert "run_with_optional_summary" in verify_script
    assert "make test-smoke" in verify_script
    assert "make test-regression" in verify_script
    assert "make test-ci-preflight" in verify_script
    assert "make test-meta" in verify_script
    assert "make test-display" in verify_script
    assert "make test-submission" in verify_script
    assert "make test-structure" in verify_script
    assert "make test-control-plane" in verify_script
    assert "make test-full" in verify_script
    for lane in ("regression", "ci-preflight", "fast", "full", "control-plane"):
        lane_block = verify_script.split(f'if [[ "${{lane}}" == "{lane}" ]]; then', maxsplit=1)[1].split(
            "\nfi",
            maxsplit=1,
        )[0]
        assert "install_project_entrypoints" in lane_block


def test_verify_script_runs_sanity_checks_before_default_dispatch() -> None:
    verify_script = _read("scripts/verify.sh")

    assert "run_sanity_checks\n\njson_escape() {" in verify_script
    assert verify_script.index("run_sanity_checks\n\njson_escape() {") < verify_script.index(
        'if [[ -z "${lane}" ]]; then'
    )
    assert verify_script.index("run_sanity_checks\n\njson_escape() {") < verify_script.index(
        'run_with_optional_summary "smoke" "make test-smoke" make test-smoke'
    )
    for command in (
        'install_project_entrypoints\n  run_with_optional_summary "regression"',
        'install_project_entrypoints\n  BASE_REF="${base_ref}" run_with_optional_summary "ci-preflight"',
        'install_project_entrypoints\n  run_with_optional_summary "fast"',
        'install_project_entrypoints\n  run_with_optional_summary "full"',
        'install_project_entrypoints\n  run_with_optional_summary "control-plane"',
    ):
        assert verify_script.index("run_sanity_checks\n\njson_escape() {") < verify_script.index(command)


def test_verify_script_writes_single_lane_summary(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_make = fake_bin / "make"
    fake_make.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "echo \"fake make $1\"\n",
        encoding="utf-8",
    )
    fake_make.chmod(0o755)
    fake_python = fake_bin / "python"
    fake_python.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "if [[ \"$1\" == \"scripts/repo_hygiene_audit.py\" ]]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [[ \"$1\" == \"scripts/line_budget.py\" ]]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [[ \"$1\" == \"-\" ]]; then\n"
        "  exit 0\n"
        "fi\n"
        "echo \"unexpected fake python $*\" >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    summary_path = tmp_path / "summary" / "smoke.json"
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["MAS_TEST_LANE_SUMMARY_PATH"] = str(summary_path)

    result = subprocess.run(
        ["bash", "scripts/verify.sh", "smoke"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["lanes"][0]["lane"] == "smoke"
    assert summary["lanes"][0]["command"] == "make test-smoke"
    assert summary["lanes"][0]["exit_code"] == 0
    assert isinstance(summary["lanes"][0]["duration_seconds"], int)
    assert summary["lanes"][0]["duration_seconds"] >= 0
    assert summary["lanes"][0]["log_path"] == ""


def test_opl_module_healthcheck_uses_install_readiness_surface() -> None:
    script = _read("scripts/opl-module-healthcheck.sh")

    assert "scripts/verify.sh" not in script
    assert "make test-fast" not in script
    assert 'command -v uv >/dev/null 2>&1' in script
    assert 'command -v medautosci' not in script
    assert 'command -v medautosci-mcp' not in script
    assert 'repo_uv=(uv run --directory "${repo_root}" --extra analysis)' in script
    assert '"${repo_uv[@]}" medautosci --help >/dev/null' in script
    assert '"${repo_uv[@]}" medautosci doctor entry-modes >/dev/null' in script
    assert 'printf \'{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\\n\'' in script
    assert '"${repo_uv[@]}" medautosci-mcp' in script
    assert '"plugins" / "mas" / ".codex-plugin" / "plugin.json"' in script
    assert '"plugins" / "mas" / "skills" / "mas" / "SKILL.md"' in script


def test_parallel_full_lane_script_covers_all_marker_groups() -> None:
    script = _read("scripts/run-parallel-test-lanes.sh")

    assert 'Usage: $0 full' in script
    for lane in PARALLEL_FULL_LANES:
        assert f'"{lane}"' in script
    assert 'make "${lane}"' in script
    assert "MAS_TEST_LANE_SUMMARY_PATH" in script
    assert 'full_lane_pytest_workers="${MAS_FULL_PYTEST_WORKERS:-4}"' in script
    assert 'MAS_PYTEST_WORKERS="${MAS_PYTEST_WORKERS:-${full_lane_pytest_workers}}" make "${lane}"' in script


def test_focused_lane_manifest_exposes_autonomy_reconcile_and_migration_lanes() -> None:
    manifest = _test_lane_manifest()
    focused_lanes = manifest["focused_lanes"]
    expected = {
        "control-plane-autonomy": "read_only_inventory_and_observability",
        "supervisor-reconcile": "scan_consume_execute_rescan_contract",
        "workspace-monolith-migration": "dry_run_before_real_workspace_apply",
    }

    for lane, authority_boundary in expected.items():
        assert lane in focused_lanes
        contract = focused_lanes[lane]
        assert contract["kind"].startswith("focused_")
        assert contract["overlap_policy"] == "allowed_with_regression"
        assert contract["authority_boundary"] == authority_boundary
        assert contract["paths"]
        for path in contract["paths"]:
            assert (REPO_ROOT / path).exists(), f"{lane} references missing test path: {path}"

    assert "tests/test_real_paper_autonomy_soak_inventory.py" in focused_lanes["control-plane-autonomy"]["paths"]
    assert "tests/test_real_paper_autonomy_soak_inventory.py" in focused_lanes["workspace-monolith-migration"]["paths"]


def test_parallel_full_lane_script_writes_summary_and_invokes_make_lanes(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    capture_dir = tmp_path / "captured"
    capture_dir.mkdir()
    summary_path = tmp_path / "summary" / "lanes.json"
    fake_make = fake_bin / "make"
    fake_make.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$1\" >\"${MAS_TEST_CAPTURE_DIR}/$1\"\n"
        "printf '%s\\n' \"$MAS_PYTEST_WORKERS\" >\"${MAS_TEST_CAPTURE_DIR}/$1.workers\"\n"
        "echo \"fake make $1\"\n",
        encoding="utf-8",
    )
    fake_make.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["MAS_TEST_CAPTURE_DIR"] = str(capture_dir)
    env["MAS_TEST_LANE_SUMMARY_PATH"] = str(summary_path)
    result = subprocess.run(
        ["bash", "scripts/run-parallel-test-lanes.sh", "full"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert sorted(path.name for path in capture_dir.iterdir() if not path.name.endswith(".workers")) == sorted(
        PARALLEL_FULL_LANES
    )
    for lane in PARALLEL_FULL_LANES:
        assert (capture_dir / f"{lane}.workers").read_text(encoding="utf-8").strip() == "4"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert [lane["lane"] for lane in summary["lanes"]] == list(PARALLEL_FULL_LANES)
    for lane in summary["lanes"]:
        assert lane["command"] == f"make {lane['lane']}"
        assert lane["exit_code"] == 0
        assert isinstance(lane["duration_seconds"], int)
        assert lane["duration_seconds"] >= 0
        assert Path(lane["log_path"]).exists()
        assert f"[{lane['lane']}] [{lane['lane']}] start" in result.stdout
        assert f"[summary] {lane['lane']}: passed" in result.stdout


def test_parallel_full_lane_script_waits_for_all_lanes_before_failing(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    capture_dir = tmp_path / "captured"
    capture_dir.mkdir()
    summary_path = tmp_path / "summary.json"
    fake_make = fake_bin / "make"
    fake_make.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$1\" >\"${MAS_TEST_CAPTURE_DIR}/$1\"\n"
        "printf '%s\\n' \"$MAS_PYTEST_WORKERS\" >\"${MAS_TEST_CAPTURE_DIR}/$1.workers\"\n"
        "echo \"fake make $1\"\n"
        "if [[ \"$1\" == \"${MAS_TEST_FAIL_LANE}\" ]]; then\n"
        "  echo \"failing $1\"\n"
        "  exit 7\n"
        "fi\n",
        encoding="utf-8",
    )
    fake_make.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["MAS_TEST_CAPTURE_DIR"] = str(capture_dir)
    env["MAS_TEST_FAIL_LANE"] = "test-display"
    env["MAS_TEST_LANE_SUMMARY_PATH"] = str(summary_path)
    result = subprocess.run(
        ["bash", "scripts/run-parallel-test-lanes.sh", "full"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert sorted(path.name for path in capture_dir.iterdir() if not path.name.endswith(".workers")) == sorted(
        PARALLEL_FULL_LANES
    )
    for lane in PARALLEL_FULL_LANES:
        assert (capture_dir / f"{lane}.workers").read_text(encoding="utf-8").strip() == "4"
    for lane in PARALLEL_FULL_LANES:
        assert f"[{lane}] fake make {lane}" in result.stdout
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    exit_codes = {lane["lane"]: lane["exit_code"] for lane in summary["lanes"]}
    assert exit_codes == {
        "test-regression": 0,
        "test-meta": 0,
        "test-display": 7,
        "test-submission": 0,
        "test-family": 0,
    }
    assert "[summary] test-display: failed (exit 7" in result.stdout


def test_family_lane_test_files_are_marker_scoped_to_avoid_full_lane_overlap() -> None:
    family_release = _read("tests/test_family_shared_release.py")
    editable_bootstrap = _read("tests/test_editable_shared_bootstrap.py")
    dev_preflight_contract = _read("tests/test_dev_preflight_contract.py")
    dev_preflight = _read("tests/test_dev_preflight.py")

    assert "pytestmark = pytest.mark.family" in family_release
    assert "pytestmark = pytest.mark.family" in editable_bootstrap
    assert "pytestmark = pytest.mark.family" in dev_preflight_contract
    assert "pytestmark = pytest.mark.family" in dev_preflight


def test_control_plane_operation_command_catalog_guards_cli_mcp_manifest_and_schema_surfaces() -> None:
    from med_autoscience import cli, domain_entry_contract, mcp_server

    parser = cli.build_parser()
    cli_commands: set[str] = set()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            cli_commands.update(action.choices)

    mcp_tools = {tool["name"]: tool for tool in mcp_server.build_tool_manifest()}
    mcp_modes = set(mcp_tools["product_entry"]["inputSchema"]["properties"]["mode"]["enum"])
    domain_catalog = domain_entry_contract.build_domain_entry_command_catalog()
    product_entry_manifest_contract = domain_entry_contract.build_domain_entry_contract()
    schema = json.loads(_read("contracts/schemas/v1/product-entry-manifest.schema.json"))
    supported_command_enum = set(
        schema["$defs"]["domainEntryContract"]["properties"]["supported_commands"]["items"]["enum"]
    )
    catalog_commands = {spec.command for spec in CONTROL_PLANE_OPERATIONS_COMMANDS}
    schema_control_plane_commands = {
        command for command in supported_command_enum if command.startswith("control-plane-")
    }

    _assert_command_surface_matches_catalog(
        surface="cli",
        expected_commands=catalog_commands,
        actual_commands={command for command in cli_commands if command.startswith("control-plane-")},
    )
    _assert_mcp_modes_cover_catalog(
        expected=CONTROL_PLANE_OPERATIONS_COMMANDS,
        actual_modes=mcp_modes,
    )
    _assert_command_surface_matches_catalog(
        surface="product_entry_manifest",
        expected_commands=catalog_commands,
        actual_commands={
            command
            for command in product_entry_manifest_contract["supported_commands"]
            if command.startswith("control-plane-")
        },
    )
    _assert_command_surface_matches_catalog(
        surface="domain_entry_command_catalog",
        expected_commands=catalog_commands,
        actual_commands={
            item["command"]
            for item in domain_catalog["command_contracts"]
            if item["command"].startswith("control-plane-")
        },
    )
    _assert_command_surface_matches_catalog(
        surface="schema",
        expected_commands=catalog_commands,
        actual_commands=schema_control_plane_commands,
    )

    manifest_contracts = {
        item["command"]: item
        for item in product_entry_manifest_contract["command_contracts"]
        if item["command"].startswith("control-plane-")
    }
    for spec in CONTROL_PLANE_OPERATIONS_COMMANDS:
        assert manifest_contracts.get(spec.command) == spec.command_contract(), (
            "control-plane command contract drift: "
            f"command={spec.command!r} "
            f"manifest_contract={manifest_contracts.get(spec.command)!r} "
            f"catalog_contract={spec.command_contract()!r}"
        )
