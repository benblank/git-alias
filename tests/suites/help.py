import re

from testlib import CommandOutput, Suite, Test


_USAGE_GENERAL = re.compile(
    r"^\s*Usage:\s+git alias \[location flag\] <add|remove|show>", re.MULTILINE
)
_USAGE_ADD = re.compile(r"^\s*Usage:\s+git alias \[location flag\] add\b", re.MULTILINE)
_USAGE_REMOVE = re.compile(
    r"^\s*Usage:\s+git alias \[location flag\] remove\b", re.MULTILINE
)
_USAGE_SHOW = re.compile(
    r"^\s*Usage:\s+git alias \[location flag\] show\b", re.MULTILINE
)


def get_suite() -> Suite:
    return Suite(
        "help/usage",
        [
            Test(
                "no parameters",
                ["git-alias.sh"],
                exit_code=1,
                output=CommandOutput(stdout="", stderr=_USAGE_GENERAL),
            ),
            Test(
                "invalid flag",
                ["git-alias.sh", "--not-a-real-flag"],
                exit_code=1,
                output=CommandOutput(stdout="", stderr=_USAGE_GENERAL),
            ),
            Test(
                "invalid subcommand",
                ["git-alias.sh", "not-a-real-subcommand"],
                exit_code=1,
                output=CommandOutput(stdout="", stderr=_USAGE_GENERAL),
            ),
            Test(
                "--help flag",
                ["git-alias.sh", "--help"],
                exit_code=0,
                output=CommandOutput(stdout="", stderr=_USAGE_GENERAL),
            ),
            Test(
                "help subcommand",
                ["git-alias.sh", "help"],
                exit_code=0,
                output=CommandOutput(stdout="", stderr=_USAGE_GENERAL),
            ),
            Test(
                "--help flag with invalid subcommand",
                ["git-alias.sh", "--help", "foo"],
                exit_code=1,
                output=CommandOutput(
                    stdout="",
                    stderr=[
                        re.compile(r"^\s*Unrecognized command 'foo'\.$", re.MULTILINE),
                        _USAGE_GENERAL,
                    ],
                ),
            ),
            Test(
                "help subcommand with invalid subcommand",
                ["git-alias.sh", "help", "foo"],
                exit_code=1,
                output=CommandOutput(
                    stdout="",
                    stderr=[
                        re.compile(r"^\s*Unrecognized command 'foo'\.$", re.MULTILINE),
                        _USAGE_GENERAL,
                    ],
                ),
            ),
            Test(
                "--help flag for add",
                ["git-alias.sh", "--help", "add"],
                exit_code=0,
                output=CommandOutput(stdout="", stderr=_USAGE_ADD),
            ),
            Test(
                "help subcommand for add",
                ["git-alias.sh", "help", "add"],
                exit_code=0,
                output=CommandOutput(stdout="", stderr=_USAGE_ADD),
            ),
            Test(
                "--help flag for remove",
                ["git-alias.sh", "--help", "remove"],
                exit_code=0,
                output=CommandOutput(stdout="", stderr=_USAGE_REMOVE),
            ),
            Test(
                "help subcommand for remove",
                ["git-alias.sh", "help", "remove"],
                exit_code=0,
                output=CommandOutput(stdout="", stderr=_USAGE_REMOVE),
            ),
            Test(
                "--help flag for show",
                ["git-alias.sh", "--help", "show"],
                exit_code=0,
                output=CommandOutput(stdout="", stderr=_USAGE_SHOW),
            ),
            Test(
                "help subcommand for show",
                ["git-alias.sh", "help", "show"],
                exit_code=0,
                output=CommandOutput(stdout="", stderr=_USAGE_SHOW),
            ),
        ],
    )
