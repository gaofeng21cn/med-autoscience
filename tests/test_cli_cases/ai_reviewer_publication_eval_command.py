from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_publication_ai_reviewer_eval_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    payload_file = tmp_path / "publication_eval.json"
    payload_file.write_text(
        json.dumps(
            {
                "eval_id": "publication-eval::001-risk::quest-001::2026-04-26T22:00:00+00:00",
                "assessment_provenance": {"owner": "ai_reviewer"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    called: dict[str, object] = {}

    def fake_materialize(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        record: dict,
        source: str,
    ) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["record"] = record
        called["source"] = source
        return {
            "status": "materialized",
            "eval_id": record["eval_id"],
            "assessment_owner": record["assessment_provenance"]["owner"],
        }

    monkeypatch.setattr(
        cli.ai_reviewer_publication_eval,
        "materialize_ai_reviewer_publication_eval",
        fake_materialize,
    )

    exit_code = cli.main(
        [
            "publication",
            "materialize-ai-reviewer-eval",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--payload-file",
            str(payload_file),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] is None
    assert called["record"]["assessment_provenance"]["owner"] == "ai_reviewer"
    assert called["source"] == "cli"
    assert json.loads(captured.out)["assessment_owner"] == "ai_reviewer"
