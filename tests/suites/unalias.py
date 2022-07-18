from typing import Callable, Sequence
from testlib import (
    COMMON_PARAMETERS,
    TestCase,
    TestExecutionContext,
    TestSuite,
    add_aliases,
    clear_aliases,
    format_parameters,
    get_parameter_matrix,
)


ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}


def after_each(
    context: TestExecutionContext, location_flags: Sequence[str]
) -> Callable[[], None]:
    def after_each_impl() -> None:
        clear_aliases(context, location_flags)

    return after_each_impl


def before_each(
    context: TestExecutionContext, location_flags: Sequence[str]
) -> Callable[[], None]:
    def before_each_impl() -> None:
        add_aliases(context, location_flags, ALIASES)

    return before_each_impl


def get_test_suite() -> TestSuite:
    context = TestExecutionContext()

    return TestSuite(
        "unalias: smoke tests",
        [
            TestSuite(
                f"with parameters {format_parameters(parameters)}",
                [
                    TestCase(
                        "doesn't produce an error",
                        context,
                        [
                            *parameters["command-unalias"],
                            *parameters["location-flags"],
                            "foo",
                        ],
                        exit_code=0,
                    ),
                    TestCase(
                        "doesn't produce an error with --dry-run",
                        context,
                        [
                            *parameters["command-unalias"],
                            *parameters["location-flags"],
                            "--dry-run",
                            "foo",
                        ],
                        exit_code=0,
                    ),
                ],
                before_each=before_each(context, parameters["location-flags"]),
                after_each=after_each(context, parameters["location-flags"]),
            )
            for parameters in get_parameter_matrix(
                {
                    parameter: COMMON_PARAMETERS[parameter]
                    for parameter in ["command-unalias", "location-flags"]
                }
            )
        ],
    )
