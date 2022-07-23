from testlib import (
    ALIAS_COMMANDS,
    COMMON_ALIASES,
    CommandOutput,
    Suite,
    Test,
)


def get_suite() -> Suite:
    return Suite(
        "alias",
        [
            Suite(
                "no positional parameters",
                [
                    Suite(
                        "command types",
                        [
                            Test(
                                name,
                                [*command, "--global", "--shell"],
                                define_aliases={("--global",): COMMON_ALIASES},
                                exit_code=0,
                                output=CommandOutput(
                                    stdout="git alias foo 'diff'\n"
                                    "git alias ml '!echo foo\necho bar'\n"
                                    "git alias func '!f() {}; f'\n",
                                    stderr="",
                                ),
                            )
                            for name, command in ALIAS_COMMANDS.items()
                        ],
                    )
                ],
            )
        ],
    )
