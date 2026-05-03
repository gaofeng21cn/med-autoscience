from __future__ import annotations

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
REQUIRED_OPL_SHARED_RUNTIME_CONTINUITY_COMMIT = "9b02ce03bf079db0257959c3219a1fd2b1ad1364"
REQUIRED_CONTROL_PLANE_TESTS = (
    "tests/test_control_plane_regression.py",
    "tests/test_control_plane_structure.py",
    "tests/test_study_control_plane_kernel.py",
    "tests/test_control_plane_state_machine.py",
    "tests/test_study_runtime_typed_surface_cases/status_type_cases.py",
    "tests/test_control_plane_route_gate.py",
    "tests/test_artifact_lifecycle_inventory.py",
    "tests/test_artifact_lifecycle_operations_report.py",
    "tests/test_runtime_protocol_paper_artifacts.py",
    "tests/test_study_delivery_sync.py",
    "tests/test_runtime_storage_maintenance.py",
    "tests/test_control_plane_cleanup_apply.py",
    "tests/test_control_plane_migration_audit.py",
    "tests/test_cli_cases/public_entry_commands.py::test_migration_audit_command_dispatches_read_only_controller",
    "tests/test_cli_cases/public_entry_commands.py::test_cleanup_apply_command_dispatches_controller",
    "tests/test_cli_cases/public_entry_commands.py::test_lifecycle_report_command_dispatches_read_only_controller",
    "tests/test_mcp_server.py::test_mcp_product_entry_description_documents_control_plane_operations_surfaces",
    "tests/test_mcp_server.py::test_mcp_product_entry_schema_accepts_control_plane_operations_options",
    "tests/test_mcp_server.py::test_mcp_product_entry_can_call_migration_audit",
    "tests/test_mcp_server.py::test_mcp_product_entry_can_call_cleanup_apply",
    "tests/test_mcp_server.py::test_mcp_product_entry_can_call_lifecycle_report",
    "tests/test_test_command_surfaces.py::test_control_plane_operation_command_catalog_guards_cli_mcp_manifest_and_schema_surfaces",
    "tests/test_installed_mcp_smoke.py::test_installed_medautosci_mcp_lists_control_plane_operation_modes",
    "tests/test_truth_projection_surfaces.py",
)
PARALLEL_FULL_LANES = (
    "test-regression",
    "test-meta",
    "test-display",
    "test-submission",
    "test-family",
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_makefile_exposes_layered_test_entrypoints() -> None:
    makefile = _read("Makefile")

    assert "test-control-plane:" in makefile
    assert "CONTROL_PLANE_TESTS :=" in makefile
    for test_path in REQUIRED_CONTROL_PLANE_TESTS:
        assert test_path in makefile
    assert "PYTHONPATH=src uv run pytest -q $(CONTROL_PLANE_TESTS)" in makefile
    assert "test: test-smoke" in makefile
    assert "test-smoke:" in makefile
    assert "uv run pytest tests/test_test_command_surfaces.py tests/test_line_budget.py -q" in makefile
    assert "test-regression:" in makefile
    assert 'uv run pytest -q -m "not meta and not display_heavy and not submission_heavy and not family"' in makefile
    assert "test-ci-preflight:" in makefile
    assert 'uv run python -m med_autoscience.cli doctor preflight --base-ref "$${BASE_REF}"' in makefile
    assert "test-fast: test-regression" in makefile
    assert "test-meta:" in makefile
    assert "uv run pytest -q -m meta" in makefile
    assert "test-display:" in makefile
    assert "uv run pytest -q -m display_heavy" in makefile
    assert "test-submission:" in makefile
    assert "uv run pytest -q -m submission_heavy" in makefile
    assert "test-family:" in makefile
    assert (
        "uv run pytest tests/test_family_shared_release.py tests/test_editable_shared_bootstrap.py "
        "tests/test_dev_preflight_contract.py tests/test_dev_preflight.py -q"
    ) in makefile
    assert "test-structure:" in makefile
    assert "uv run python scripts/line_budget.py" in makefile
    assert "sentrux gate" in makefile
    assert "test-full:" in makefile
    assert "./scripts/run-parallel-test-lanes.sh full" in makefile


def test_pyproject_registers_meta_display_and_submission_markers() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    markers = pyproject["tool"]["pytest"]["ini_options"]["markers"]

    assert "meta: repo-tracked docs, workflow, packaging, and command-surface checks" in markers
    assert "display_heavy: display materialization and golden-regression tests that dominate wall-clock time" in markers
    assert "submission_heavy: submission package materialization tests that dominate fast-lane wall-clock time" in markers
    assert "family: family shared boundary tests that depend on cross-repo shared-module topology" in markers


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
    assert "run_sanity_checks() {" in verify_script
    assert "git grep -n -I -E '^(<<<<<<< |=======|>>>>>>> |\\|\\|\\|\\|\\|\\|\\| )' -- ." in verify_script
    assert "while IFS= read -r python_file; do" in verify_script
    assert "python_files+=(\"${python_file}\")" in verify_script
    assert "done < <(git ls-files '*.py')" in verify_script
    assert "mapfile" not in verify_script
    assert 'uv run python -m py_compile "${python_files[@]}"' in verify_script
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


def test_verify_script_runs_sanity_checks_before_default_dispatch() -> None:
    verify_script = _read("scripts/verify.sh")

    assert "run_sanity_checks\n\njson_escape() {" in verify_script
    assert verify_script.index("run_sanity_checks\n\njson_escape() {") < verify_script.index(
        'if [[ -z "${lane}" ]]; then'
    )
    assert verify_script.index("run_sanity_checks\n\njson_escape() {") < verify_script.index(
        'run_with_optional_summary "smoke" "make test-smoke" make test-smoke'
    )


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
    assert 'medautosci_bin="$(command -v medautosci)"' in script
    assert 'medautosci_mcp_bin="$(command -v medautosci-mcp)"' in script
    assert '"${medautosci_bin}" --help >/dev/null' in script
    assert '"${medautosci_bin}" doctor entry-modes >/dev/null' in script
    assert 'printf \'{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\\n\'' in script
    assert '"${medautosci_mcp_bin}"' in script
    assert '"plugins" / "mas" / ".codex-plugin" / "plugin.json"' in script
    assert '"plugins" / "mas" / "skills" / "mas" / "SKILL.md"' in script


def test_parallel_full_lane_script_covers_all_marker_groups() -> None:
    script = _read("scripts/run-parallel-test-lanes.sh")

    assert 'Usage: $0 full' in script
    for lane in PARALLEL_FULL_LANES:
        assert f'"{lane}"' in script
    assert 'make "${lane}"' in script
    assert "MAS_TEST_LANE_SUMMARY_PATH" in script


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
    assert sorted(path.name for path in capture_dir.iterdir()) == sorted(PARALLEL_FULL_LANES)
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
    assert sorted(path.name for path in capture_dir.iterdir()) == sorted(PARALLEL_FULL_LANES)
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
    cli_parser = _read("src/med_autoscience/cli_parts/parser.py")
    cli_main = _read("src/med_autoscience/cli.py")
    mcp_server = _read("src/med_autoscience/mcp_server.py")
    domain_entry_contract = _read("src/med_autoscience/domain_entry_contract.py")
    schema = json.loads(_read("contracts/schemas/v1/product-entry-manifest.schema.json"))
    supported_command_enum = set(
        schema["$defs"]["domainEntryContract"]["properties"]["supported_commands"]["items"]["enum"]
    )

    for spec in CONTROL_PLANE_OPERATIONS_COMMANDS:
        assert f'add_parser("{spec.cli_command}")' in cli_parser
        assert f'args.command == "{spec.cli_command}"' in cli_main
        assert f'if mode == "{spec.mcp_mode}"' in mcp_server
        assert "CONTROL_PLANE_OPERATIONS_COMMANDS" in domain_entry_contract
        assert "item.command: item" in domain_entry_contract
        assert spec.command in supported_command_enum
