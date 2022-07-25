from testlib import ALIAS_COMMANDS, COMMON_ALIASES, CommandOutput, Suite, Test


def get_suite() -> Suite:
    return Suite(
        "alias",
        [
            Suite(
                "one positional parameter",
                [
                    Suite(
                        "command types",
                        [
                            Test(
                                name,
                                [*command, "--global", "--shell", "func"],
                                define_aliases={("--global",): COMMON_ALIASES},
                                exit_code=0,
                                output=CommandOutput(
                                    stdout="git alias func '!f() {}; f'\n", stderr=""
                                ),
                            )
                            for name, command in ALIAS_COMMANDS.items()
                        ],
                    )
                ],
            )
        ],
    )
