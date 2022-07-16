from dataclasses import replace
from typing import Callable

from testlib import (
    COMMON_PARAMETERS,
    CommandOutput,
    GitExecutionContext,
    TestCase,
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
            for parameter in ["command-alias", "location-flags"]
        }
    ):
        context = GitExecutionContext(
            parameters["command-alias"], parameters["location-flags"]
        )

        # Also used to construct the "default" test case.
        shell_flag = TestCase(
            "--shell flag",
            context,
            ["--shell"],
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
            ["--config", "--header"],
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
            ["--json", "--pretty"],
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
                        extra_arguments=[],
                    ),
                    shell_flag,
                    replace(
                        config_header_flags,
                        name="--config flag",
                        extra_arguments=["--config"],
                    ),
                    config_header_flags,
                    TestCase(
                        "--config --no-header flags",
                        context,
                        ["--config", "--no-header"],
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
                        extra_arguments=["--json"],
                    ),
                    json_pretty_flags,
                    TestCase(
                        "--json --compact flags",
                        context,
                        ["--json", "--compact"],
                        exit_code=0,
                        output=CommandOutput(
                            stdout='{"foo":"diff","ml":"!echo foo\\necho bar","func":"!f() {}; f"}',
                            stderr="",
                        ),
                    ),
                ],
                before_each=before_each(context),
                after_each=after_each(context),
            )
        )

    return TestSuite("alias: output formatting", tests)
