from testlib import (
    CONFIG_LOCATIONS,
    LOCATION_FLAGS,
    NO_ALIASES,
    CommandOutput,
    GitExecutionContext,
    Suite,
    Test,
)


def get_suite() -> Suite:
    config_tests: list[Test] = []
    cli_tests: list[Test] = []

    for setting, location_name in CONFIG_LOCATIONS.items():
        context = GitExecutionContext()

        # Interpret the empty string as not being set.
        if setting:
            context.execute_command(
                ["git", "config", "--local", "git-alias.config-file", setting]
            )

        location_flag = LOCATION_FLAGS[location_name]

        config_tests.append(
            Test(
                setting if setting else "(not set)",
                ["git-alias.sh", "foo", "diff a b"],
                context,
                exit_code=0,
                output=CommandOutput(stdout="", stderr=""),
                aliases={**NO_ALIASES, location_flag: {"foo": "diff a b"}},
            )
        )

    for name, location_flag in LOCATION_FLAGS.items():
        context = GitExecutionContext()

        # Define a config setting, which should always be overridden by the cli
        # flags.
        context.execute_command(
            ["git", "config", "--local", "git-alias.config-file", "../gitconfig-unused"]
        )

        cli_tests.append(
            Test(
                name,
                ["git-alias.sh", *location_flag, "foo", "diff a b"],
                context,
                exit_code=0,
                output=CommandOutput(stdout="", stderr=""),
                aliases={
                    **NO_ALIASES,
                    ("--file", "../gitconfig-unused"): {},
                    location_flag: {"foo": "diff a b"},
                },
            )
        )

    return Suite(
        "alias",
        [
            Suite(
                "define",
                [
                    Suite(
                        "location flags",
                        [
                            Suite("from Git settings", config_tests),
                            Suite("on the command line", cli_tests),
                        ],
                    )
                ],
            )
        ],
    )
