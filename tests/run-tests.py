#!/bin/env python3

from argparse import ArgumentParser
import importlib.util
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import Iterable

from testlib import Report, Suite


tests_root = (Path.cwd() / Path(__file__)).resolve().parent


def module_name_from_path(module_path: Path) -> str:
    return ".".join(
        re.sub(r"\W+", "_", re.sub(r"^\W+|\W+$", "", part))
        for part in [*module_path.parent.parts, module_path.stem]
    )


def load_module_from_path(module_name: str, module_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, module_path)

    if not spec:
        raise ValueError(f"Could not find a file loader for '{module_path}'.")

    module = importlib.util.module_from_spec(spec)

    # By my read of spec_from_file_location, spec.loader can't be None unless
    # the loader= parameter was provided.
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    return module


def load_suite(suite_path: Path) -> Suite:
    if not suite_path.is_absolute():
        suite_path = suite_path.resolve()

    module_name = module_name_from_path(suite_path.relative_to(tests_root))
    module = load_module_from_path(module_name, suite_path)

    return module.get_suite()


def load_suites(root: Path) -> list[Suite]:
    suites = []

    for entry in root.iterdir():
        # Skip entries whose name starts with a dot or underscore.
        if entry.match("[._]*"):
            continue

        if entry.is_dir():
            suites.extend(load_suites(entry))
        elif entry.suffix == ".py":
            suites.append(load_suite(entry))

    return suites


def run_suites(module_paths: Iterable[str], *, show_successful: bool) -> bool:
    suites: list[Suite] = []
    cwd = Path.cwd()

    for module_path in module_paths:
        resolved_path = (cwd / module_path).resolve()

        if resolved_path.is_dir():
            suites.extend(load_suites(resolved_path))
        else:
            suites.append(load_suite(resolved_path))

    reports = []

    for suite in Suite.merge(suites):
        with Report(suite.name, show_successful=show_successful) as report:
            reports.append(report)
            suite.run(report)
            report.print()

    counts = sum((report.counts for report in reports), start=Report.Counts())
    status = sum((report.status for report in reports), start=Report.Status.SUCCESS)

    print(
        f"Ran {counts.tests} total test(s) from {len(suites)} file(s)."
        f" {counts.successes} passed, {counts.failures} failed,"
        f" and {counts.errors} produced an error."
    )

    return status is Report.Status.SUCCESS


if __name__ == "__main__":
    parser = ArgumentParser(description="Run test suites.")

    parser.add_argument(
        "suites",
        help="The path to a file or directory containing tests to run.",
        nargs="+",
        metavar="suite",
    )

    parser.add_argument(
        "-s",
        "--show-successful",
        help="Show successful tests as well as failing ones.",
        action="store_true",
    )

    if sys.version_info < (3, 10, 0):
        parser.error("Running tests requires Python 3.10 or higher.")

    args = parser.parse_args()

    sys.exit(0 if run_suites(args.suites, show_successful=args.show_successful) else 1)
