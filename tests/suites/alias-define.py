from testlib import CommandOutput, Suite, Test


def get_suite() -> Suite:
    return Suite(
        "alias",
        [
            Suite(
                "define",
                [
                    Test(
                        "supports a single argument as the body of an alias",
                        ["git-alias.sh", "--global", "foo", "diff a b"],
                        exit_code=0,
                        output=CommandOutput(stdout="", stderr=""),
                        aliases={("--global",): {"foo": "diff a b"}},
                    ),
                    Test(
                        "supports multiple arguments as the body of an alias",
                        ["git-alias.sh", "--global", "foo", "diff", "a", "b"],
                        exit_code=0,
                        output=CommandOutput(stdout="", stderr=""),
                        aliases={("--global",): {"foo": "diff a b"}},
                    ),
                ],
            )
        ],
    )
