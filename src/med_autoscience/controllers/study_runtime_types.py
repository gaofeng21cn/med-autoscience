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
    "ProgressProjectionStatus",
    "StudyRuntimeWorkspaceContractsSummary",
    "_LIVE_QUEST_STATUSES",
    "_RESUMABLE_QUEST_STATUSES",
]


_STATUS_NAMES = set(__all__)


def __getattr__(name: str):
    if name in _STATUS_NAMES:
        value = getattr(import_module("med_autoscience.controllers.progress_projection"), name)
    else:
        raise AttributeError(name)
    globals()[name] = value
    return value
