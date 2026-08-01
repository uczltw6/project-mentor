from __future__ import annotations

from pathlib import Path

from mentor_core import cli

REPOSITORY = Path(__file__).resolve().parents[2]
EXAMPLES = REPOSITORY / "examples"


def test_committed_example_ledger_and_receipt_are_reproducible(tmp_path: Path) -> None:
    ledger = tmp_path / "project-mentor-ledger.json"
    receipt = tmp_path / "learning-receipt.md"
    assert (
        cli.main(
            [
                "init",
                "--goal",
                "Add and verify a health endpoint",
                "--mode",
                "guided",
                "--session-id",
                "pm-example-health",
                "--created-at",
                "2026-08-01T09:00:00Z",
                "--root-label",
                "sample-api",
                "--vcs",
                "git",
                "--baseline",
                "main",
                "--output",
                str(ledger),
            ]
        )
        == 0
    )

    for revision, event in enumerate(sorted((EXAMPLES / "events").glob("*.json"))):
        assert (
            cli.main(
                [
                    "apply-event",
                    "--ledger",
                    str(ledger),
                    "--event",
                    str(event),
                    "--expected-revision",
                    str(revision),
                ]
            )
            == 0
        )

    assert (
        cli.main(
            [
                "render",
                "--ledger",
                str(ledger),
                "--language",
                "en",
                "--rendered-at",
                "2026-08-01T09:05:00Z",
                "--output-locator",
                "examples/learning-receipt.md",
                "--output",
                str(receipt),
            ]
        )
        == 0
    )
    assert ledger.read_bytes() == (EXAMPLES / "project-mentor-ledger.json").read_bytes()
    assert receipt.read_bytes() == (EXAMPLES / "learning-receipt.md").read_bytes()
