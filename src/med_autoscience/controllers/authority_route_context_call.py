from __future__ import annotations

import inspect
from collections.abc import Mapping
from typing import Any


def call_with_authority_route_context(
    function,
    /,
    *,
    authority_route_context: Mapping[str, Any] | None,
    **kwargs: Any,
):
    signature = inspect.signature(function)
    accepts_route_context = "authority_route_context" in signature.parameters or any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )
    if authority_route_context is not None and accepts_route_context:
        kwargs["authority_route_context"] = authority_route_context
    return function(**kwargs)


__all__ = ["call_with_authority_route_context"]
