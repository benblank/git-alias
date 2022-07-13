import importlib.util
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import List

from testlib import TestReport, TestSuite


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


def load_suite(suite_path: Path) -> TestSuite:
    if not suite_path.is_absolute():
        suite_path = suite_path.resolve()

    module_name = module_name_from_path(suite_path.relative_to(tests_root))
    module = load_module_from_path(module_name, suite_path)

    return module.get_test_suite()


def load_suites(root: Path) -> List[TestSuite]:
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


def main(module_paths: List[str]) -> int:
    if not module_paths:
        print(
            "You must specify paths to test suites to run on the command line.",
            file=sys.stderr,
        )

        return 1

    suites: List[TestSuite] = []
    cwd = Path.cwd()

    for module_path in module_paths:
        resolved_path = (cwd / module_path).resolve()

        if resolved_path.is_dir():
            suites.extend(load_suites(resolved_path))
        else:
            suites.append(load_suite(resolved_path))

    report = TestReport()

    for suite in suites:
        report += suite.run()

    print(
        f"Ran {report.tests} total tests. {report.failures} failures, {report.errors} errors."
    )

    return 0 if report.successful else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
