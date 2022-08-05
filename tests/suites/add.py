import re
from testlib import CommandOutput, Suite, Test


def get_suite() -> Suite:
    return Suite(
        "add",
        [
            Test(
                "supports a single argument as the body of an alias",
                ["git-alias.sh", "--global", "add", "foo", "diff a b"],
                exit_code=0,
                output=CommandOutput(stdout="", stderr=""),
                aliases={("--global",): {"foo": "diff a b"}},
            ),
            Test(
                "supports multiple arguments as the body of an alias",
                ["git-alias.sh", "--global", "add", "foo", "diff", "a", "b"],
                exit_code=0,
                output=CommandOutput(stdout="", stderr=""),
                aliases={("--global",): {"foo": "diff a b"}},
            ),
            Test(
                "complains when no body is provided",
                ["git-alias.sh", "--global", "add", "foo"],
                exit_code=1,
                output=CommandOutput(
                    stdout="",
                    stderr=[
                        re.compile(r"\bbody\b"),
                        re.compile(r"^\s*Usage: git alias\b.+\sadd\s", re.MULTILINE),
                    ],
                ),
                aliases={("--global",): {}},
            ),
            Test(
                "complains when no name is provided",
                ["git-alias.sh", "--global", "add"],
                exit_code=1,
                output=CommandOutput(
                    stdout="",
                    stderr=[
                        re.compile(r"\bname\b"),
                        re.compile(r"^\s*Usage: git alias\b.+\sadd\s", re.MULTILINE),
                    ],
                ),
                aliases={("--global",): {}},
            ),
        ],
    )
