#!/usr/local/bin/python3
# coding=utf-8

"""
Custom version bumper partially implements PEP 440.
"""

import argparse
import re
import subprocess

from packaging import version
from typing import Optional, List

PACKAGE = "ehforwarderbot"

parser = argparse.ArgumentParser(description="Custom version bumper partially implements PEP 440.")
parser.add_argument("level", action="store",
                    choices=("major", "minor", "patch", "alpha", "beta", "post", "dev"))
parser.add_argument("--dry-run", "-d", help="Dry run.", action="store_true")
parser.add_argument("--allow-dirty", "-a", help="Allow dirty git working directory.", action="store_true")
parser.add_argument("--no-commit", "-n", help="Do not make a new commit.", action="store_true")
parser.add_argument("--tag", "-t", help="Make a tag on the new commit.", action="store_true")


def bump_version(v: version.Version, level: str) -> str:
    """Version bump logic"""
    release: List[int] = list(v.release)
    stage: Optional[str]
    pre: Optional[int]
    stage, pre = v.pre if v.pre else (None, None)
    dev: Optional[int] = v.dev
    post: Optional[int] = v.post

    if level in ("major", "minor", "patch"):
        segments = 0
        if level == "major":
            # if the version code is in format of x.0.0, and pre/dev is not empty
            # do not increase the version number
            segments = 1
        elif level == "minor":
            # if the version code is in format of x.x.0, and pre/dev is not empty
            # do not increase the version number
            segments = 2
        elif level == "patch":
            # if the version code is in format of x.x.x, and pre/dev is not empty
            # do not increase the version number
            segments = 3
        if not any(release[segments:]) and (stage is not None or dev is not None):
            pass
        else:
            release[segments - 1] += 1
        release[segments:] = [0] * max(len(release) - segments, 0)
        stage = pre = post = dev = None
    elif level == "alpha":
        if stage is None:
            if dev is None:
                release[-1] += 1
            stage, pre = "a", 1
        elif stage > "a":
            release[-1] += 1
            stage, pre = "a", 1
        elif stage == "a":
            pre += 1
        post = dev = None
    elif level == "beta":
        if stage is None:
            if dev is None:
                release[-1] += 1
            stage, pre = "b", 1
        elif stage > "b":
            release[-1] += 1
            stage, pre = "b", 1
        elif stage == "b":
            pre += 1
        elif stage < "b":
            pre = 1
            stage = "b"
        post = dev = None
    elif level == "post":
        if post is not None:
            post += 1
        else:
            post = 1
        dev = None
    elif level == "dev":
        if dev is not None:
            dev += 1
        else:
            if stage:
                pre += 1
            else:
                release[-1] += 1
            dev = 1

    ver = ".".join(str(i) for i in release)
    if stage is not None:
        ver += f"{stage}{pre}"
    if post is not None:
        ver += f".post{post}"
    if dev is not None:
        ver += f".dev{dev}"

    return ver


def main():
    args = parser.parse_args()
    version_file_path = f"{PACKAGE}/__version__.py"
    with open(version_file_path) as f:
        content = f.read()
        span = next(re.finditer(r'(?<=__version__ = ")[^"]+(?=")', content)).span()
        source = (content[:span[0]], content[span[0]:span[1]], content[span[1]:])
    v = version.parse(source[1])

    new_ver = bump_version(v, args.level)

    bump_message = f"Bumping version: {source[1]} -> {new_ver}"

    print(bump_message)

    if not args.allow_dirty:
        lines = [
            line.strip() for line in
            subprocess.check_output(
                ["git", "status", "--porcelain"]).splitlines()
            if not line.strip().startswith(b"??")
        ]

        if lines:
            print("Git working directory is dirty, stopped.")
            exit(1)

    if args.dry_run:
        print("Dry run, not writing to the file")
    else:
        with open(version_file_path, 'w') as f:
            f.write(source[0])
            f.write(new_ver)
            f.write(source[2])

    if not args.dry_run and not args.no_commit:
        subprocess.check_output(["git", "add", "--update", version_file_path])
        subprocess.check_output(["git", "commit", "-m", bump_message])

        if args.tag:
            subprocess.check_output(["git", "tag", new_ver])


if __name__ == "__main__":
    main()
