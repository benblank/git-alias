from testlib import (
    COMMON_ALIASES,
    CONFIG_LOCATIONS,
    LOCATION_FLAGS,
    CommandOutput,
    GitExecutionContext,
    Suite,
    Test,
    pick,
)


ALL_ALIASES = {
    location_flags: COMMON_ALIASES for location_flags in LOCATION_FLAGS.values()
}


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

        location_flags = LOCATION_FLAGS[location_name]

        config_tests.append(
            Test(
                setting if setting else "(not set)",
                ["git-unalias.sh", "ml"],
                context,
                define_aliases=ALL_ALIASES,
                exit_code=0,
                output=CommandOutput(stdout="'unset ml'\n", stderr=""),
                aliases={
                    **ALL_ALIASES,
                    location_flags: pick(COMMON_ALIASES, ["foo", "func"]),
                },
            )
        )

    for name, location_flags in LOCATION_FLAGS.items():
        context = GitExecutionContext()

        # Define a config setting, which should always be overridden by the cli
        # flags.
        context.execute_command(
            ["git", "config", "--local", "git-alias.config-file", "../gitconfig-unused"]
        )

        # And some aliases which should always remain after the command has run.
        context.add_aliases(("--file", "../gitconfig-unused"), COMMON_ALIASES)

        cli_tests.append(
            Test(
                name,
                ["git-unalias.sh", *location_flags, "ml"],
                context,
                define_aliases=ALL_ALIASES,
                exit_code=0,
                output=CommandOutput(stdout="'unset ml'\n", stderr=""),
                aliases={
                    **ALL_ALIASES,
                    ("--file", "../gitconfig-unused"): COMMON_ALIASES,
                    location_flags: pick(COMMON_ALIASES, ["foo", "func"]),
                },
            )
        )

    return Suite(
        "unalias",
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
