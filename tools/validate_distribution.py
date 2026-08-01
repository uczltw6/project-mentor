#!/usr/bin/env python3
"""Validate Project Mentor wheel and source-distribution release contracts."""

from __future__ import annotations

import argparse
import stat
import sys
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path, PurePosixPath

PACKAGE = "project_mentor_cli"
SOURCE_PACKAGE = ".agents/skills/project-mentor/scripts/mentor_core"
MAX_ARCHIVE_BYTES = 5 * 1024 * 1024
REPOSITORY = Path(__file__).resolve().parents[1]
DEV_REQUIREMENTS = {
    'build<2,>=1.2; extra == "dev"',
    'coverage[toml]<8,>=7.6; extra == "dev"',
    'mypy<3,>=1.11; extra == "dev"',
    'pyyaml<7,>=6.0; extra == "dev"',
    'pytest<10,>=8.3; extra == "dev"',
    'ruff<1,>=0.6; extra == "dev"',
    'setuptools<90,>=77; extra == "dev"',
}
MODULES = {
    "__init__.py",
    "__main__.py",
    "anchors.py",
    "cli.py",
    "doctor.py",
    "errors.py",
    "events.py",
    "io.py",
    "model.py",
    "redact.py",
    "render.py",
    "validate.py",
}


class DistributionValidationError(ValueError):
    """Raised when a built artifact violates the distribution contract."""


def _validate_archive_names(names: set[str]) -> None:
    for name in names:
        path = PurePosixPath(name)
        drive_like = bool(path.parts and path.parts[0].endswith(":"))
        if not name or "\\" in name or path.is_absolute() or drive_like or ".." in path.parts:
            raise DistributionValidationError("archive contains an unsafe path")
        if "__pycache__" in path.parts or name.endswith((".pyc", ".pyo")):
            raise DistributionValidationError("archive contains generated runtime residue")


