from pathlib import Path as _RuntimeEventsPath

_RUNTIME_EVENTS_PARTS = (
    "ownership_and_continuation.py",
    "human_gates.py",
    "runtime_summary.py",
    "pending_interactions.py",
)
for _runtime_events_part in _RUNTIME_EVENTS_PARTS:
    _runtime_events_chunk_path = (
        _RuntimeEventsPath(__file__).with_name("study_runtime_decision_parts")
        / "runtime_events_parts"
        / _runtime_events_part
    )
    exec(
        compile(
            _runtime_events_chunk_path.read_text(encoding="utf-8"),
            str(_runtime_events_chunk_path),
            "exec",
        ),
        globals(),
    )

del _RuntimeEventsPath, _RUNTIME_EVENTS_PARTS, _runtime_events_part, _runtime_events_chunk_path
