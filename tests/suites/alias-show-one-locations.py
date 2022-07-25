import random
import string

from testlib import (
    CONFIG_LOCATIONS,
    LOCATION_FLAGS,
    CommandOutput,
    GitExecutionContext,
    Suite,
    Test,
)


# A mapping of location flags to randomly-generated alias names, so that we can
# tell which location was queried.
LOCATION_ALIAS_NAMES = {
    location_flags: "".join(random.choices(string.ascii_lowercase, k=16))
    for location_flags in LOCATION_FLAGS.values()
}

UNIQUE_ALIASES = {
    l_flags: {LOCATION_ALIAS_NAMES[l_flags]: "diff"}
    for l_flags in LOCATION_FLAGS.values()
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
                ["git-alias.sh", "--shell", LOCATION_ALIAS_NAMES[location_flags]],
                context,
                define_aliases=UNIQUE_ALIASES,
                exit_code=0,
                output=CommandOutput(
                    stdout=f"git alias {LOCATION_ALIAS_NAMES[location_flags]} 'diff'\n",
                    stderr="",
                ),
            )
        )

    for name, location_flags in LOCATION_FLAGS.items():
        context = GitExecutionContext()

        # Define a config setting, which should always be overridden by the cli
        # flags.
        context.execute_command(
            ["git", "config", "--local", "git-alias.config-file", "../gitconfig-unused"]
        )

        # And an alias which should never appear in the output.
        context.add_aliases(("--file", "../gitconfig-unused"), {"foo": "log"})

        cli_tests.append(
            Test(
                name,
                [
                    "git-alias.sh",
                    *location_flags,
                    "--shell",
                    LOCATION_ALIAS_NAMES[location_flags],
                ],
                context,
                define_aliases=UNIQUE_ALIASES,
                exit_code=0,
                output=CommandOutput(
                    stdout=f"git alias {LOCATION_ALIAS_NAMES[location_flags]} 'diff'\n",
                    stderr="",
                ),
            )
        )

    return Suite(
        "alias",
        [
            Suite(
                "one positional parameter",
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
