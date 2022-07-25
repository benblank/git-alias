from testlib import ALIAS_COMMANDS, NO_ALIASES, Suite, Test


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
                                output="",
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
