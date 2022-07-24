from testlib import (
    CommandOutput,
    Suite,
    Test,
)


def get_suite() -> Suite:
    return Suite(
        "alias",
        [
            Suite(
                "one positional parameter",
                [
                    Test(
                        "complains when the named alias doesn't exist",
                        ["git-alias.sh", "--global", "--shell", "does-not-exist"],
                        exit_code=1,
                        output=CommandOutput(
                            stdout="",
                            stderr='No alias named "does-not-exist" exists.\n',
                        ),
                    )
                ],
            )
        ],
    )
