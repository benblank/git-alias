from dataclasses import replace

from testlib import (
    COMMANDS_ALIAS,
    LOCATION_FLAGS,
    CommandOutput,
    GitExecutionContext,
    Suite,
    Test,
)

ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}


def get_suite() -> Suite:
    tests: list[Test | Suite] = []

    for command in COMMANDS_ALIAS:
        for location_flags in LOCATION_FLAGS:
            # Also used to construct the "default" test case.
            shell_flag = Test(
                "--shell flag",
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
                    f"with parameters command={command}, location_flags={location_flags}",
                    [
                        replace(
                            shell_flag,
                            name="default",
                            command_line=[*command, *location_flags],
                            context=GitExecutionContext(),
                        ),
                        shell_flag,
                        replace(
                            config_header_flags,
                            name="--config flag",
                            command_line=[*command, *location_flags, "--config"],
                            context=GitExecutionContext(),
                        ),
                        config_header_flags,
                        Test(
                            "--config --no-header flags",
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
                            context=GitExecutionContext(),
                        ),
                        json_pretty_flags,
                        Test(
                            "--json --compact flags",
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
