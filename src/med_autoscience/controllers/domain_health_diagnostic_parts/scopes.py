from __future__ import annotations

from dataclasses import dataclass


FULL = "full"
CURRENTNESS_ONLY = "currentness-only"
OWNER_ROUTE = "owner-route"
PROVIDER_ADMISSION = "provider-admission"

VALID_SCOPES = frozenset({
    FULL,
    CURRENTNESS_ONLY,
    OWNER_ROUTE,
    PROVIDER_ADMISSION,
})


@dataclass(frozen=True)
class DomainHealthDiagnosticScope:
    scope: str

    @property
    def reads_active_quest_reports(self) -> bool:
        return self.scope == FULL

    @property
    def reads_currentness(self) -> bool:
        return self.scope in {FULL, CURRENTNESS_ONLY, OWNER_ROUTE, PROVIDER_ADMISSION}

    @property
    def reads_owner_route(self) -> bool:
        return self.scope in {FULL, OWNER_ROUTE}

    @property
    def reads_provider_admission(self) -> bool:
        return self.scope in {FULL, PROVIDER_ADMISSION}

    @property
    def runs_outer_loop_wakeup(self) -> bool:
        return self.scope == FULL

    @property
    def runs_autonomy_slo(self) -> bool:
        return self.scope == FULL

    @property
    def runs_autonomy_repair(self) -> bool:
        return self.scope == FULL

    @property
    def materializes_opl_handoff(self) -> bool:
        return self.scope in {FULL, PROVIDER_ADMISSION}

    @property
    def runs_same_tick_owner_route(self) -> bool:
        return self.scope in {FULL, OWNER_ROUTE}

    @property
    def materializes_provider_admission_current_control(self) -> bool:
        return self.scope in {FULL, PROVIDER_ADMISSION}

    @property
    def allows_apply(self) -> bool:
        return self.scope != CURRENTNESS_ONLY

    def skipped_surfaces(self) -> list[str]:
        skipped: list[str] = []
        if not self.reads_active_quest_reports:
            skipped.append("active_quest_reports")
        if not self.runs_outer_loop_wakeup:
            skipped.append("outer_loop_wakeup")
        if not self.reads_owner_route:
            skipped.append("owner_route_reconcile")
        if not self.materializes_provider_admission_current_control:
            skipped.append("provider_admission_current_control")
        if not self.allows_apply:
            skipped.append("apply_actuator")
        if not self.runs_autonomy_slo:
            skipped.append("autonomy_slo")
        if not self.runs_autonomy_repair:
            skipped.append("autonomy_repair")
        return skipped

    def to_report(self) -> dict[str, object]:
        return {
            "scope": self.scope,
            "executed_surfaces": [
                surface
                for surface, enabled in (
                    ("managed_study_currentness", self.reads_currentness),
                    ("active_quest_reports", self.reads_active_quest_reports),
                    ("outer_loop_wakeup", self.runs_outer_loop_wakeup),
                    ("owner_route_reconcile", self.reads_owner_route),
                    (
                        "provider_admission_current_control",
                        self.materializes_provider_admission_current_control,
                    ),
                    ("autonomy_slo", self.runs_autonomy_slo),
                    ("autonomy_repair", self.runs_autonomy_repair),
                )
                if enabled
            ],
            "skipped_surfaces": self.skipped_surfaces(),
        }


def parse_diagnostic_scope(value: object | None) -> DomainHealthDiagnosticScope:
    scope = str(value or FULL).strip() or FULL
    if scope not in VALID_SCOPES:
        raise ValueError(f"Unsupported domain-health-diagnostic scope: {scope}")
    return DomainHealthDiagnosticScope(scope=scope)


__all__ = [
    "CURRENTNESS_ONLY",
    "FULL",
    "OWNER_ROUTE",
    "PROVIDER_ADMISSION",
    "VALID_SCOPES",
    "DomainHealthDiagnosticScope",
    "parse_diagnostic_scope",
]
