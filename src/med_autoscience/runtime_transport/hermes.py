from __future__ import annotations

from med_autoscience.runtime_transport import med_deepscientist as stable_transport


# Hermes 接入当前仍属于 consumer-only controlled-onramp：
# 复用已经冻结的稳定 transport contract，但不改变默认 backend、
# 不重写 workspace physical layout，也不宣称 external runtime gate 已清除。
BACKEND_ID = "hermes"
ENGINE_ID = "hermes"
CONTROLLED_RESEARCH_BACKEND_ID = stable_transport.BACKEND_ID
CONTROLLED_RESEARCH_ENGINE_ID = stable_transport.ENGINE_ID
DEFAULT_DAEMON_TIMEOUT_SECONDS = stable_transport.DEFAULT_DAEMON_TIMEOUT_SECONDS

resolve_daemon_url = stable_transport.resolve_daemon_url
create_quest = stable_transport.create_quest
resume_quest = stable_transport.resume_quest
pause_quest = stable_transport.pause_quest
stop_quest = stable_transport.stop_quest
get_quest_session = stable_transport.get_quest_session
inspect_quest_live_runtime = stable_transport.inspect_quest_live_runtime
inspect_quest_live_execution = stable_transport.inspect_quest_live_execution
inspect_quest_live_bash_sessions = stable_transport.inspect_quest_live_bash_sessions
update_quest_startup_context = stable_transport.update_quest_startup_context
artifact_complete_quest = stable_transport.artifact_complete_quest
artifact_interact = stable_transport.artifact_interact
