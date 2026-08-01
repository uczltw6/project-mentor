"""Command-line interface for the Project Mentor deterministic helper."""

from __future__ import annotations

import argparse
import copy
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import __version__
from .anchors import anchor_event_id, verify_anchors
from .doctor import diagnose, is_safe_skill_root
from .errors import InvalidInputError, MentorError, RevisionConflictError
from .events import apply_event
from .io import atomic_write_json, read_json, read_text, sha256_file, write_text
from .model import MODES, SCHEMA_VERSION, VCS_TYPES, canonical_json, new_ledger, utc_now
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


def _reject_output_alias(source: str | Path, destination: str | Path) -> None:
    if str(source) == "-" or str(destination) == "-":
        return
    if Path(source).resolve() == Path(destination).resolve():
        raise InvalidInputError("input and output paths must be different")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project-mentor", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
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
    render_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    summarize_parser = subparsers.add_parser("summarize", help="Emit a compact JSON summary")
    summarize_parser.add_argument(
        "--ledger", required=True, help="Ledger JSON file or '-' for stdin"
    )
    summarize_parser.add_argument("--output", default="-")

    redact_parser = subparsers.add_parser("redact", help="Redact likely secrets from UTF-8 text")
    _add_input_output(redact_parser)

    doctor_parser = subparsers.add_parser("doctor", help="Run read-only environment checks")
    doctor_parser.add_argument("--skill-root", type=Path)
    doctor_parser.add_argument("--project-root", type=Path, default=Path("."))
    doctor_parser.add_argument("--ledger", type=Path)
    doctor_parser.add_argument("--output", default="-")

    anchors_parser = subparsers.add_parser(
        "verify-anchors", help="Verify local project-evidence anchors"
    )
    anchors_parser.add_argument("--ledger", required=True, type=Path)
    anchors_parser.add_argument("--root", type=Path, default=Path("."))
    anchors_parser.add_argument("--output", default="-")
    anchors_parser.add_argument("--write", action="store_true")
    anchors_parser.add_argument("--expected-revision", type=int)
    anchors_parser.add_argument("--checked-at")
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
    _reject_output_alias(args.ledger, args.output)
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
    if args.format == "json":
        write_text(args.output, canonical_json(redact_data(receipt)))
    else:
        write_text(args.output, redact_text(render_receipt(ledger, receipt)))
    return 0


def _command_summarize(args: argparse.Namespace) -> int:
    _reject_output_alias(args.ledger, args.output)
    ledger = read_json(args.ledger)
    write_text(args.output, canonical_json(redact_data(summarize(ledger))))
    return 0


def _command_redact(args: argparse.Namespace) -> int:
    _reject_output_alias(args.input, args.output)
    write_text(args.output, redact_text(read_text(args.input)))
    return 0


def _discover_skill_root(project_root: Path) -> Path | None:
    bundled = Path(__file__).resolve().parents[2]
    candidates = (
        (project_root, project_root / ".agents" / "skills" / "project-mentor"),
        (Path.home(), Path.home() / ".agents" / "skills" / "project-mentor"),
        (bundled.parent, bundled),
    )
    return next(
        (
            candidate
            for boundary, candidate in candidates
            if is_safe_skill_root(candidate, boundary=boundary)
            and (candidate / "SKILL.md").is_file()
        ),
        None,
    )


def _command_doctor(args: argparse.Namespace) -> int:
    if args.ledger is not None:
        _reject_output_alias(args.ledger, args.output)
    skill_root = args.skill_root or _discover_skill_root(args.project_root)
    report = diagnose(
        skill_root=skill_root,
        project_root=args.project_root,
        ledger_path=args.ledger,
    )
    write_text(args.output, canonical_json(report))
    return 0 if report["status"] == "ok" else 1


def _command_verify_anchors(args: argparse.Namespace) -> int:
    if str(args.ledger) == "-":
        raise InvalidInputError("verify-anchors requires an explicit --ledger path")
    _reject_output_alias(args.ledger, args.output)
    digest = sha256_file(args.ledger)
    ledger = read_json(args.ledger)
    validate_ledger(ledger)
    report, stale_targets = verify_anchors(ledger, root=args.root)
    report["revision"] = ledger["revision"]
    report["written_events"] = 0
    if not args.write and (args.expected_revision is not None or args.checked_at is not None):
        raise InvalidInputError("--expected-revision and --checked-at require --write")
    if args.write:
        if args.expected_revision is None:
            raise InvalidInputError("--write requires --expected-revision")
        if args.expected_revision != ledger["revision"]:
            raise RevisionConflictError(
                f"expected revision {args.expected_revision}, found {ledger['revision']}"
            )
        checked_at = args.checked_at or utc_now()
        updated = copy.deepcopy(ledger)
        for target in stale_targets:
            event = {
                "schema_version": SCHEMA_VERSION,
                "id": anchor_event_id(target, checked_at),
                "timestamp": checked_at,
                "type": "evidence_marked_stale",
                "actor": "rule",
                "payload": target,
            }
            updated, changed = apply_event(updated, event, expected_revision=updated["revision"])
            report["written_events"] += int(changed)
        if report["written_events"]:
            atomic_write_json(args.ledger, updated, expected_sha256=digest)
        report["revision"] = updated["revision"]
    write_text(args.output, canonical_json(redact_data(report)))
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
        "doctor": _command_doctor,
        "verify-anchors": _command_verify_anchors,
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
