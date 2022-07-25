from testlib import COMMON_ALIASES, UNALIAS_COMMANDS, CommandOutput, Suite, Test, pick


def get_suite() -> Suite:
    return Suite(
        "unalias",
        [
            Suite(
                "command types",
                [
                    Test(
                        name,
                        [*command, "--global", "ml"],
                        define_aliases={("--global",): COMMON_ALIASES},
                        exit_code=0,
                        output=CommandOutput(stdout="'unset ml'\n", stderr=""),
                        aliases={("--global",): pick(COMMON_ALIASES, ["foo", "func"])},
                    )
                    for name, command in UNALIAS_COMMANDS.items()
                ],
            )
        ],
    )
