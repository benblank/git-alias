from dataclasses import replace
from typing import Callable, Sequence

from testlib import (
    CommandOutput,
    TestExecutionContext,
    TestCase,
    TestSuite,
    add_aliases,
    clear_aliases,
    common_parameters,
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
    tests = []

    for parameters in get_parameter_matrix(
        {
            parameter: common_parameters[parameter]
            for parameter in ["command-alias", "location-flags"]
        }
    ):
        context = TestExecutionContext()

        # Also used to construct the "default" test case.
        shell_flag = TestCase(
            "--shell flag",
            context,
            [*parameters["command-alias"], *parameters["location-flags"], "--shell"],
            exit_code=0,
            output=CommandOutput(
                stdout="git alias foo 'diff'\n"
                "git alias ml '!echo foo\necho bar'\n"
                "git alias func '!f() {}; f'\n",
                stderr="",
            ),
        )

        # Also used to construct the "--config" test case.
        config_header_flags = TestCase(
            "--config --header flags",
            context,
            [
                *parameters["command-alias"],
                *parameters["location-flags"],
                "--config",
                "--header",
            ],
            exit_code=0,
            output=CommandOutput(
                stdout="[alias]\n"
                '\tfoo = "diff"\n'
                '\tml = "!echo foo\\necho bar"\n'
                '\tfunc = "!f() {}; f"\n',
                stderr="",
            ),
        )

        # Also used to construct the "--json" test case.
        json_pretty_flags = TestCase(
            "--json --pretty flags",
            context,
            [
                *parameters["command-alias"],
                *parameters["location-flags"],
                "--json",
                "--pretty",
            ],
            exit_code=0,
            output=CommandOutput(
                stdout="{\n"
                '  "foo": "diff",\n'
                '  "ml": "!echo foo\\necho bar",\n'
                '  "func": "!f() {}; f"\n'
                "}\n",
                stderr="",
            ),
        )

        tests.append(
            TestSuite(
                f"with parameters {format_parameters(parameters)}",
                [
                    replace(
                        shell_flag,
                        name="default",
                        command_line=[
                            *parameters["command-alias"],
                            *parameters["location-flags"],
                        ],
                    ),
                    shell_flag,
                    replace(
                        config_header_flags,
                        name="--config flag",
                        command_line=[
                            *parameters["command-alias"],
                            *parameters["location-flags"],
                            "--config",
                        ],
                    ),
                    config_header_flags,
                    TestCase(
                        "--config --no-header flags",
                        context,
                        [
                            *parameters["command-alias"],
                            *parameters["location-flags"],
                            "--config",
                            "--no-header",
                        ],
                        exit_code=0,
                        output=CommandOutput(
                            stdout='foo = "diff"\n'
                            'ml = "!echo foo\\necho bar"\n'
                            'func = "!f() {}; f"\n',
                            stderr="",
                        ),
                    ),
                    replace(
                        json_pretty_flags,
                        name="--json flag",
                        command_line=[
                            *parameters["command-alias"],
                            *parameters["location-flags"],
                            "--json",
                        ],
                    ),
                    json_pretty_flags,
                    TestCase(
                        "--json --compact flags",
                        context,
                        [
                            *parameters["command-alias"],
                            *parameters["location-flags"],
                            "--json",
                            "--compact",
                        ],
                        exit_code=0,
                        output=CommandOutput(
                            stdout='{"foo":"diff","ml":"!echo foo\\necho bar","func":"!f() {}; f"}',
                            stderr="",
                        ),
                    ),
                ],
                before_each=before_each(context, parameters["location-flags"]),
                after_each=after_each(context, parameters["location-flags"]),
            )
        )

    return TestSuite("alias: output formatting", tests)
