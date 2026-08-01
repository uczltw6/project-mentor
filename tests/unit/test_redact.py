from __future__ import annotations

import pytest
from conftest import assert_no_secret
from mentor_core.redact import PRIVATE_KEY_REDACTED, REDACTED, redact_data, redact_text


@pytest.mark.parametrize(
    "build_text",
    [
        lambda secret: f"Authorization: Bearer {secret}",
        lambda secret: f"TOKEN={secret}",
        lambda secret: f'API_KEY="{secret}"',
        lambda secret: f"PASSWORD='{secret}'",
        lambda secret: f"--api-key {secret}",
        lambda secret: f"--client_secret={secret}",
        lambda secret: f"https://user:{secret}@example.invalid/path",
        lambda secret: f"https://example.invalid/path?token={secret}&page=1",
        lambda secret: "gh" + "p_" + secret,
        lambda secret: "github_pat_" + secret,
        lambda secret: "sk-" + secret,
        lambda secret: "AKIA" + secret[:16].upper(),
        lambda secret: "xoxb-" + secret,
        lambda secret: "glpat-" + secret,
    ],
)
def test_redacts_recognized_secrets(build_text: object) -> None:
    secret = "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6"
    text = build_text(secret)  # type: ignore[operator]
    result = redact_text(text)
    assert_no_secret(result, secret)
    assert REDACTED in result


def test_redacts_private_key_block() -> None:
    body = "sensitive-material"
    text = f"before\n-----BEGIN PRIVATE KEY-----\n{body}\n-----END PRIVATE KEY-----\nafter"
    result = redact_text(text)
    assert_no_secret(result, body)
    assert PRIVATE_KEY_REDACTED in result
    assert result.startswith("before") and result.endswith("after")


@pytest.mark.parametrize(
    "text",
    [
        "token budget is 1000",
        "monkey=banana",
        "secret management is a concept",
        "https://example.invalid/public?page=1",
        "sk-short",
        "API_KEY is an environment-variable name",
    ],
)
def test_preserves_expected_false_positives(text: str) -> None:
    assert redact_text(text) == text


def test_recursive_redaction_is_idempotent() -> None:
    secret = "z" * 40
    source = {
        "authorization": secret,
        "nested": [
            {"api-key": secret},
            "CLIENT_SECRET=" + secret,
            7,
            None,
        ],
        "safe": "保留这个值",
    }
    first = redact_data(source)
    second = redact_data(first)
    assert first == second
    assert_no_secret(repr(first), secret)
    assert first["authorization"] == REDACTED
    assert first["safe"] == "保留这个值"
    assert source["authorization"] == secret


def test_redacts_multiple_secrets_in_one_command() -> None:
    first = "f" * 32
    second = "s" * 32
    result = redact_text(f"TOKEN={first} run --password {second}")
    assert_no_secret(result, first, second)
    assert result.count(REDACTED) == 2
