import re

from testlib import (
    COMMANDS_UNALIAS,
    LOCATION_FLAGS,
    CommandOutput,
    Suite,
    Test,
    pick,
)

ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}
USAGE = re.compile("^Usage: ")


def get_suite() -> Suite:
    tests = []

    for command in COMMANDS_UNALIAS:
        for location_flags in LOCATION_FLAGS:
            tests.append(
                Suite(
                    f"with parameters command={command}, location_flags={location_flags}",
                    [
                        Test(
                            "removes only the named alias",
                            [*command, *location_flags, "foo"],
                            define_aliases={location_flags: ALIASES},
                            exit_code=0,
                            output=CommandOutput(stdout="'unset foo'\n", stderr=""),
                            aliases={location_flags: pick(ALIASES, ["ml", "func"])},
                        ),
                        Test(
                            "supports wildcards",
                            [*command, *location_flags, "f*"],
                            define_aliases={location_flags: ALIASES},
                            exit_code=0,
                            output=CommandOutput(
                                stdout="'unset foo'\n'unset func'\n", stderr=""
                            ),
                            aliases={location_flags: pick(ALIASES, ["ml"])},
                        ),
                        Test(
                            "supports multiple parameters",
                            [*command, *location_flags, "ml", "func"],
                            define_aliases={location_flags: ALIASES},
                            exit_code=0,
                            output=CommandOutput(
                                stdout="'unset ml'\n'unset func'\n", stderr=""
                            ),
                            aliases={location_flags: pick(ALIASES, ["foo"])},
                        ),
                        Test(
                            "complains when no patterns are provided",
                            [*command, *location_flags],
                            define_aliases={location_flags: ALIASES},
                            exit_code=1,
                            output=CommandOutput(stdout="", stderr=USAGE),
                            aliases={location_flags: ALIASES},
                        ),
                        Test(
                            "complains when a pattern doesn't match any aliases",
                            [*command, *location_flags, "no-such-alias", "f*"],
                            define_aliases={location_flags: ALIASES},
                            exit_code=1,
                            output=CommandOutput(
                                stdout="'unset foo'\n'unset func'\n",
                                stderr='No aliases matching "no-such-alias" were found.\n',
                            ),
                            aliases={location_flags: pick(ALIASES, ["ml"])},
                        ),
                        Test(
                            "doesn't remove aliases with --dry-run",
                            [*command, *location_flags, "--dry-run", "*"],
                            define_aliases={location_flags: ALIASES},
                            exit_code=0,
                            output=CommandOutput(
                                stdout="[dry-run] 'unset foo'\n[dry-run] 'unset ml'\n[dry-run] 'unset func'\n",
                                stderr="",
                            ),
                            aliases={location_flags: ALIASES},
                        ),
                    ],
                )
            )

    return Suite("unalias", tests)
