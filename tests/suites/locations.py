import random
import string
from testlib import CommandOutput, GitExecutionContext, Suite, Test


_CONFIG_LOCATIONS = {
    "": "global config",
    "../gitconfig-specific-file": "specific file",
    "../gitconfig-foo !bar": "specific file which needs quoted",
    "--file ../gitconfig-specific-file": "specific file",
    "--file ../gitconfig-foo !bar": "specific file which needs quoted",
    "--global": "global config",
    "--local": "local repo config",
    "--system": "system config",
}

_LOCATION_FLAGS: dict[str, tuple[str, ...]] = {
    "specific file": ("--file", "../gitconfig-specific-file"),
    "specific file which needs quoted": ("--file", "../gitconfig-foo !bar"),
    "global config": ("--global",),
    "local repo config": ("--local",),
    "system config": ("--system",),
}

_RANDOM_NAMES: dict[tuple[str, ...], str] = {
    location_flag: "".join(random.choices(string.ascii_lowercase, k=16))
    for location_flag in _LOCATION_FLAGS.values()
}

_RANDOM_ALIASES: dict[tuple[str, ...], dict[str, str]] = {
    location_flag: {_RANDOM_NAMES[location_flag]: "diff"}
    for location_flag in _LOCATION_FLAGS.values()
}


def get_suite() -> Suite:
    config_tests: list[Test] = []
    cli_tests: list[Test] = []

    for setting, location_name in _CONFIG_LOCATIONS.items():
        context = GitExecutionContext()

        # Interpret the empty string as not being set.
        if setting:
            context.execute_command(
                ["git", "config", "--local", "git-alias.config-file", setting]
            )

        location_flag = _LOCATION_FLAGS[location_name]

        config_tests.append(
            Test(
                setting if setting else "(not set)",
                [
                    "git-alias.sh",
                    "show",
                    "--config-no-header",
                    _RANDOM_NAMES[location_flag],
                ],
                context,
                define_aliases=_RANDOM_ALIASES,
                exit_code=0,
                output=CommandOutput(
                    stdout=f'{_RANDOM_NAMES[location_flag]} = "diff"\n', stderr=""
                ),
            )
        )

    for name, location_flag in _LOCATION_FLAGS.items():
        context = GitExecutionContext()

        # Define a config setting, which should always be overridden by the cli
        # flag.
        context.execute_command(
            ["git", "config", "--local", "git-alias.config-file", "../gitconfig-unused"]
        )

        cli_tests.append(
            Test(
                name,
                [
                    "git-alias.sh",
                    *location_flag,
                    "show",
                    "--config-no-header",
                    _RANDOM_NAMES[location_flag],
                ],
                context,
                define_aliases=_RANDOM_ALIASES,
                exit_code=0,
                output=CommandOutput(
                    stdout=f'{_RANDOM_NAMES[location_flag]} = "diff"\n', stderr=""
                ),
            )
        )

    return Suite(
        "location flags",
        [
            Suite("from Git settings", config_tests),
            Suite("on the command line", cli_tests),
        ],
    )
