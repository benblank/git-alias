from testlib import ALIAS_COMMANDS, NO_ALIASES, CommandOutput, Suite, Test


def get_suite() -> Suite:
    return Suite(
        "alias",
        [
            Suite(
                "define",
                [
                    Suite(
                        "command types",
                        [
                            Test(
                                name,
                                [*command, "--global", "foo", "diff a b"],
                                exit_code=0,
                                output=CommandOutput(stdout="", stderr=""),
                                aliases={
                                    **NO_ALIASES,
                                    ("--global",): {"foo": "diff a b"},
                                },
                            )
                            for name, command in ALIAS_COMMANDS.items()
                        ],
                    )
                ],
            )
        ],
    )
