import re

from testlib import (
    COMMON_PARAMETERS,
    CommandOutput,
    GitExecutionContext,
    Suite,
    Test,
    format_parameters,
    get_parameter_matrix,
    pick,
)

ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}
USAGE = re.compile("^Usage: ")


def get_suite() -> Suite:
    tests = []

    for parameters in get_parameter_matrix(
        pick(COMMON_PARAMETERS, ["command-unalias", "location-flags"])
    ):
        command = parameters["command-unalias"]
        location_flags = parameters["location-flags"]
        context = GitExecutionContext()

        tests.append(
            Suite(
                f"with parameters {format_parameters(parameters)}",
                [
                    Test(
                        "removes only the named alias",
                        context,
                        [*command, *location_flags, "foo"],
                        define_aliases={location_flags: ALIASES},
                        exit_code=0,
                        output=CommandOutput(stdout="'unset foo'\n", stderr=""),
                        aliases={location_flags: pick(ALIASES, ["ml", "func"])},
                    ),
                    Test(
                        "supports wildcards",
                        context,
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
                        context,
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
                        context,
                        [*command, *location_flags],
                        define_aliases={location_flags: ALIASES},
                        exit_code=1,
                        output=CommandOutput(stdout="", stderr=USAGE),
                        aliases={location_flags: ALIASES},
                    ),
                    Test(
                        "complains when a pattern doesn't match any aliases",
                        context,
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
                        context,
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
