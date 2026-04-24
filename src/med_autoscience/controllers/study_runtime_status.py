from __future__ import annotations

from .study_runtime_status_parts import (
    _UNSET,
    _absent_study_completion_state,
    StudyRuntimeDecision,
    StudyRuntimeReason,
    StudyRuntimeQuestStatus,
    StudyRuntimeBindingAction,
    StudyRuntimeDaemonStep,
    StudyRuntimeAuditStatus,
    _LIVE_QUEST_STATUSES,
    _RESUMABLE_QUEST_STATUSES,
    StudyRuntimeAuditRecord,
    StudyRuntimeAutonomousRuntimeNotice,
    StudyRuntimeSummaryAlignment,
    StudyRuntimeExecutionOwnerGuard,
    StudyRuntimePendingUserInteraction,
    StudyRuntimeInteractionArbitration,
    StudyRuntimeContinuationState,
    annotations,
    Iterator,
    MutableMapping,
    dataclass,
    field,
    StrEnum,
    PathLike,
    Path,
    Any,
    study_runtime_protocol,
    StudyCompletionState,
    StudyCompletionStateStatus,
    StudyRuntimeAnalysisBundleResult,
    StudyRuntimeOverlayAudit,
    StudyRuntimeOverlayResult,
    StudyRuntimeStartupContextSyncResult,
    StudyRuntimePartialQuestRecoveryResult,
    StudyRuntimeWorkspaceContractsSummary,
    StudyRuntimeStartupDataReadinessReport,
    StudyRuntimeStartupBoundaryGate,
    StudyRuntimeReentryGate,
    StudyRuntimePublicationSupervisorState,
    StudyRuntimeProgressProjection,
    StudyCompletionSyncResult,
    StudyRuntimeStatus,
    __all__,
)
from .study_runtime_status_parts import enums_and_audits as enums_and_audits
from .study_runtime_status_parts import runtime_result_types as runtime_result_types
from .study_runtime_status_parts import status_model as status_model

import sys
from types import ModuleType
from typing import Any as _Any

_DECLARED_NAMES = ('__all__', '_UNSET', '_absent_study_completion_state', 'StudyRuntimeDecision', 'StudyRuntimeReason', 'StudyRuntimeQuestStatus', 'StudyRuntimeBindingAction', 'StudyRuntimeDaemonStep', 'StudyRuntimeAuditStatus', '_LIVE_QUEST_STATUSES', '_RESUMABLE_QUEST_STATUSES', 'StudyRuntimeAuditRecord', 'StudyRuntimeAutonomousRuntimeNotice', 'StudyRuntimeSummaryAlignment', 'StudyRuntimeExecutionOwnerGuard', 'StudyRuntimePendingUserInteraction', 'StudyRuntimeInteractionArbitration', 'StudyRuntimeContinuationState', 'StudyRuntimeAnalysisBundleResult', 'StudyRuntimeOverlayAudit', 'StudyRuntimeOverlayResult', 'StudyRuntimeStartupContextSyncResult', 'StudyRuntimePartialQuestRecoveryResult', 'StudyRuntimeWorkspaceContractsSummary', 'StudyRuntimeStartupDataReadinessReport', 'StudyRuntimeStartupBoundaryGate', 'StudyRuntimeReentryGate', 'StudyRuntimePublicationSupervisorState', 'StudyRuntimeProgressProjection', 'StudyCompletionSyncResult', 'StudyRuntimeStatus',)


def _split_chunks() -> tuple[ModuleType, ...]:
    return tuple(
        value
        for name, value in globals().items()
        if isinstance(value, ModuleType) and name in {'enums_and_audits', 'runtime_result_types', 'status_model'} # and isinstance(value, ModuleType)
    )


def _restore_declaring_module() -> None:
    module_name = __name__
    for name in _DECLARED_NAMES:
        value = globals().get(name)
        if isinstance(value, type) or callable(value):
            if getattr(value, "__module__", None) != module_name:
                try:
                    value.__module__ = module_name
                except (AttributeError, TypeError):
                    pass


class _SplitModule(ModuleType):
    def __setattr__(self, name: str, value: _Any) -> None:
        super().__setattr__(name, value)
        for chunk in _split_chunks():
            if hasattr(chunk, name):
                setattr(chunk, name, value)


_restore_declaring_module()
sys.modules[__name__].__class__ = _SplitModule
