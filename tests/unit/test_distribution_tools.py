from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from tools.validate_distribution import (
    DEV_REQUIREMENTS,
    MODULES,
    DistributionValidationError,
    _validate_archive_names,
    validate_wheel,
)


def _wheel(path: Path, *, runtime_requirement: str | None = None) -> Path:
    version = "0.3.0"
    dist_info = f"project_mentor-{version}.dist-info"
    metadata = (
        "Metadata-Version: 2.4\n"
        "Name: project-mentor\n"
        f"Version: {version}\n"
        "Requires-Python: >=3.10\n"
        "License-Expression: MIT\n"
        "Provides-Extra: dev\n"
    )
    metadata += "".join(f"Requires-Dist: {requirement}\n" for requirement in DEV_REQUIREMENTS)
    if runtime_requirement is not None:
        metadata += f"Requires-Dist: {runtime_requirement}\n"
    with zipfile.ZipFile(path, mode="w") as archive:
        for module in MODULES:
            archive.writestr(f"project_mentor_cli/{module}", "")
        archive.writestr(f"{dist_info}/METADATA", metadata)
        archive.writestr(f"{dist_info}/WHEEL", "Wheel-Version: 1.0\n")
        archive.writestr(
            f"{dist_info}/entry_points.txt",
            "[console_scripts]\nproject-mentor = project_mentor_cli.cli:main\n",
        )
        archive.writestr(f"{dist_info}/licenses/LICENSE", "MIT\n")
        archive.writestr(f"{dist_info}/RECORD", "")
        archive.writestr(f"{dist_info}/top_level.txt", "project_mentor_cli\n")
    return path


def test_wheel_validator_accepts_only_development_extra_dependencies(tmp_path: Path) -> None:
    valid = _wheel(tmp_path / "valid.whl")
    validate_wheel(valid, version="0.3.0")

    unsafe = _wheel(tmp_path / "unsafe.whl", runtime_requirement="requests>=2")
    with pytest.raises(DistributionValidationError, match="dev-only contract"):
        validate_wheel(unsafe, version="0.3.0")


@pytest.mark.parametrize(
    "name", ("../secret", "/absolute", "safe/../../secret", "bad\\path", "C:/absolute")
)
def test_distribution_validator_rejects_unsafe_archive_paths(name: str) -> None:
    with pytest.raises(DistributionValidationError, match="unsafe path"):
        _validate_archive_names({name})
