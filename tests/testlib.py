from dataclasses import dataclass, field
from itertools import product, starmap
import os
import os.path
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence
import weakref


_INDENT = "  "
_TESTS_DIR = (Path.cwd() / Path(__file__)).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
_TEMP_ROOT = _TESTS_DIR / "tmp"


common_parameters: Mapping[str, Iterable[Any]] = {
    "command-alias": [
        ["git", "alias-abs"],
        ["git", "alias-rel"],
        ["git-alias.sh"],
    ],
    "command-unalias": [
        ["git", "unalias-abs"],
        ["git", "unalias-rel"],
        ["git-unalias.sh"],
    ],
    "location-flags": [
        ["--file", "gitconfig-specific-file"],
        ["--global"],
        ["--local"],
        ["--system"],
    ],
}


def add_aliases(
    context: "TestExecutionContext",
    location_flags: Sequence[str],
    aliases: Mapping[str, str],
) -> None:
    for name, contents in aliases.items():
        run_in_context(
            context,
            ["git", "config", *location_flags, "alias." + name, contents],
            check=True,
        )


def clear_aliases(
    context: "TestExecutionContext", location_flags: Sequence[str] = []
) -> None:
    # We could run `git config --name-only` rather than picking the keys off
    # `get_aliases()`, but this is simpler.
    for name in get_aliases(context, location_flags).keys():
        run_in_context(
            context,
            ["git", "config", *location_flags, "--unset-all", "alias." + name],
            check=True,
        )


def format_parameters(parameters: Mapping[str, Any]):
    return ", ".join(starmap(lambda name, value: f"{name}={value}", parameters.items()))


def get_aliases(
    context: "TestExecutionContext", location_flags: Sequence[str] = []
) -> Mapping[str, str]:
    aliases = {}

    try:
        result = run_in_context(
            context,
            ["git", "config", *location_flags, "--null", "--get-regex", "^alias\\."],
            check=True,
        )

        for alias in filter(None, result.stdout.split("\0")):
            name, command = alias.split("\n", 1)

            # Strip the first six characters (always "alias.") from the names.
            aliases[name[6:]] = command
    except subprocess.CalledProcessError as ex:
        # A return code of 1 just means that no aliases were defined.
        if ex.returncode != 1:
            raise

    return aliases


def get_parameter_matrix(
    parameters: Mapping[str, Iterable[Any]]
) -> Iterator[Mapping[str, Any]]:
    """Produce all possible combinations of parameter values.

    Accepts a mapping of parameter names to their possible values and returns an
    iterator over mappings of each possible combination of values. For example:

    >>> list(get_parameter_matrix({'a': [1, 2, 3], 'b': [4, 5, 6]}))
    [{'a': 1, 'b': 4}, {'a': 1, 'b': 5}, {'a': 1, 'b': 6}, {'a': 2, 'b': 4}, {'a': 2, 'b': 5}, {'a': 2, 'b': 6}, {'a': 3, 'b': 4}, {'a': 3, 'b': 5}, {'a': 3, 'b': 6}]
    """

    return map(
        dict,
        product(
            *starmap(
                lambda name, values: [(name, value) for value in values],
                parameters.items(),
            )
        ),
    )


def run_in_context(
    context: "TestExecutionContext",
    command: Sequence[str],
    *,
    combine_output: bool = False,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=context.base_dir,
        env=context.env,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT if combine_output else subprocess.PIPE,
        check=check,
    )


@dataclass(kw_only=True)
class CommandOutput:
    """Represents the output command execution produces on stdout and strerr."""

    stderr: str
    stdout: str


@dataclass
class TestCase:
    name: str

    context: "TestExecutionContext"

    command_line: Sequence[str]
    """The command and arguments to execute.

    Because the first element specifies the command to run, it is an error to
    provide an empty sequence.
    """

    exit_code: int | None = field(default=None, kw_only=True)
    """If set, the exit code expected from executing `command_line`.

    If unset, the exit code will be ignored.
    """

    output: str | CommandOutput | None = field(default=None, kw_only=True)
    """If set, the expected output from executing `command_line`.

    Use a string to velidate the combined output (stdout and stderr). Use a
    `CommandOutput` to validate them individually.

    If unset, the output will be ignored.
    """

    def run(self, indent_level: int = 0) -> bool:
        """Executes the test case.

        A return value of True indicates success; False indicates failure. An
        exception will be raised when an error occurs.
        """

        failed = False

        result = run_in_context(
            self.context,
            self.command_line,
            combine_output=not isinstance(self.output, CommandOutput),
        )

        if self.exit_code is not None and result.returncode != self.exit_code:
            print(
                f"{_INDENT * (indent_level + 1)}- expected exit code {self.exit_code}, but got {result.returncode}"
            )

            failed = True

        if self.output is not None:
            if isinstance(self.output, CommandOutput):
                if result.stdout != self.output.stdout:
                    print(
                        f"{_INDENT * (indent_level + 1)}- expected {repr(self.output.stdout)} on stdout, but got {repr(result.stdout)}"
                    )

                    failed = True

                if result.stderr != self.output.stderr:
                    print(
                        f"{_INDENT * (indent_level + 1)}- expected {repr(self.output.stderr)} on stderr, but got {repr(result.stderr)}"
                    )

                    failed = True
            else:
                if result.stdout != self.output:
                    print(
                        f"{_INDENT * (indent_level + 1)}- expected {repr(self.output)} as output, but got {repr(result.stdout)}"
                    )

                    failed = True

        print(f"{_INDENT * indent_level}{'❌' if failed else '✔'} {self.name}")

        return not failed


