from typing import Callable

from testlib import (
    COMMON_PARAMETERS,
    TestCase,
    GitExecutionContext,
    TestSuite,
    add_aliases,
    clear_aliases,
    format_parameters,
    get_parameter_matrix,
)


ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}


def after_each(context: GitExecutionContext) -> Callable[[], None]:
    def after_each_impl() -> None:
        clear_aliases(context)

    return after_each_impl


def before_each(context: GitExecutionContext) -> Callable[[], None]:
    def before_each_impl() -> None:
        add_aliases(context, ALIASES)

    return before_each_impl


def get_test_suite() -> TestSuite:
    tests = []

    for parameters in get_parameter_matrix(
        {
            parameter: COMMON_PARAMETERS[parameter]
            for parameter in ["command-unalias", "location-flags"]
        }
    ):
        context = GitExecutionContext(
            parameters["command-unalias"], parameters["location-flags"]
        )

        tests.append(
            TestSuite(
                f"with parameters {format_parameters(parameters)}",
                [
                    TestCase(
                        "doesn't produce an error",
                        context,
                        ["foo"],
                        exit_code=0,
                    ),
                    TestCase(
                        "doesn't produce an error with --dry-run",
                        context,
                        ["--dry-run", "foo"],
                        exit_code=0,
                    ),
                ],
                before_each=before_each(context),
                after_each=after_each(context),
            )
        )

    return TestSuite("unalias: smoke tests", tests)
