from dataclasses import replace

from testlib import (
    COMMON_PARAMETERS,
    CommandOutput,
    GitExecutionContext,
    Suite,
    Test,
    format_parameters,
    get_parameter_matrix,
    pick,
)

ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}


def get_suite() -> Suite:
    tests: list[Test | Suite] = []

    for parameters in get_parameter_matrix(
        pick(COMMON_PARAMETERS, ["command-alias", "location-flags"])
    ):
        command = parameters["command-alias"]
        location_flags = parameters["location-flags"]
        context = GitExecutionContext()

        # Also used to construct the "default" test case.
        shell_flag = Test(
            "--shell flag",
            context,
            [*command, *location_flags, "--shell"],
            define_aliases={location_flags: ALIASES},
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
            [*command, *location_flags, "--config", "--header"],
            define_aliases={location_flags: ALIASES},
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
            [*command, *location_flags, "--json", "--pretty"],
            define_aliases={location_flags: ALIASES},
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
                        command_line=[*command, *location_flags],
                    ),
                    shell_flag,
                    replace(
                        config_header_flags,
                        name="--config flag",
                        command_line=[*command, *location_flags, "--config"],
                    ),
                    config_header_flags,
                    Test(
                        "--config --no-header flags",
                        context,
                        [*command, *location_flags, "--config", "--no-header"],
                        define_aliases={location_flags: ALIASES},
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
                        command_line=[*command, *location_flags, "--json"],
                    ),
                    json_pretty_flags,
                    Test(
                        "--json --compact flags",
                        context,
                        [*command, *location_flags, "--json", "--compact"],
                        define_aliases={location_flags: ALIASES},
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
