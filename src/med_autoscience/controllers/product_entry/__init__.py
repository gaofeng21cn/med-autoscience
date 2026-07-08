from __future__ import annotations

from importlib import import_module
from typing import Any


def __getattr__(name: str) -> Any:
    if name == "dispatch_guarded_medical_paper_operator_action":
        module = import_module("med_autoscience.controllers.medical_paper_operator_actions")
        return module.dispatch_guarded_medical_paper_operator_action
    raise AttributeError(name)


__all__ = ("dispatch_guarded_medical_paper_operator_action",)
