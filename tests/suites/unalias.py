from typing import Callable

from testlib import (
    COMMON_PARAMETERS,
    GitExecutionContext,
    Suite,
    Test,
    format_parameters,
    get_parameter_matrix,
)

ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}


def after_each(context: GitExecutionContext) -> Callable[[], None]:
    def after_each_impl() -> None:
        context.clear_aliases()

    return after_each_impl


def before_each(context: GitExecutionContext) -> Callable[[], None]:
    def before_each_impl() -> None:
        context.add_aliases(ALIASES)

    return before_each_impl


def get_suite() -> Suite:
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
            Suite(
                f"with parameters {format_parameters(parameters)}",
                [
                    Test(
                        "doesn't produce an error",
                        context,
                        ["foo"],
                        exit_code=0,
                    ),
                    Test(
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

    return Suite("unalias: smoke tests", tests)