def validate_wheel(path: Path, *, version: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise DistributionValidationError("wheel must be an existing regular file")
    dist_info = f"project_mentor-{version}.dist-info"
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = {item.filename for item in infos}
        if len(names) != len(infos):
            raise DistributionValidationError("wheel contains duplicate archive paths")
        _validate_archive_names(names)
        if sum(item.file_size for item in infos) > MAX_ARCHIVE_BYTES:
            raise DistributionValidationError("wheel exceeds the uncompressed size limit")
        if any(stat.S_ISLNK(item.external_attr >> 16) for item in infos):
            raise DistributionValidationError("wheel must not contain symbolic links")

        expected_modules = {f"{PACKAGE}/{module}" for module in MODULES}
        expected_metadata = {
            f"{dist_info}/METADATA",
            f"{dist_info}/WHEEL",
            f"{dist_info}/entry_points.txt",
            f"{dist_info}/licenses/LICENSE",
            f"{dist_info}/RECORD",
            f"{dist_info}/top_level.txt",
        }
        missing = sorted((expected_modules | expected_metadata) - names)
        if missing:
            raise DistributionValidationError(f"wheel is missing required content: {missing[0]}")
        unexpected = sorted(names - expected_modules - expected_metadata)
        if unexpected:
            raise DistributionValidationError(f"wheel contains unexpected content: {unexpected[0]}")

        metadata = Parser().parsestr(archive.read(f"{dist_info}/METADATA").decode("utf-8"))
        required_metadata = {
            "Name": "project-mentor",
            "Version": version,
            "Requires-Python": ">=3.10",
            "License-Expression": "MIT",
        }
        if any(metadata[key] != value for key, value in required_metadata.items()):
            raise DistributionValidationError("wheel metadata does not match the public contract")
        requirements = set(metadata.get_all("Requires-Dist", []))
        if requirements != DEV_REQUIREMENTS:
            raise DistributionValidationError(
                "wheel dependencies do not match the dev-only contract"
            )
        if metadata.get_all("Provides-Extra", []) != ["dev"]:
            raise DistributionValidationError("wheel development extra does not match the contract")

        entry_points = (
            archive.read(f"{dist_info}/entry_points.txt").decode("utf-8").replace("\r\n", "\n")
        )
        if entry_points.strip() != (
            "[console_scripts]\nproject-mentor = project_mentor_cli.cli:main"
        ):
            raise DistributionValidationError(
                "wheel console entry point does not match the contract"
            )


def validate_sdist(path: Path, *, version: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise DistributionValidationError("source distribution must be an existing regular file")
    root = f"project_mentor-{version}"
    with tarfile.open(path, mode="r:gz") as archive:
        members = archive.getmembers()
        names = {member.name for member in members}
        if len(names) != len(members):
            raise DistributionValidationError("source distribution contains duplicate paths")
        _validate_archive_names(names)
        if sum(member.size for member in members if member.isfile()) > MAX_ARCHIVE_BYTES:
            raise DistributionValidationError("source distribution exceeds the size limit")
        if any(not (member.isfile() or member.isdir()) for member in members):
            raise DistributionValidationError("source distribution contains a special file")

        expected_files = {
            f"{root}/LICENSE",
            f"{root}/PKG-INFO",
            f"{root}/README.md",
            f"{root}/pyproject.toml",
            f"{root}/setup.cfg",
            f"{root}/project_mentor.egg-info/PKG-INFO",
            f"{root}/project_mentor.egg-info/SOURCES.txt",
            f"{root}/project_mentor.egg-info/dependency_links.txt",
            f"{root}/project_mentor.egg-info/entry_points.txt",
            f"{root}/project_mentor.egg-info/requires.txt",
            f"{root}/project_mentor.egg-info/top_level.txt",
        }
        expected_files.update(f"{root}/{SOURCE_PACKAGE}/{module}" for module in MODULES)
        actual_files = {member.name for member in members if member.isfile()}
        missing = sorted(expected_files - actual_files)
        if missing:
            raise DistributionValidationError(
                f"source distribution is missing required content: {missing[0]}"
            )
        unexpected = sorted(actual_files - expected_files)
        if unexpected:
            raise DistributionValidationError(
                f"source distribution contains unexpected content: {unexpected[0]}"
            )

        for relative in ("LICENSE", "README.md", "pyproject.toml"):
            extracted = archive.extractfile(f"{root}/{relative}")
            if extracted is None or extracted.read() != (REPOSITORY / relative).read_bytes():
                raise DistributionValidationError(
                    f"source distribution does not match repository content: {relative}"
                )
        for module in MODULES:
            extracted = archive.extractfile(f"{root}/{SOURCE_PACKAGE}/{module}")
            repository_module = REPOSITORY / SOURCE_PACKAGE / module
            if extracted is None or extracted.read() != repository_module.read_bytes():
                raise DistributionValidationError(
                    f"source distribution runtime differs from the repository: {module}"
                )

        package_metadata_file = archive.extractfile(f"{root}/PKG-INFO")
        if package_metadata_file is None:
            raise DistributionValidationError("source distribution metadata is unreadable")
        package_metadata = Parser().parsestr(package_metadata_file.read().decode("utf-8"))
        required_metadata = {
            "Name": "project-mentor",
            "Version": version,
            "Requires-Python": ">=3.10",
            "License-Expression": "MIT",
        }
        if any(package_metadata[key] != value for key, value in required_metadata.items()):
            raise DistributionValidationError(
                "source distribution metadata does not match the public contract"
            )
        if set(package_metadata.get_all("Requires-Dist", [])) != DEV_REQUIREMENTS:
            raise DistributionValidationError(
                "source distribution dependencies do not match the dev-only contract"
            )
        if package_metadata.get_all("Provides-Extra", []) != ["dev"]:
            raise DistributionValidationError(
                "source distribution development extra does not match the contract"
            )

        setup_file = archive.extractfile(f"{root}/setup.cfg")
        if setup_file is None or setup_file.read().decode("utf-8").replace("\r\n", "\n") != (
            "[egg_info]\ntag_build = \ntag_date = 0\n\n"
        ):
            raise DistributionValidationError("source distribution setup.cfg is unexpected")


def validate_artifact_pair(wheel: Path, sdist: Path, *, version: str) -> None:
    root = f"project_mentor-{version}"
    with (
        zipfile.ZipFile(wheel) as wheel_archive,
        tarfile.open(sdist, mode="r:gz") as source_archive,
    ):
        for module in MODULES:
            source_file = source_archive.extractfile(f"{root}/{SOURCE_PACKAGE}/{module}")
            if source_file is None or source_file.read() != wheel_archive.read(
                f"{PACKAGE}/{module}"
            ):
                raise DistributionValidationError(
                    f"wheel runtime differs from the source distribution: {module}"
                )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", required=True, type=Path)
    parser.add_argument("--version", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    wheels = sorted(args.dist_dir.glob(f"project_mentor-{args.version}-*.whl"))
    source_distributions = sorted(args.dist_dir.glob(f"project_mentor-{args.version}.tar.gz"))
    if len(wheels) != 1 or len(source_distributions) != 1:
        print("error: expected exactly one matching wheel and source distribution", file=sys.stderr)
        return 2
    try:
        validate_wheel(wheels[0], version=args.version)
        validate_sdist(source_distributions[0], version=args.version)
        validate_artifact_pair(wheels[0], source_distributions[0], version=args.version)
    except (
        DistributionValidationError,
        KeyError,
        OSError,
        UnicodeError,
        tarfile.TarError,
        zipfile.BadZipFile,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"distribution contract valid for project-mentor {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