class TestExecutionContext:
    def __init__(self) -> None:
        # Ensure _TEMP_ROOT exists, so that temporary directories can be created
        # in it.
        os.makedirs(_TEMP_ROOT, exist_ok=True)

        # TemporaryDirectory is nice, but we don't need a context manager and it
        # issues a warning when cleaning up due to garbage collection.
        self.base_dir = Path(tempfile.mkdtemp(dir=_TEMP_ROOT))
        self._finalizer = weakref.finalize(
            self, TestExecutionContext.cleanup, self.base_dir
        )

        self.bin_dir = self.base_dir / "bin"
        self.repo_dir = self.base_dir / "repo"

        os.mkdir(self.bin_dir)

        # pathlib can't construct relative paths which ascend the ancestor
        # chain, so fall back to os.path for that.
        #
        # See: https://github.com/python/cpython/issues/84538
        scripts_dir_rel = Path(os.path.relpath(_SCRIPTS_DIR, self.bin_dir))

        os.symlink(_SCRIPTS_DIR / "git-alias.sh", self.bin_dir / "git-alias-abs")
        os.symlink(scripts_dir_rel / "git-alias.sh", self.bin_dir / "git-alias-rel")
        os.symlink(_SCRIPTS_DIR / "git-unalias.sh", self.bin_dir / "git-unalias-abs")
        os.symlink(scripts_dir_rel / "git-unalias.sh", self.bin_dir / "git-unalias-rel")

        self.env = {
            "GIT_CONFIG_GLOBAL": str(self.base_dir / "gitconfig-global"),
            "GIT_CONFIG_SYSTEM": str(self.base_dir / "gitconfig-system"),
            "PATH": os.pathsep.join(
                [str(self.bin_dir), str(_SCRIPTS_DIR), os.environ["PATH"]]
            ),
        }

        run_in_context(self, ["git", "init", str(self.repo_dir)])

    @classmethod
    def cleanup(cls, temp_dir: Path) -> None:
        shutil.rmtree(temp_dir, onerror=TestExecutionContext._on_cleanup_error)

    @classmethod
    def _on_cleanup_error(cls, function, path: str, exception_info) -> None:
        # Not much can be done (without an unreasonable amount of effort) other
        # than to report it and continue.
        print(
            f"Failed to fully clean up temporary directory '{path}'.", file=sys.stderr
        )


@dataclass(kw_only=True)
class TestReport:
    tests: int = 0
    failures: int = 0
    errors: int = 0

    def __add__(self, other: "TestReport | bool") -> "TestReport":
        """Creates a new TestReport with summed values.

        If `other` is a TestReport, each field is summed. If `other` is a
        boolean, `tests` is incremented regardless of the value and `failures`
        is incremented on False.
        """

        if isinstance(other, TestReport):
            return TestReport(
                tests=self.tests + other.tests,
                failures=self.failures + other.failures,
                errors=self.errors + other.errors,
            )

        if isinstance(other, bool):
            return TestReport(
                tests=self.tests + 1,
                failures=self.failures + (not other),
                errors=self.errors,
            )

        raise NotImplementedError()

    def successful(self) -> bool:
        return self.failures == self.errors == 0


@dataclass
class TestSuite:
    name: str
    tests: Iterable["TestCase | TestSuite"]
    before_all: Callable[[], None] | None = field(default=None, kw_only=True)
    before_each: Callable[[], None] | None = field(default=None, kw_only=True)
    after_each: Callable[[], None] | None = field(default=None, kw_only=True)
    after_all: Callable[[], None] | None = field(default=None, kw_only=True)

    def run(self, indent_level: int = 0) -> TestReport:
        print(_INDENT * indent_level + "- " + self.name)

        report = TestReport()

        if self.before_all:
            self.before_all()

        for test in self.tests:
            if self.before_each:
                self.before_each()

            try:
                report += test.run(indent_level + 1)
            except Exception:
                print(
                    "".join(
                        map(
                            lambda line: f"{_INDENT * (indent_level + 2)}{line}",
                            traceback.format_exc(),
                        )
                    ),
                    file=sys.stderr,
                )

                report += TestReport(tests=1, errors=1)

            if self.after_each:
                self.after_each()

        if self.after_all:
            self.after_all()

        return report
