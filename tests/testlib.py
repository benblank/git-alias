from contextlib import AbstractContextManager
from dataclasses import dataclass, field
import enum
import itertools
import os
import os.path
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback
from types import TracebackType
from typing import (
    Any,
    Callable,
    ClassVar,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
    Type,
)
import weakref


_TESTS_DIR = (Path.cwd() / Path(__file__)).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
_TEMP_ROOT = _TESTS_DIR / "tmp"

COMMON_PARAMETERS: Mapping[str, Iterable[Any]] = {
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


def add_aliases(context: "GitExecutionContext", aliases: Mapping[str, str]) -> None:
    for name, contents in aliases.items():
        _execute_command_in_context(
            context,
            ["git", "config", *context.location_flags, "alias." + name, contents],
            check=True,
        )


def clear_aliases(context: "GitExecutionContext") -> None:
    # We could run `git config --name-only` rather than picking the keys off
    # `get_aliases()`, but this is simpler.
    for name in get_aliases(context).keys():
        _execute_command_in_context(
            context,
            ["git", "config", *context.location_flags, "--unset-all", "alias." + name],
            check=True,
        )


def execute_git(
    context: "GitExecutionContext",
    extra_arguments: Sequence[str],
    *,
    combine_output: bool = False,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return _execute_command_in_context(
        context,
        [*context.base_command, *context.location_flags, *extra_arguments],
        combine_output=combine_output,
        check=check,
    )


def _execute_command_in_context(
    context: "GitExecutionContext",
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


def format_parameters(parameters: Mapping[str, Any]):
    return ", ".join(f"{name}={value}" for name, value in parameters.items())


def get_aliases(context: "GitExecutionContext") -> Mapping[str, str]:
    aliases = {}

    try:
        result = _execute_command_in_context(
            context,
            [
                "git",
                "config",
                *context.location_flags,
                "--null",
                "--get-regex",
                "^alias\\.",
            ],
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

    return (
        dict(pairs)
        for pairs in itertools.product(
            *(
                [(name, value) for value in values]
                for name, values in parameters.items()
            )
        )
    )


@dataclass(kw_only=True)
class CommandOutput:
    """Represents the output command execution produces on stdout and strerr."""

    stderr: str
    stdout: str


class GitExecutionContext:
    def __init__(
        self, base_command: Sequence[str], location_flags: Sequence[str]
    ) -> None:
        self.base_command = base_command
        self.location_flags = location_flags

        # Ensure _TEMP_ROOT exists, so that temporary directories can be created
        # in it.
        os.makedirs(_TEMP_ROOT, exist_ok=True)

        # TemporaryDirectory is nice, but we don't need a context manager and it
        # issues a warning when cleaning up due to garbage collection.
        self.base_dir = Path(tempfile.mkdtemp(dir=_TEMP_ROOT))
        self._finalizer = weakref.finalize(
            self, GitExecutionContext.cleanup, self.base_dir
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

        _execute_command_in_context(self, ["git", "init", str(self.repo_dir)])

    @classmethod
    def cleanup(cls, temp_dir: Path) -> None:
        shutil.rmtree(temp_dir, onerror=GitExecutionContext._on_cleanup_error)

    @classmethod
    def _on_cleanup_error(cls, function, path: str, exception_info) -> None:
        # Not much can be done (without an unreasonable amount of effort) other
        # than to report it and continue.
        print(
            f"Failed to fully clean up temporary directory '{path}'.", file=sys.stderr
        )


@dataclass
class TestCase:
    name: str

    context: "GitExecutionContext"

    extra_arguments: Sequence[str]
    """Extra arguments to add to the command line when executing it."""

    exit_code: int | None = field(default=None, kw_only=True)
    """If set, the exit code expected from executing Git.

    If unset, the exit code will be ignored.
    """

    output: str | CommandOutput | None = field(default=None, kw_only=True)
    """If set, the expected output from executing Git.

    Use a string to velidate the combined output (stdout and stderr). Use a
    `CommandOutput` to validate them individually.

    If unset, the output will be ignored.
    """

    def run(self, report: "TestReport"):
        """Executes the test case."""

        result = execute_git(
            self.context,
            self.extra_arguments,
            combine_output=not isinstance(self.output, CommandOutput),
        )

        if self.exit_code is not None and result.returncode != self.exit_code:
            report.failures.append(
                f"expected exit code {self.exit_code}, but got {result.returncode}"
            )

        if self.output is not None:
            if isinstance(self.output, CommandOutput):
                if result.stdout != self.output.stdout:
                    report.failures.append(
                        f"expected {repr(self.output.stdout)} on stdout, but got {repr(result.stdout)}"
                    )

                if result.stderr != self.output.stderr:
                    report.failures.append(
                        f"expected {repr(self.output.stderr)} on stderr, but got {repr(result.stderr)}"
                    )
            else:
                if result.stdout != self.output:
                    report.failures.append(
                        f"expected {repr(self.output)} as output, but got {repr(result.stdout)}"
                    )


# We probably shouldn't be using `frozen=True` here, as the `init=False` fields
# are themselves mutable, but it at least prevents any of the fields from being
# reassigned.
@dataclass(frozen=True)
class TestReport(AbstractContextManager):
    @dataclass(kw_only=True)
    class Counts:
        tests: int = 0
        successes: int = 0
        failures: int = 0
        errors: int = 0

        def __add__(self, other: "TestReport.Counts") -> "TestReport.Counts":
            return TestReport.Counts(
                tests=self.tests + other.tests,
                successes=self.successes + other.successes,
                failures=self.failures + other.failures,
                errors=self.errors + other.errors,
            )

    class Status(enum.Enum):
        SUCCESS = enum.auto()
        FAILURE = enum.auto()
        ERROR = enum.auto()

        def __add__(self, other: "TestReport.Status") -> "TestReport.Status":
            if self == TestReport.Status.ERROR or other == TestReport.Status.ERROR:
                return TestReport.Status.ERROR

            if self == TestReport.Status.FAILURE or other == TestReport.Status.FAILURE:
                return TestReport.Status.FAILURE

            return TestReport.Status.SUCCESS

    __icons: ClassVar[dict[Status, str]] = {
        Status.SUCCESS: "✔ ",
        Status.FAILURE: "❌ ",
        Status.ERROR: "⚠️ ",
    }
    __indent: ClassVar[str] = "  "

    title: str
    parent: "TestReport | None" = None
    show_successful: bool = field(default=True, kw_only=True)

    __children: list["TestReport"] = field(default_factory=list, init=False)
    errors: list[str | list[str]] = field(default_factory=list, init=False)
    failures: list[str | list[str]] = field(default_factory=list, init=False)

    def add_exception(
        self,
        description: str,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.errors.append(
            [
                description,
                # Each elememt in the list returned by `format_exception()`
                # is actually one *or more* lines terminated by newline
                # characters. We're going to add indentation and use
                # `print()` later, so we need to convert it to one line per
                # element, without newlines.
                *(
                    line
                    for formatted in traceback.format_exception(
                        exc_type, exc_val, exc_tb
                    )
                    for line in formatted.rstrip().split("\n")
                ),
            ]
        )

    # TODO? make sure this is only called after the report is "finished" and cache it
    @property
    def counts(self) -> Counts:
        """Get the number of tests, successes, failures, and errors stored in
        this result.

        Only leaf nodes (those without children) are considered tests and can
        therefore be successful. Non-tests are only *counted* as failed or
        errored if they have failures or errors of their own (the failures and
        errors of their children are counted only by those children).

        It is therefore not guaranteed to be the case that `tests = successes +
        failures + errors`, though that will be the case if only tests produce
        failures or errors, which is typical.
        """

        is_test = not self.__children
        is_error = bool(self.errors)
        is_failure = not is_error and bool(self.failures)
        is_success = is_test and not is_failure and not is_error

        own_counts = TestReport.Counts(
            tests=int(is_test),
            successes=int(is_success),
            failures=int(is_failure),
            errors=int(is_error),
        )

        if self.__children:
            return own_counts + sum(
                (child.counts for child in self.__children),
                start=TestReport.Counts(),
            )

        return own_counts

    def create_child_report(self, for_: "TestCase | TestSuite") -> "TestReport":
        child = TestReport(for_.name, self, show_successful=self.show_successful)

        self.__children.append(child)

        return child

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_val is not None:
            self.add_exception("Unhandled exception.", exc_type, exc_val, exc_tb)

        # Don't swallow e.g. KeyboardInterrupt.
        return exc_type is None or issubclass(exc_type, Exception)

    # TODO? make sure this is only called after the report is "finished"
    def print(self):
        if self.show_successful or self.status is not TestReport.Status.SUCCESS:
            self.__println(
                TestReport.__icons[self.status]
                + ("Untitled block" if self.title is None else self.title)
            )

        for failure in self.failures:
            if isinstance(failure, str):
                self.__println(
                    TestReport.__indent
                    + self.__icons[TestReport.Status.FAILURE]
                    + failure
                )
            else:
                self.__println(
                    TestReport.__indent
                    + self.__icons[TestReport.Status.FAILURE]
                    + failure[0]
                )

                for line in failure[1:]:
                    self.__println(TestReport.__indent * 2 + line)

        for error in self.errors:
            if isinstance(error, str):
                self.__println(
                    TestReport.__indent + self.__icons[TestReport.Status.ERROR] + error
                )
            else:
                self.__println(
                    TestReport.__indent
                    + self.__icons[TestReport.Status.ERROR]
                    + error[0]
                )

                for line in error[1:]:
                    self.__println(TestReport.__indent * 2 + line)

        for child in self.__children:
            child.print()

    def __println(self, line: str) -> None:
        if self.parent is None:
            print(line)
        else:
            self.parent.__println(TestReport.__indent + line)

    # TODO? make sure this is only called after the report is "finished" and cache it
    @property
    def status(self) -> Status:
        own_status = (
            TestReport.Status.ERROR
            if self.errors
            else TestReport.Status.FAILURE
            if self.failures
            else TestReport.Status.SUCCESS
        )

        if self.__children:
            return own_status + sum(
                (child.status for child in self.__children),
                start=TestReport.Status.SUCCESS,
            )

        return own_status


@dataclass
class TestSuite:
    name: str
    tests: Iterable["TestCase | TestSuite"]
    before_all: Callable[[], None] = field(default=lambda: None, kw_only=True)
    before_each: Callable[[], None] = field(default=lambda: None, kw_only=True)
    after_each: Callable[[], None] = field(default=lambda: None, kw_only=True)
    after_all: Callable[[], None] = field(default=lambda: None, kw_only=True)

    def run(self, report: TestReport) -> None:
        try:
            self.before_all()
        except Exception:
            report.add_exception("Exception occurred in before_all.", *sys.exc_info())

        for test in self.tests:
            try:
                self.before_each()
            except Exception:
                report.add_exception(
                    "Exception occurred in before_each.", *sys.exc_info()
                )

            with report.create_child_report(test) as child_report:
                test.run(child_report)

            try:
                self.after_each()
            except Exception:
                report.add_exception(
                    "Exception occurred in after_each.", *sys.exc_info()
                )

        try:
            self.after_all()
        except Exception:
            report.add_exception("Exception occurred in after_all.", *sys.exc_info())
