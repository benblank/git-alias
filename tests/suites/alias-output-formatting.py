from dataclasses import replace

from testlib import (
    COMMON_PARAMETERS,
    CommandOutput,
    GitExecutionContext,
    Suite,
    Test,
    format_parameters,
    get_parameter_matrix,
)

ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}


def get_suite() -> Suite:
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
        shell_flag = Test(
            "--shell flag",
            context,
            ["--shell"],
            define_aliases=ALIASES,
            exit_code=0,
            output=CommandOutput(
                stdout="git alias foo 'diff'\n"
                "git alias ml '!echo foo\necho bar'\n"
                "git alias func '!f() {}; f'\n",
                stderr="",
            ),
        )

        # Also used to construct the "--config" test case.
        config_header_flags = Test(
            "--config --header flags",
            context,
            ["--config", "--header"],
            define_aliases=ALIASES,
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
        json_pretty_flags = Test(
            "--json --pretty flags",
            context,
            ["--json", "--pretty"],
            define_aliases=ALIASES,
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
            Suite(
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
                    Test(
                        "--config --no-header flags",
                        context,
                        ["--config", "--no-header"],
                        define_aliases=ALIASES,
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
                    Test(
                        "--json --compact flags",
                        context,
                        ["--json", "--compact"],
                        define_aliases=ALIASES,
                        exit_code=0,
                        output=CommandOutput(
                            stdout='{"foo":"diff","ml":"!echo foo\\necho bar","func":"!f() {}; f"}',
                            stderr="",
                        ),
                    ),
                ],
            )
        )

    return Suite("alias: output formatting", tests)
