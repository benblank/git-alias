import re

from testlib import COMMON_ALIASES, CommandOutput, Suite, Test, pick


def get_suite() -> Suite:
    return Suite(
        "unalias",
        [
            Test(
                "removes only the named alias",
                ["git-unalias.sh", "--global", "ml"],
                define_aliases={("--global",): COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(stdout="'unset ml'\n", stderr=""),
                aliases={("--global",): pick(COMMON_ALIASES, ["foo", "func"])},
            ),
            Test(
                "supports wildcards",
                ["git-unalias.sh", "--global", "f*"],
                define_aliases={("--global",): COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(stdout="'unset foo'\n'unset func'\n", stderr=""),
                aliases={("--global",): pick(COMMON_ALIASES, ["ml"])},
            ),
            Test(
                "supports multiple parameters",
                ["git-unalias.sh", "--global", "ml", "func"],
                define_aliases={("--global",): COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(stdout="'unset ml'\n'unset func'\n", stderr=""),
                aliases={("--global",): pick(COMMON_ALIASES, ["foo"])},
            ),
            Test(
                "complains when no patterns are provided",
                ["git-unalias.sh", "--global"],
                define_aliases={("--global",): COMMON_ALIASES},
                exit_code=1,
                output=CommandOutput(stdout="", stderr=re.compile("^Usage: ")),
                aliases={("--global",): COMMON_ALIASES},
            ),
            Test(
                "complains when a pattern doesn't match any aliases",
                ["git-unalias.sh", "--global", "no-such-alias", "f*"],
                define_aliases={("--global",): COMMON_ALIASES},
                exit_code=1,
                output=CommandOutput(
                    stdout="'unset foo'\n'unset func'\n",
                    stderr='No aliases matching "no-such-alias" were found.\n',
                ),
                aliases={("--global",): pick(COMMON_ALIASES, ["ml"])},
            ),
            Test(
                "doesn't remove aliases with --dry-run",
                ["git-unalias.sh", "--global", "--dry-run", "*"],
                define_aliases={("--global",): COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(
                    stdout="[dry-run] 'unset foo'\n[dry-run] 'unset ml'\n[dry-run] 'unset func'\n",
                    stderr="",
                ),
                aliases={("--global",): COMMON_ALIASES},
            ),
        ],
    )
