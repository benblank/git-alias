from dataclasses import replace

from testlib import (
    COMMANDS_ALIAS,
    LOCATION_FLAGS,
    CommandOutput,
    GitExecutionContext,
    Suite,
    Test,
)


def get_suite() -> Suite:
    tests = []

    for command in COMMANDS_ALIAS:
        for location_flags in LOCATION_FLAGS:
            context = GitExecutionContext()

            # Also used to construct the "default" test case.
            shell_flag = Test(
                "--shell flag",
                context,
                [*command, *location_flags, "--shell"],
                exit_code=0,
                output="",
            )

            # Also used to construct the "--config" test case.
            config_header_flags = Test(
                "--config --header flags",
                context,
                [*command, *location_flags, "--config", "--header"],
                exit_code=0,
                output=CommandOutput(stdout="[alias]\n", stderr=""),
            )

            # Also used to construct the "--json" test case.
            json_pretty_flags = Test(
                "--json --pretty flags",
                context,
                [*command, *location_flags, "--json", "--pretty"],
                exit_code=0,
                output=CommandOutput(stdout="{}\n", stderr=""),
            )

            tests.append(
                Suite(
                    f"with parameters command={command}, location_flags={location_flags}",
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
                            exit_code=0,
                            output="",
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
                            exit_code=0,
                            output=CommandOutput(stdout="{}", stderr=""),
                        ),
                    ],
                )
            )

    return Suite("alias: output formatting (no aliases defined)", tests)
