#!/usr/bin/env python3
"""Check that this web runs against the robot_driver revision it is pinned to.

compat.yaml pins one robot_driver commit. That commit fixes
  - robot_interfaces (its deps.repos): this repository must pin the same commit;
  - robot_description (its src/description/source-lock.yaml): the model the web shows,
    installed with robot_driver on the target machine.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Callable
from urllib.request import urlopen

import yaml

SHA = re.compile(r"^[0-9a-f]{40}$")
INTERFACES = "robot_interfaces"
Fetch = Callable[[str, str, str], str]


def _pin(revision: object, what: str) -> str:
    if not isinstance(revision, str) or not SHA.match(revision):
        raise ValueError(f"{what} must be a full 40-character commit, got {revision!r}")
    return revision


def _interfaces_pin(deps_text: str, what: str) -> str:
    repositories = yaml.safe_load(deps_text)["repositories"]
    pins = [
        entry["version"]
        for path, entry in repositories.items()
        if Path(path).name == INTERFACES
    ]
    if len(pins) != 1:
        raise ValueError(f"{what} must pin {INTERFACES} exactly once")
    return _pin(pins[0], f"{what} {INTERFACES}")


def github_raw(repository: str, commit: str, path: str) -> str:
    slug = repository.removeprefix("https://github.com/").removesuffix(".git")
    with urlopen(f"https://raw.githubusercontent.com/{slug}/{commit}/{path}", timeout=30) as reply:
        return reply.read().decode("utf-8")


def check(compat_text: str, deps_text: str, fetch: Fetch) -> tuple[list[str], str]:
    driver = yaml.safe_load(compat_text)["robot_driver"]
    revision = _pin(driver["revision"], "compat.yaml robot_driver revision")
    ours = _interfaces_pin(deps_text, "deps.repos")
    theirs = _interfaces_pin(
        fetch(driver["repository"], revision, "deps.repos"), f"robot_driver@{revision[:7]}"
    )
    lock = yaml.safe_load(fetch(driver["repository"], revision, "src/description/source-lock.yaml"))
    model = _pin(lock["source_revision"], "robot_description source_revision")
    findings = []
    if ours != theirs:
        findings.append(
            f"deps.repos pins {INTERFACES} {ours}, robot_driver@{revision[:7]} pins {theirs}"
        )
    return findings, model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        findings, model = check(
            (args.root / "compat.yaml").read_text("utf-8"),
            (args.root / "deps.repos").read_text("utf-8"),
            github_raw,
        )
    except (OSError, KeyError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    for finding in findings:
        print(f"FAIL: {finding}", file=sys.stderr)
    if findings:
        return 1
    print(f"PASS: robot_interfaces matches robot_driver; robot_description model {model}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
