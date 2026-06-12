from __future__ import annotations

from .. import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_resolve_journal_shortlist_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_resolve(*, study_root: Path) -> dict[str, object]:
        called["study_root"] = study_root
        return {"status": "resolved", "shortlist": ["Heart"], "candidate_count": 1}

    monkeypatch.setattr(cli.journal_shortlist_controller, "resolve_journal_shortlist", fake_resolve)

    exit_code = cli.main(["publication", "resolve-journal-shortlist", "--study-root", str(tmp_path / "study")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["study_root"] == tmp_path / "study"
    assert '"status": "resolved"' in captured.out


def test_publication_aftercare_plan_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_aftercare(*, study_root: Path, quest_root: Path | None = None) -> dict[str, object]:
        called["study_root"] = study_root
        called["quest_root"] = quest_root
        return {
            "surface_kind": "mas_publication_aftercare_plan",
            "analysis_queue_entry": {"status": "ready"},
        }

    monkeypatch.setattr(cli.publication_aftercare, "build_publication_aftercare_plan", fake_aftercare)

    exit_code = cli.main(
        [
            "publication",
            "aftercare-plan",
            "--study-root",
            str(tmp_path / "study"),
            "--quest-root",
            str(tmp_path / "quest"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["study_root"] == tmp_path / "study"
    assert called["quest_root"] == tmp_path / "quest"
    assert '"surface_kind": "mas_publication_aftercare_plan"' in captured.out


def test_resolve_journal_requirements_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_resolve(
        *,
        study_root: Path,
        journal_name: str | None = None,
        journal_slug: str | None = None,
        official_guidelines_url: str | None = None,
        publication_profile: str | None = None,
        requirements_payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        called["study_root"] = study_root
        called["journal_name"] = journal_name
        called["journal_slug"] = journal_slug
        called["official_guidelines_url"] = official_guidelines_url
        called["publication_profile"] = publication_profile
        called["requirements_payload"] = requirements_payload
        return {"status": "resolved", "journal_slug": "rheumatology-international"}

    monkeypatch.setattr(cli.journal_requirements_controller, "resolve_journal_requirements", fake_resolve)

    exit_code = cli.main(
        [
            "publication",
            "resolve-journal-requirements",
            "--study-root",
            str(tmp_path / "study"),
            "--journal-name",
            "Rheumatology International",
            "--official-guidelines-url",
            "https://example.org/ri-guide",
            "--publication-profile",
            "general_medical_journal",
            "--requirements-json",
            '{"abstract_word_cap": 250}',
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["study_root"] == tmp_path / "study"
    assert called["journal_name"] == "Rheumatology International"
    assert called["official_guidelines_url"] == "https://example.org/ri-guide"
    assert called["publication_profile"] == "general_medical_journal"
    assert called["requirements_payload"] == {"abstract_word_cap": 250}
    assert '"journal_slug": "rheumatology-international"' in captured.out


def test_init_portfolio_memory_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {"portfolio_memory_root": str(workspace_root / "memory" / "portfolio" / "research_memory"), "created_files": []}

    monkeypatch.setattr(cli.portfolio_memory_controller, "init_portfolio_memory", fake_init)

    exit_code = cli.main(["data", "init-memory", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"portfolio_memory_root"' in captured.out


def test_portfolio_memory_status_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {"portfolio_memory_exists": True, "asset_count": 3}

    monkeypatch.setattr(cli.portfolio_memory_controller, "portfolio_memory_status", fake_status)

    exit_code = cli.main(["data", "memory-status", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"asset_count": 3' in captured.out


def test_init_workspace_literature_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {
            "workspace_literature_root": str(workspace_root / "memory" / "portfolio" / "research_memory" / "literature"),
            "created_files": [],
        }

    monkeypatch.setattr(cli.workspace_literature_controller, "init_workspace_literature", fake_init)

    exit_code = cli.main(["data", "init-literature", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"workspace_literature_root"' in captured.out


def test_workspace_literature_status_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {"workspace_literature_exists": True, "record_count": 7}

    monkeypatch.setattr(cli.workspace_literature_controller, "workspace_literature_status", fake_status)

    exit_code = cli.main(["data", "literature-status", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"record_count": 7' in captured.out
