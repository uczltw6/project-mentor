"""Command-line interface for the Project Mentor deterministic helper."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .errors import InvalidInputError, MentorError
from .events import apply_event
from .io import atomic_write_json, read_json, read_text, sha256_file, write_text
from .model import MODES, SCHEMA_VERSION, VCS_TYPES, canonical_json, new_ledger
from .redact import redact_data, redact_text
from .render import build_receipt_contract, render_receipt, summarize
from .validate import (
    validate_demonstration,
    validate_event,
    validate_evidence,
    validate_ledger,
    validate_receipt,
)

Validator = Callable[[Any], None]


def _add_input_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", default="-", help="UTF-8 input file or '-' for stdin")
    parser.add_argument("--output", default="-", help="UTF-8 output file or '-' for stdout")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug", action="store_true", help="Show unexpected Python tracebacks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("init", help="Create a new empty ledger")
    initialize.add_argument("--goal", required=True)
    initialize.add_argument("--mode", choices=sorted(MODES), default="guided")
    initialize.add_argument("--session-id")
    initialize.add_argument("--created-at", help="Inject a UTC timestamp for reproducible output")
    initialize.add_argument("--root-label", default="project")
    initialize.add_argument("--vcs", choices=sorted(VCS_TYPES), default="unknown")
    initialize.add_argument("--baseline")
    initialize.add_argument("--output", default="-")

    apply_parser = subparsers.add_parser("apply-event", help="Apply one event atomically")
    apply_parser.add_argument("--ledger", required=True, type=Path)
    apply_parser.add_argument("--event", default="-", help="Event JSON file or '-' for stdin")
    apply_parser.add_argument("--expected-revision", required=True, type=int)

    validate_parser = subparsers.add_parser("validate", help="Validate a versioned JSON contract")
    validate_parser.add_argument("--input", default="-", help="JSON file or '-' for stdin")
    validate_parser.add_argument(
        "--kind",
        choices=("ledger", "event", "evidence", "demonstration", "receipt"),
        default="ledger",
    )

    render_parser = subparsers.add_parser("render", help="Render a deterministic learning receipt")
    render_parser.add_argument("--ledger", required=True, help="Ledger JSON file or '-' for stdin")
    render_parser.add_argument("--output", default="-")
    render_parser.add_argument("--language", choices=("en", "zh"), default="en")
    render_parser.add_argument(
        "--rendered-at", help="Inject a UTC timestamp for reproducible output"
    )
    render_parser.add_argument("--output-locator")
    render_parser.add_argument("--max-concepts", type=int, default=5)

    summarize_parser = subparsers.add_parser("summarize", help="Emit a compact JSON summary")
    summarize_parser.add_argument(
        "--ledger", required=True, help="Ledger JSON file or '-' for stdin"
    )
    summarize_parser.add_argument("--output", default="-")

    redact_parser = subparsers.add_parser("redact", help="Redact likely secrets from UTF-8 text")
    _add_input_output(redact_parser)
    return parser


def _command_init(args: argparse.Namespace) -> int:
    ledger = new_ledger(
        goal=args.goal,
        mode=args.mode,
        session_id=args.session_id,
        created_at=args.created_at,
        root_label=args.root_label,
        vcs=args.vcs,
        baseline=args.baseline,
    )
    if args.output == "-":
        write_text("-", canonical_json(ledger))
    else:
        atomic_write_json(args.output, ledger)
        print(f"Initialized ledger revision 0 at {args.output}")
    return 0


def _command_apply(args: argparse.Namespace) -> int:
    if str(args.ledger) == "-":
        raise InvalidInputError("apply-event requires an explicit persistent --ledger path")
    digest = sha256_file(args.ledger)
    ledger = read_json(args.ledger)
    event = redact_data(read_json(args.event))
    updated, changed = apply_event(ledger, event, expected_revision=args.expected_revision)
    if changed:
        atomic_write_json(args.ledger, updated, expected_sha256=digest)
    result = {
        "event_id": event.get("id") if isinstance(event, dict) else None,
        "replayed": not changed,
        "revision": updated["revision"],
    }
    write_text("-", canonical_json(result))
    return 0


def _command_validate(args: argparse.Namespace) -> int:
    validators: dict[str, Validator] = {
        "ledger": validate_ledger,
        "event": validate_event,
        "evidence": validate_evidence,
        "demonstration": validate_demonstration,
        "receipt": validate_receipt,
    }
    value = read_json(args.input)
    validators[args.kind](value)
    print(f"valid {args.kind} schema_version={SCHEMA_VERSION}")
    return 0


def _command_render(args: argparse.Namespace) -> int:
    ledger = read_json(args.ledger)
    generated_at = args.rendered_at or ledger.get("session", {}).get("updated_at")
    if not isinstance(generated_at, str):
        raise InvalidInputError("--rendered-at is required when the ledger has no updated_at")
    locator = args.output_locator or ("chat" if args.output == "-" else Path(args.output).name)
    try:
        receipt = build_receipt_contract(
            ledger,
            language=args.language,
            generated_at=generated_at,
            output_locator=locator,
            max_concepts=args.max_concepts,
        )
    except ValueError as error:
        raise InvalidInputError(str(error)) from error
    write_text(args.output, redact_text(render_receipt(ledger, receipt)))
    return 0


def _command_summarize(args: argparse.Namespace) -> int:
    ledger = read_json(args.ledger)
    write_text(args.output, canonical_json(redact_data(summarize(ledger))))
    return 0


def _command_redact(args: argparse.Namespace) -> int:
    write_text(args.output, redact_text(read_text(args.input)))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    commands: dict[str, Callable[[argparse.Namespace], int]] = {
        "init": _command_init,
        "apply-event": _command_apply,
        "validate": _command_validate,
        "render": _command_render,
        "summarize": _command_summarize,
        "redact": _command_redact,
    }
    try:
        return commands[args.command](args)
    except MentorError as error:
        print(f"error: {redact_text(str(error))}", file=sys.stderr)
        return error.exit_code
    except Exception:
        if args.debug:
            raise
        print("error: unexpected failure; rerun with --debug for a traceback", file=sys.stderr)
        return 1
