from tinyapi import route


@route("GET", "/health")
def health(_: dict[str, object]) -> tuple[int, dict[str, object]]:
    return 200, {"status": "ok"}
