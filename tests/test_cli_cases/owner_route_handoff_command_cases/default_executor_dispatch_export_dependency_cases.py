from __future__ import annotations

from .default_executor_dispatch_export_cases import _write_default_executor_dispatch
from .shared import *  # noqa: F403,F401
import builtins


def test_domain_handler_export_default_executor_dispatch_does_not_require_pdf_dependency(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    for module_name in list(sys.modules):
        if (
            module_name == "pypdf"
            or module_name.startswith("pypdf.")
            or module_name == "med_autoscience.cli"
            or module_name == "med_autoscience.controllers.owner_route_handoff"
            or module_name.startswith("med_autoscience.controllers.owner_route_handoff_parts.")
            or module_name == "med_autoscience.controllers.submission_minimal"
        ):
            sys.modules.pop(module_name, None)

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pypdf" or name.startswith("pypdf."):
            raise ModuleNotFoundError("No module named 'pypdf'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_default_executor_dispatch(
        dispatch_path=dispatch_path,
        study_root=study_root,
        include_owner_route=True,
    )

    cli = importlib.import_module("med_autoscience.cli")
    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [
        task["task_kind"]
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ] == ["domain_owner/default-executor-dispatch"]
