from __future__ import annotations


def render_automation_ready_block() -> str:
    lines = [
        "## Automation-ready execution contract",
        "",
        "when a study boundary is explicit and startup-ready, prefer autonomous managed execution over repeated human clarification loops.",
        "",
        "Automation-ready signals include:",
        "- startup boundary has passed",
        "- execution engine is `med-deepscientist`",
        "- managed entry is enabled",
        "- `decision_policy` is `autonomous`",
        "- auto-resume is enabled for resumable quest states",
        "",
        "Managed runtime behavior once automation-ready:",
        "- prefer `create_and_start` for a missing quest",
        "- prefer `resume` for paused, idle, or created quest states that are safe to continue",
        "- continue until durable outputs requiring human selection are produced",
        "",
        "Human escalation remains appropriate only for blocked credentials, true user-value decisions, or explicit safety/governance boundaries.",
    ]
    return "\n".join(lines) + "\n"


def render_automation_ready_summary() -> str:
    return (
        "Automation-ready rule: when a study boundary is explicit and startup-ready, prefer autonomous managed runtime "
        "execution over repeated clarification. In that state, the system should choose `create_and_start` or `resume` "
        "as appropriate and continue until durable outputs requiring human selection are produced."
    )
