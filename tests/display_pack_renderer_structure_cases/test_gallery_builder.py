from __future__ import annotations

from .common import (
    CORE_PACK_MODULE_ROOT,
    CORE_PACK_ROOT,
    CORE_PACK_SRC_ROOT,
    REPO_ROOT,
    SimpleNamespace,
    _candidate_request,
    importlib,
    json,
    os,
    subprocess,
    sys,
    tempfile,
    tomllib,
    Path,
)


def test_gallery_builder_fails_closed_without_opl_dependency_run_context(tmp_path: Path) -> None:
    script_path = REPO_ROOT / "scripts" / "build-display-pack-gallery.py"
    env = dict(os.environ)
    env.pop("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_PATH", None)
    env.pop("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_REF", None)
    env.pop("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_FINGERPRINT", None)
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--force-render",
            "--output-root",
            str(tmp_path / "gallery-output"),
        ],
        cwd=REPO_ROOT,
        env={**env, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode != 0
    assert "requires OPL-prepared dependency run-context" in result.stderr


def test_core_r_evidence_renderer_finds_helpers_when_invoked_by_absolute_path() -> None:
    renderer_path = CORE_PACK_ROOT / "rlib" / "medicaldisplaycore" / "evidence_renderer.R"
    text = renderer_path.read_text(encoding="utf-8")

    assert 'grep("^--file=", script_args, value = TRUE)' in text
    assert "file.path(script_dir, file_name)" in text


def test_gallery_r_renderers_apply_opl_dependency_run_context(monkeypatch, tmp_path: Path) -> None:
    from med_autoscience.display_pack_gallery_catalog import TemplateRecord
    from med_autoscience.display_pack_gallery_parts import paths
    from med_autoscience.display_pack_gallery_parts import rendering

    paths.configure_output_paths(tmp_path / "gallery")
    run_context_path = tmp_path / "dependency_run_context.json"
    run_context_path.write_text(
        json.dumps(
                {
                    "surface_kind": "opl_runtime_environment_dependency_run_context",
                    "status": "prepared",
                    "selected_requirement_profile_ids": [
                        "r_ggplot2_evidence_subprocess_v1",
                        "r_ggplot2_alluvial_transition_v1",
                        "r_ggplot2_ggconsort_reporting_flow_v1",
                    ],
                    "binary_paths": {"Rscript": "/opt/opl/bin/Rscript"},
                    "env_vars": {
                    "OPL_RUNTIME_ENVIRONMENT_STATUS": "prepared",
                    "R_LIBS_USER": str(tmp_path / "opl-managed-r-lib"),
                },
                "execution_fingerprint": "sha256:test-opl-run-context",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_PATH", str(run_context_path))
    monkeypatch.setenv("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_FINGERPRINT", "sha256:test-opl-run-context")
    monkeypatch.setattr(
        rendering,
        "_load_r_gallery_payload",
        lambda template_id, seed_payloads: {"title": template_id},
    )
    monkeypatch.setattr(
        "med_autoscience.display_pack_gallery_parts.dependency_run_context._missing_required_r_packages",
        lambda **kwargs: [],
    )

    record = TemplateRecord(
        template_id="alluvial_transition",
        full_template_id="fenggaolab.org.medical-display-core::alluvial_transition",
        display_name="Alluvial Transition",
        kind="evidence_figure",
        audit_family="Publication",
        renderer_family="r_ggplot2",
        execution_mode="subprocess",
        entrypoint="Rscript render.R --request {request_json}",
        paper_proven=False,
        required_exports=("png", "pdf"),
        template_dir=CORE_PACK_ROOT / "templates" / "alluvial_transition",
        canonical_family_id="",
        canonical_family_title="",
        canonical_family_category="",
        canonical_template_id="alluvial_transition",
        figure_archetype="",
        migration_status="canonical",
        default_visible=True,
        migrated_alias_template_ids=(),
        migration_reason="",
        analysis_responsibility="",
        analysis_input_state="",
        medical_family_ids=(),
        publication_quality_profile={},
    )
    preview_record = TemplateRecord(
        template_id="table1_baseline_characteristics",
        full_template_id="fenggaolab.org.medical-display-core::table1_baseline_characteristics",
        display_name="Table 1 Baseline Characteristics",
        kind="table_shell",
        audit_family="Publication Shells and Tables",
        renderer_family="n/a",
        execution_mode="python_plugin",
        entrypoint="fenggaolab_org_medical_display_core.table_shells:render_table_shell",
        paper_proven=False,
        required_exports=("csv", "md"),
        template_dir=CORE_PACK_ROOT / "templates" / "table1_baseline_characteristics",
        canonical_family_id="",
        canonical_family_title="",
        canonical_family_category="",
        canonical_template_id="table1_baseline_characteristics",
        figure_archetype="",
        migration_status="canonical",
        default_visible=True,
        migrated_alias_template_ids=(),
        migration_reason="",
        analysis_responsibility="",
        analysis_input_state="",
        medical_family_ids=(),
        publication_quality_profile={},
    )
    cohort_flow_record = TemplateRecord(
        template_id="cohort_flow_figure",
        full_template_id="fenggaolab.org.medical-display-core::cohort_flow_figure",
        display_name="Cohort Flow Figure",
        kind="illustration_shell",
        audit_family="Publication Shells and Tables",
        renderer_family="r_ggplot2",
        execution_mode="subprocess",
        entrypoint="Rscript render.R --request {request_json}",
        paper_proven=False,
        required_exports=("png", "pdf"),
        template_dir=CORE_PACK_ROOT / "templates" / "cohort_flow_figure",
        canonical_family_id="",
        canonical_family_title="",
        canonical_family_category="",
        canonical_template_id="cohort_flow_figure",
        figure_archetype="",
        migration_status="canonical",
        default_visible=True,
        migrated_alias_template_ids=(),
        migration_reason="",
        analysis_responsibility="",
        analysis_input_state="",
        medical_family_ids=(),
        publication_quality_profile={},
    )
    calls: list[dict[str, object]] = []
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00"
        b"\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def fake_run(argv, *, cwd, capture_output, text, check, timeout, env):
        request_path = Path(argv[-1])
        request_payload = json.loads(request_path.read_text(encoding="utf-8"))
        calls.append(
            {
                "argv": list(argv),
                "env": dict(env),
                "request": request_payload,
                "cwd": Path(cwd),
            }
        )
        Path(request_payload["output_png_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(request_payload["output_png_path"]).write_bytes(png_bytes)
        Path(request_payload["output_pdf_path"]).write_bytes(b"%PDF-1.4\n")
        Path(request_payload["layout_sidecar_path"]).write_text(
            json.dumps({"template_id": request_payload["short_template_id"]}) + "\n",
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(rendering.subprocess, "run", fake_run)

    rendering._render_r_template(record, {}, force_render=True)
    rendering._render_r_gallery_preview(preview_record, {}, force_render=True)
    rendering._render_r_template(cohort_flow_record, {}, force_render=True)

    assert len(calls) == 3
    assert {call["request"]["short_template_id"] for call in calls} == {
        "alluvial_transition",
        "table1_baseline_characteristics",
        "cohort_flow_figure",
    }
    for call in calls:
        expected_profile_ids = {
            "r_ggplot2_evidence_subprocess_v1",
            "r_ggplot2_alluvial_transition_v1",
        } if call["request"]["short_template_id"] == "alluvial_transition" else (
            {
                "r_ggplot2_evidence_subprocess_v1",
                "r_ggplot2_ggconsort_reporting_flow_v1",
            } if call["request"]["short_template_id"] == "cohort_flow_figure" else {
                "r_ggplot2_evidence_subprocess_v1",
            }
        )
        assert call["argv"][0] == "/opt/opl/bin/Rscript"
        assert call["env"]["R_LIBS_USER"] == str(tmp_path / "opl-managed-r-lib")
        assert call["env"]["OPL_RUNTIME_ENVIRONMENT_STATUS"] == "prepared"
        dependency_environment = call["request"]["dependency_environment"]
        assert dependency_environment["status"] == "prepared"
        assert dependency_environment["run_context_ref"] == str(run_context_path)
        assert dependency_environment["run_context_fingerprint"] == "sha256:test-opl-run-context"
        assert set(dependency_environment["required_profile_ids"].split(",")) == expected_profile_ids
        dependency_cache_context = call["request"]["dependency_cache_context"]
        assert dependency_cache_context["status"] == "prepared"
        assert dependency_cache_context["run_context_ref"] == str(run_context_path)
        assert dependency_cache_context["run_context_fingerprint"] == "sha256:test-opl-run-context"
        assert set(dependency_cache_context["required_profile_ids"].split(",")) == expected_profile_ids
        assert dependency_cache_context["rscript_path"] == "/opt/opl/bin/Rscript"
        assert dependency_cache_context["r_libs_user"] == str(tmp_path / "opl-managed-r-lib")


def test_gallery_builder_packages_cached_assets_by_default(monkeypatch, tmp_path: Path, capsys) -> None:
    from med_autoscience.display_pack_gallery_parts import cli as gallery_cli

    calls: dict[str, object] = {
        "clean_assets": 0,
        "force_render_values": [],
    }

    def fake_manifest(
        *,
        records,
        rendered,
        baseline_rendered,
        publish_docs,
        render_cache_summary,
        force_render,
        package_only,
    ):
        return {
            "quality_audit": {
                "overall_status": "not_publication_ready",
                "publication_ready_claim_authorized": False,
            },
            "design_gallery_template_count": 0,
            "non_visual_canonical_template_count": 0,
            "rendered_image_template_count": 0,
            "internal_rendered_image_template_count": 0,
            "lidocaineq_reference_coverage": {
                "reference_template_count": 0,
                "covered_reference_template_count": 0,
                "coverage_complete": True,
                "missing_or_downgraded_reference_template_ids": [],
                "replacement_template_count": 0,
                "do_not_restore_legacy_alias_count": 0,
            },
            "quality_overall_status": "not_publication_ready",
            "force_render": force_render,
            "package_only": package_only,
            "render_cache_summary": render_cache_summary,
        }

    def fake_render_records(records, *, force_render, package_only):
        calls["force_render_values"].append((force_render, package_only))
        return {}, {}

    def fake_clean_assets() -> None:
        calls["clean_assets"] = int(calls["clean_assets"]) + 1

    def fake_write_reference(records, rendered, baseline_rendered, *, reference_path: Path) -> None:
        reference_path.parent.mkdir(parents=True, exist_ok=True)
        reference_path.write_text("reference\n", encoding="utf-8")

    monkeypatch.setattr(gallery_cli.shutil, "which", lambda name: "/usr/bin/Rscript" if name == "Rscript" else None)
    monkeypatch.setattr(gallery_cli, "read_template_records", lambda *_: [])
    monkeypatch.setattr(gallery_cli, "_render_records", fake_render_records)
    monkeypatch.setattr(gallery_cli, "_clean_assets", fake_clean_assets)
    monkeypatch.setattr(gallery_cli, "_render_html", lambda *_: "<html></html>")
    monkeypatch.setattr(gallery_cli, "_write_reference", fake_write_reference)
    monkeypatch.setattr(gallery_cli, "build_manifest", fake_manifest)
    monkeypatch.setattr(gallery_cli, "build_quality_audit_markdown", lambda *_: "quality\n")
    monkeypatch.setattr(gallery_cli, "build_gallery_status_markdown", lambda *_: "status\n")
    monkeypatch.setattr(gallery_cli, "_export_pdf", lambda: None)

    assert gallery_cli.main(["--output-root", str(tmp_path / "default")]) == 0
    default_stdout = json.loads(capsys.readouterr().out)
    assert default_stdout["force_render"] is False
    assert calls["force_render_values"] == [(False, False)]
    assert calls["clean_assets"] == 0

    assert gallery_cli.main(["--output-root", str(tmp_path / "force"), "--force-render"]) == 0
    force_stdout = json.loads(capsys.readouterr().out)
    assert force_stdout["force_render"] is True
    assert calls["force_render_values"] == [(False, False), (True, False)]
    assert calls["clean_assets"] == 1


def test_gallery_builder_package_only_skips_renderer_preflight(monkeypatch, tmp_path: Path, capsys) -> None:
    from med_autoscience.display_pack_gallery_parts import cli as gallery_cli

    calls: dict[str, object] = {
        "which": [],
        "render_records": [],
    }

    def fake_manifest(
        *,
        records,
        rendered,
        baseline_rendered,
        publish_docs,
        render_cache_summary,
        force_render,
        package_only,
    ):
        return {
            "quality_audit": {
                "overall_status": "not_publication_ready",
                "publication_ready_claim_authorized": False,
            },
            "design_gallery_template_count": 0,
            "non_visual_canonical_template_count": 0,
            "rendered_image_template_count": 0,
            "internal_rendered_image_template_count": 0,
            "lidocaineq_reference_coverage": {
                "reference_template_count": 0,
                "covered_reference_template_count": 0,
                "coverage_complete": True,
                "missing_or_downgraded_reference_template_ids": [],
                "replacement_template_count": 0,
                "do_not_restore_legacy_alias_count": 0,
            },
            "force_render": force_render,
            "package_only": package_only,
            "render_cache_summary": render_cache_summary,
        }

    def fake_render_records(records, *, force_render, package_only):
        calls["render_records"].append((force_render, package_only))
        return {}, {}

    def fake_which(name: str) -> None:
        calls["which"].append(name)
        return None

    def fake_write_reference(records, rendered, baseline_rendered, *, reference_path: Path) -> None:
        reference_path.parent.mkdir(parents=True, exist_ok=True)
        reference_path.write_text("reference\n", encoding="utf-8")

    monkeypatch.setattr(gallery_cli.shutil, "which", fake_which)
    monkeypatch.setattr(gallery_cli, "read_template_records", lambda *_: [])
    monkeypatch.setattr(gallery_cli, "_render_records", fake_render_records)
    monkeypatch.setattr(gallery_cli, "_render_html", lambda *_: "<html></html>")
    monkeypatch.setattr(gallery_cli, "_write_reference", fake_write_reference)
    monkeypatch.setattr(gallery_cli, "build_manifest", fake_manifest)
    monkeypatch.setattr(gallery_cli, "build_quality_audit_markdown", lambda *_: "quality\n")
    monkeypatch.setattr(gallery_cli, "build_gallery_status_markdown", lambda *_: "status\n")
    monkeypatch.setattr(gallery_cli, "_export_pdf", lambda: None)

    assert gallery_cli.main(["--output-root", str(tmp_path / "package-only"), "--package-only"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["package_only"] is True
    assert calls["which"] == []
    assert calls["render_records"] == [(False, True)]


def test_gallery_builder_package_only_fails_closed_without_assets(monkeypatch, tmp_path: Path) -> None:
    from med_autoscience.display_pack_gallery_catalog import TemplateRecord
    from med_autoscience.display_pack_gallery_parts import cli as gallery_cli

    record = TemplateRecord(
        template_id="roc_curve_binary",
        full_template_id="fenggaolab.org.medical-display-core::roc_curve_binary",
        display_name="ROC Curve",
        kind="evidence_figure",
        audit_family="Prediction Performance",
        renderer_family="r_ggplot2",
        execution_mode="subprocess",
        entrypoint="Rscript render.R --request {request_json}",
        paper_proven=False,
        required_exports=("png", "pdf"),
        template_dir=CORE_PACK_ROOT / "templates" / "roc_curve_binary",
        canonical_family_id="roc_curve_binary",
        canonical_family_title="ROC Curve",
        canonical_family_category="Prediction Performance",
        canonical_template_id="roc_curve_binary",
        figure_archetype="curve",
        migration_status="canonical",
        default_visible=True,
        migrated_alias_template_ids=(),
        migration_reason="",
        analysis_responsibility="validated_summary_required",
        analysis_input_state="validated_summary",
        medical_family_ids=("prediction_model_performance",),
        publication_quality_profile={},
    )

    monkeypatch.setattr(gallery_cli.shutil, "which", lambda _: None)
    monkeypatch.setattr(gallery_cli, "read_template_records", lambda *_: [record])

    try:
        gallery_cli.main(["--output-root", str(tmp_path / "package-only"), "--package-only"])
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("package-only gallery build should fail when required assets are absent")

    assert "package-only gallery build requires existing rendered gallery assets" in message
    assert "roc_curve_binary.png" in message
    assert "local output gallery assets" in message


def test_package_only_asset_seed_updates_stale_target_files(tmp_path: Path) -> None:
    from med_autoscience.display_pack_gallery_parts.asset_reuse import seed_package_only_assets

    source_root = tmp_path / "docs_assets"
    target_root = tmp_path / "output_assets"
    source_root.mkdir()
    target_root.mkdir()
    (source_root / "submission_graphical_abstract.design.png").write_bytes(b"fresh-ga")
    (target_root / "submission_graphical_abstract.design.png").write_bytes(b"stale-ga")
    (source_root / "submission_graphical_abstract.design.layout.json").write_text('{"layout":"fresh"}\n', encoding="utf-8")

    result = seed_package_only_assets(source_asset_root=source_root, target_asset_root=target_root)

    assert result["status"] == "synced_from_source_assets"
    assert result["updated_file_count"] == 1
    assert result["copied_file_count"] == 1
    assert result["skipped_existing_count"] == 0
    assert (target_root / "submission_graphical_abstract.design.png").read_bytes() == b"fresh-ga"
    assert (target_root / "submission_graphical_abstract.design.layout.json").read_text(encoding="utf-8") == '{"layout":"fresh"}\n'
