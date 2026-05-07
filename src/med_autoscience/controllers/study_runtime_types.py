from __future__ import annotations

from importlib import import_module

__all__ = [
    "StudyCompletionSyncResult",
    "StudyRuntimeAutonomousRuntimeNotice",
    "StudyRuntimeAnalysisBundleResult",
    "StudyRuntimeAuditRecord",
    "StudyRuntimeAuditStatus",
    "StudyRuntimeBindingAction",
    "StudyRuntimeContinuationState",
    "StudyRuntimeDaemonStep",
    "StudyRuntimeDecision",
    "StudyRuntimeExecutionOwnerGuard",
    "StudyRuntimeInteractionArbitration",
    "StudyRuntimeExecutionContext",
    "StudyRuntimeExecutionOutcome",
    "StudyRuntimeOverlayAudit",
    "StudyRuntimeOverlayResult",
    "StudyRuntimePendingUserInteraction",
    "StudyRuntimePartialQuestRecoveryResult",
    "StudyRuntimeProgressProjection",
    "StudyRuntimePublicationSupervisorState",
    "StudyRuntimeQuestStatus",
    "StudyRuntimeReason",
    "StudyRuntimeReentryGate",
    "StudyRuntimeSummaryAlignment",
    "StudyRuntimeStartupBoundaryGate",
    "StudyRuntimeStartupContextSyncResult",
    "StudyRuntimeStartupDataReadinessReport",
    "StudyRuntimeStatus",
    "StudyRuntimeWorkspaceContractsSummary",
    "_LIVE_QUEST_STATUSES",
    "_RESUMABLE_QUEST_STATUSES",
]


_EXECUTION_NAMES = {
    "StudyRuntimeExecutionContext",
    "StudyRuntimeExecutionOutcome",
}

_STATUS_NAMES = set(__all__) - _EXECUTION_NAMES


def __getattr__(name: str):
    if name in _EXECUTION_NAMES:
        value = getattr(import_module("med_autoscience.controllers.study_runtime_execution"), name)
    elif name in _STATUS_NAMES:
        value = getattr(import_module("med_autoscience.controllers.study_runtime_status"), name)
    else:
        raise AttributeError(name)
    globals()[name] = value
    return value
