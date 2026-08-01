from __future__ import annotations

from collections.abc import Callable
from typing import Any

Handler = Callable[[dict[str, Any]], tuple[int, dict[str, Any]]]
ROUTES: dict[tuple[str, str], Handler] = {}


def route(method: str, path: str) -> Callable[[Handler], Handler]:
    def register(handler: Handler) -> Handler:
        ROUTES[(method.upper(), path)] = handler
        return handler

    return register


def request(method: str, path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    handler = ROUTES.get((method.upper(), path))
    if handler is None:
        return 404, {"error": "not found"}
    return handler(payload)
