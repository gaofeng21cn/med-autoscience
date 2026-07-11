from med_autoscience.controllers import stage_knowledge_entry, stage_knowledge_visibility


def _ref(source_ref: str, digest: str = "sha256-value") -> dict[str, str]:
    return {"source_ref": source_ref, "payload_sha256": digest, "source_family": "stage_folder_refs"}


def test_stage_entry_consumes_explicit_opl_refs_without_local_materialization() -> None:
    entry = stage_knowledge_entry.build_stage_knowledge_entry(
        study_id="S1",
        stage="review",
        stage_folder_refs=[_ref("opl-stage-folder://S1/review/current.json")],
        state_index_refs=[_ref("opl-state-index://S1/review")],
    )

    assert entry["status"] == "ready"
    assert entry["consumed_refs"] == [
        "opl-stage-folder://S1/review/current.json",
        "opl-state-index://S1/review",
    ]
    assert entry["authority_boundary"]["local_persistence"] == "absent"


def test_stage_visibility_never_discovers_receipts_by_glob() -> None:
    visibility = stage_knowledge_visibility.build_stage_knowledge_visibility(
        study_id="S1",
        stage_refs={"review": [_ref("opl-stage-folder://S1/review/current.json")]},
        closeout_refs=[_ref("opl-state-index://S1/review/owner-receipt")],
    )

    assert visibility["status"] == "available"
    assert visibility["closeout_refs"][0]["payload_sha256"] == "sha256-value"
    assert visibility["authority_boundary"]["state_index_owner"] == "one-person-lab"
