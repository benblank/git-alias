import re
from testlib import CommandOutput, Suite, Test, pick


_COMMON_ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}


def get_suite() -> Suite:
    return Suite(
        "remove",
        [
            Test(
                "removes only the named alias",
                ["git-alias.sh", "--global", "remove", "ml"],
                define_aliases={("--global",): _COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(stdout="'unset ml'\n", stderr=""),
                aliases={("--global",): pick(_COMMON_ALIASES, ["foo", "func"])},
            ),
            Test(
                "supports wildcards",
                ["git-alias.sh", "--global", "remove", "f*"],
                define_aliases={("--global",): _COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(stdout="'unset foo'\n'unset func'\n", stderr=""),
                aliases={("--global",): pick(_COMMON_ALIASES, ["ml"])},
            ),
            Test(
                "supports multiple parameters",
                ["git-alias.sh", "--global", "remove", "ml", "func"],
                define_aliases={("--global",): _COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(stdout="'unset ml'\n'unset func'\n", stderr=""),
                aliases={("--global",): pick(_COMMON_ALIASES, ["foo"])},
            ),
            Test(
                "complains when no patterns are provided",
                ["git-alias.sh", "--global", "remove"],
                define_aliases={("--global",): _COMMON_ALIASES},
                exit_code=1,
                output=CommandOutput(
                    stdout="",
                    stderr=[
                        re.compile(r"\bpatterns?\b"),
                        re.compile(r"^\s*Usage: git alias\b.+\sremove\s", re.MULTILINE),
                    ],
                ),
                aliases={("--global",): _COMMON_ALIASES},
            ),
            Test(
                "complains when a pattern doesn't match any aliases",
                ["git-alias.sh", "--global", "remove", "no-such-alias", "f*"],
                define_aliases={("--global",): _COMMON_ALIASES},
                exit_code=1,
                output=CommandOutput(
                    stdout="'unset foo'\n'unset func'\n",
                    stderr='No aliases matching "no-such-alias" were found.\n',
                ),
                aliases={("--global",): pick(_COMMON_ALIASES, ["ml"])},
            ),
            Test(
                "doesn't remove aliases with --dry-run",
                ["git-alias.sh", "--global", "remove", "--dry-run", "*"],
                define_aliases={("--global",): _COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(
                    stdout="[dry-run] 'unset foo'\n[dry-run] 'unset ml'\n[dry-run] 'unset func'\n",
                    stderr="",
                ),
                aliases={("--global",): _COMMON_ALIASES},
            ),
        ],
    )
