from contextlib import AbstractContextManager
from dataclasses import dataclass, field
import enum
import itertools
import os
import os.path
from pathlib import Path
import re
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
    TypeVar,
)
import weakref


K = TypeVar("K")
V = TypeVar("V")

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


def format_parameters(parameters: Mapping[str, Any]):
    return ", ".join(f"{name}={value}" for name, value in parameters.items())


def _format_expected_output(expected: str | re.Pattern) -> str:
    if isinstance(expected, re.Pattern):
        return f"a string matching /{expected.pattern}/"

    return repr(expected)


def get_parameter_matrix(
    parameters: Mapping[K, Iterable[V]]
) -> Iterator[Mapping[K, V]]:
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


def _is_valid_output(expected: str | re.Pattern, actual: str) -> bool:
    if isinstance(expected, re.Pattern):
        return expected.search(actual) is not None

    return expected == actual


def pick(mapping: Mapping[K, V], keys: Iterable[K]) -> dict[K, V]:
    """Filter a mapping such that only the specified keys are retained.

    Note that all specified keys must exist on the mapping.
    """

    return {key: mapping[key] for key in keys}


@dataclass(kw_only=True)
class CommandOutput:
    """Represents the output expected from a command on its stdout and strerr."""

    stderr: str | re.Pattern
    stdout: str | re.Pattern


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

        self._execute_command(["git", "init", str(self.repo_dir)])

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

    def add_aliases(self, aliases: Mapping[str, str]) -> None:
        for name, contents in aliases.items():
            self._execute_command(
                ["git", "config", *self.location_flags, "alias." + name, contents],
                check=True,
            )

    def clear_aliases(self) -> None:
        # We could run `git config --name-only` rather than picking the keys off
        # `get_aliases()`, but this is simpler.
        for name in self.get_aliases().keys():
            self._execute_command(
                [
                    "git",
                    "config",
                    *self.location_flags,
                    "--unset-all",
                    "alias." + name,
                ],
                check=True,
            )

    def execute_git(
        self,
        extra_arguments: Sequence[str],
        *,
        combine_output: bool = False,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        return self._execute_command(
            [*self.base_command, *self.location_flags, *extra_arguments],
            combine_output=combine_output,
            check=check,
        )

    def _execute_command(
        self,
        command: Sequence[str],
        *,
        combine_output: bool = False,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=self.base_dir,
            env=self.env,
            text=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT if combine_output else subprocess.PIPE,
            check=check,
        )

    def get_aliases(self) -> Mapping[str, str]:
        aliases = {}

        try:
            result = self._execute_command(
                [
                    "git",
                    "config",
                    *self.location_flags,
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


# We probably shouldn't be using `frozen=True` here, as the `init=False` fields
# are themselves mutable, but it at least prevents any of the fields from being
# reassigned.
@dataclass(frozen=True)
class Report(AbstractContextManager):
    @dataclass(kw_only=True)
    class Counts:
        tests: int = 0
        successes: int = 0
        failures: int = 0
        errors: int = 0

        def __add__(self, other: "Report.Counts") -> "Report.Counts":
            return Report.Counts(
                tests=self.tests + other.tests,
                successes=self.successes + other.successes,
                failures=self.failures + other.failures,
                errors=self.errors + other.errors,
            )

    class Status(enum.Enum):
        SUCCESS = enum.auto()
        FAILURE = enum.auto()
        ERROR = enum.auto()

        def __add__(self, other: "Report.Status") -> "Report.Status":
            if self == Report.Status.ERROR or other == Report.Status.ERROR:
                return Report.Status.ERROR

            if self == Report.Status.FAILURE or other == Report.Status.FAILURE:
                return Report.Status.FAILURE

            return Report.Status.SUCCESS

    __icons: ClassVar[dict[Status, str]] = {
        Status.SUCCESS: "✔ ",
        Status.FAILURE: "❌ ",
        Status.ERROR: "⚠️ ",
    }
    __indent: ClassVar[str] = "  "

    title: str
    parent: "Report | None" = None
    show_successful: bool = field(default=True, kw_only=True)

    __children: list["Report"] = field(default_factory=list, init=False)
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

        own_counts = Report.Counts(
            tests=int(is_test),
            successes=int(is_success),
            failures=int(is_failure),
            errors=int(is_error),
        )

        if self.__children:
            return own_counts + sum(
                (child.counts for child in self.__children),
                start=Report.Counts(),
            )

        return own_counts

    def create_child_report(self, for_: "Test | Suite") -> "Report":
        child = Report(for_.name, self, show_successful=self.show_successful)

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
        if self.show_successful or self.status is not Report.Status.SUCCESS:
            self.__println(
                Report.__icons[self.status]
                + ("Untitled block" if self.title is None else self.title)
            )

        for failure in self.failures:
            if isinstance(failure, str):
                self.__println(
                    Report.__indent + self.__icons[Report.Status.FAILURE] + failure
                )
            else:
                self.__println(
                    Report.__indent + self.__icons[Report.Status.FAILURE] + failure[0]
                )

                for line in failure[1:]:
                    self.__println(Report.__indent * 2 + line)

        for error in self.errors:
            if isinstance(error, str):
                self.__println(
                    Report.__indent + self.__icons[Report.Status.ERROR] + error
                )
            else:
                self.__println(
                    Report.__indent + self.__icons[Report.Status.ERROR] + error[0]
                )

                for line in error[1:]:
                    self.__println(Report.__indent * 2 + line)

        for child in self.__children:
            child.print()

    def __println(self, line: str) -> None:
        if self.parent is None:
            print(line)
        else:
            self.parent.__println(Report.__indent + line)

    # TODO? make sure this is only called after the report is "finished" and cache it
    @property
    def status(self) -> Status:
        own_status = (
            Report.Status.ERROR
            if self.errors
            else Report.Status.FAILURE
            if self.failures
            else Report.Status.SUCCESS
        )

        if self.__children:
            return own_status + sum(
                (child.status for child in self.__children),
                start=Report.Status.SUCCESS,
            )

        return own_status


@dataclass
class Suite:
    name: str
    tests: Iterable["Test | Suite"]
    before_all: Callable[[], None] = field(default=lambda: None, kw_only=True)
    before_each: Callable[[], None] = field(default=lambda: None, kw_only=True)
    after_each: Callable[[], None] = field(default=lambda: None, kw_only=True)
    after_all: Callable[[], None] = field(default=lambda: None, kw_only=True)

    def run(self, report: Report) -> None:
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


@dataclass
class Test:
    name: str

    context: GitExecutionContext

    extra_arguments: Sequence[str]
    """Extra arguments to add to the command line when executing it."""

    define_aliases: Mapping[str, str] = field(default_factory=dict, kw_only=True)
    """Aliases to create prior to running the test case."""

    exit_code: int | None = field(default=None, kw_only=True)
    """If set, the exit code expected from executing Git.

    If unset, the exit code will be ignored.
    """

    output: str | re.Pattern | CommandOutput | None = field(default=None, kw_only=True)
    """If set, the expected output from executing Git.

    Use a string or pattern to velidate the combined output (stdout and stderr).
    Use `CommandOutput` to validate them individually.

    If unset, the output will be ignored.
    """

    aliases: Mapping[str, str] | None = field(default=None, kw_only=True)
    """The aliases which must be present after the test case has executed.

    Note that *all* aliases defined in the execution context must be present in
    `aliases_after` **and** that *all* aliases in `aliases_after` must be
    defined in the execution context.
    """

    def run(self, report: Report):
        """Executes the test case."""

        if self.define_aliases:
            self.context.add_aliases(self.define_aliases)

        result = self.context.execute_git(
            self.extra_arguments,
            combine_output=not isinstance(self.output, CommandOutput),
        )

        if self.exit_code is not None and result.returncode != self.exit_code:
            report.failures.append(
                f"expected exit code {self.exit_code}, but got {result.returncode}"
            )

        if self.output is not None:
            if isinstance(self.output, CommandOutput):
                if not _is_valid_output(self.output.stdout, result.stdout):
                    report.failures.append(
                        f"expected {_format_expected_output(self.output.stdout)}"
                        f" on stdout, but got {repr(result.stdout)}"
                    )

                if not _is_valid_output(self.output.stderr, result.stderr):
                    report.failures.append(
                        f"expected {_format_expected_output(self.output.stderr)}"
                        f" on stderr, but got {repr(result.stderr)}"
                    )
            else:
                if not _is_valid_output(self.output, result.stdout):
                    report.failures.append(
                        f"expected {_format_expected_output(self.output)}"
                        f" as output, but got {repr(result.stdout)}"
                    )

        if self.aliases is not None:
            aliases = self.context.get_aliases()

            if aliases != self.aliases:
                report.failures.append(
                    f"expected aliases {repr(self.aliases)}, but found {repr(aliases)}"
                )

        self.context.clear_aliases()
