from contextlib import AbstractContextManager
from dataclasses import dataclass, field
import enum
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
from typing import ClassVar, Hashable, Iterable, Mapping, Sequence, Type, TypeVar
import weakref


K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

_TESTS_DIR = (Path.cwd() / Path(__file__)).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
_TEMP_ROOT = _TESTS_DIR / "tmp"

ALIAS_COMMANDS = {
    "symlink with absolute path": ["git", "alias-abs"],
    "symlink with relative path": ["git", "alias-rel"],
    "no symlink": ["git-alias.sh"],
}

UNALIAS_COMMANDS = {
    "symlink with absolute path": ["git", "unalias-abs"],
    "symlink with relative path": ["git", "unalias-rel"],
    "no symlink": ["git-unalias.sh"],
}

LOCATION_FLAGS: dict[str, tuple[str, ...]] = {
    "specific file": ("--file", "../gitconfig-specific-file"),
    "specific file which need quoted": ("--file", "../gitconfig-foo !bar"),
    "global config": ("--global",),
    "local repo config": ("--local",),
    "system config": ("--system",),
}

NO_ALIASES: dict[tuple[str, ...], dict[str, str]] = {
    location_flags: {} for location_flags in LOCATION_FLAGS.values()
}

COMMON_ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}

CONFIG_LOCATIONS = {
    "": "global config",
    "../gitconfig-specific-file": "specific file",
    "../gitconfig-foo !bar": "specific file which need quoted",
    "--file ../gitconfig-specific-file": "specific file",
    "--file ../gitconfig-foo !bar": "specific file which need quoted",
    "--global": "global config",
    "--local": "local repo config",
    "--system": "system config",
}


def _format_expected_output(expected: str | re.Pattern) -> str:
    if isinstance(expected, re.Pattern):
        return f"a string matching /{expected.pattern}/"

    return repr(expected)


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
    def __init__(self) -> None:
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

        self.execute_command(["git", "init", str(self.repo_dir)], cwd=self.base_dir)

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

    def add_aliases(
        self, location_flags: Sequence[str], aliases: Mapping[str, str]
    ) -> None:
        for name, contents in aliases.items():
            self.execute_command(
                ["git", "config", *location_flags, "alias." + name, contents],
                check=True,
            )

    def clear_aliases(self, location_flags: Sequence[str]) -> None:
        # We could run `git config --name-only` rather than picking the keys off
        # `get_aliases()`, but this is simpler.
        for name in self.get_aliases(location_flags).keys():
            self.execute_command(
                ["git", "config", *location_flags, "--unset-all", "alias." + name],
                check=True,
            )

    def execute_command(
        self,
        command: Sequence[str],
        *,
        cwd: Path | None = None,
        combine_output: bool = False,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        cwd = cwd if cwd is not None else self.repo_dir

        return subprocess.run(
            command,
            cwd=cwd,
            env=self.env,
            text=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT if combine_output else subprocess.PIPE,
            check=check,
        )

    def get_aliases(self, location_flags: Sequence[str]) -> Mapping[str, str]:
        aliases = {}

        try:
            result = self.execute_command(
                [
                    "git",
                    "config",
                    *location_flags,
                    "--null",
                    "--get-regexp",
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
                (child.counts for child in self.__children), start=Report.Counts()
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
                (child.status for child in self.__children), start=Report.Status.SUCCESS
            )

        return own_status


@dataclass
class Suite:
    name: str
    tests: Iterable["Test | Suite"]

    @classmethod
    def merge(cls, tests: Iterable["Test | Suite"]) -> Iterable["Test | Suite"]:
        result: list["Test | Suite"] = []
        names: dict[str, Suite] = {}

        for test in tests:
            if isinstance(test, Test):
                result.append(test)

                continue

            if test.name not in names:
                result.append(test)
                names[test.name] = test
            else:
                existing = names[test.name]
                existing.tests = Suite.merge([*existing.tests, *test.tests])

        return result

    def run(self, report: Report) -> None:
        for test in self.tests:
            with report.create_child_report(test) as child_report:
                test.run(child_report)


@dataclass
class Test:
    name: str

    command_line: Sequence[str]
    """The command and arguments to execute.

    Because the first element specifies the command to run, it is an error to
    provide an empty sequence.
    """

    context: GitExecutionContext = field(default_factory=GitExecutionContext)

    define_aliases: Mapping[tuple[str, ...], Mapping[str, str]] = field(
        default_factory=dict, kw_only=True
    )
    """Aliases to create prior to running the test case.

    The keys are the "location" flag(s) to pass to `git config` and the values
    are {name: definition} mappings of aliases to define.
    """

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

    aliases: Mapping[tuple[str, ...], Mapping[str, str]] | None = field(
        default=None, kw_only=True
    )
    """The aliases which must be present after the test case has executed.

    The keys are the "location" flag(s) to pass to `git config` and the values
    are {name: definition} mappings of aliases to check.

    Note that *all* aliases defined in the execution context must be present in
    `aliases_after` **and** that *all* aliases in `aliases_after` must be
    defined in the execution context.
    """

    def run(self, report: Report):
        """Executes the test case."""

        for location_flags, aliases in self.define_aliases.items():
            self.context.add_aliases(location_flags, aliases)

        result = self.context.execute_command(
            self.command_line, combine_output=not isinstance(self.output, CommandOutput)
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
            for location_flags, expected in self.aliases.items():
                actual = self.context.get_aliases(location_flags)

                if actual != expected:
                    report.failures.append(
                        f"expected aliases {repr(self.aliases)}, but found {repr(actual)}"
                    )
