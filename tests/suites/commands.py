from testlib import CommandOutput, Suite, Test


_COMMANDS = {
    "symlink with absolute path": ["git", "alias-abs"],
    "symlink with relative path": ["git", "alias-rel"],
    "no symlink": ["git-alias.sh"],
}


def get_suite() -> Suite:
    return Suite(
        "command types",
        [
            Test(
                name,
                [*command, "--global", "show", "--shell", "foo"],
                define_aliases={("--global",): {"foo": "diff a b"}},
                exit_code=0,
                output=CommandOutput(
                    stdout="git alias add foo 'diff a b'\n", stderr=""
                ),
            )
            for name, command in _COMMANDS.items()
        ],
    )
