import re

from testlib import (
    COMMON_PARAMETERS,
    CommandOutput,
    GitExecutionContext,
    Suite,
    Test,
    format_parameters,
    get_parameter_matrix,
)

ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}
USAGE = re.compile("^Usage: ")


def get_suite() -> Suite:
    tests = []

    for parameters in get_parameter_matrix(
        {
            parameter: COMMON_PARAMETERS[parameter]
            for parameter in ["command-unalias", "location-flags"]
        }
    ):
        context = GitExecutionContext(
            parameters["command-unalias"], parameters["location-flags"]
        )

        tests.append(
            Suite(
                f"with parameters {format_parameters(parameters)}",
                [
                    Test(
                        "removes only the named alias",
                        context,
                        ["foo"],
                        define_aliases=ALIASES,
                        exit_code=0,
                        output=CommandOutput(stdout="'unset foo'\n", stderr=""),
                        aliases={name: ALIASES[name] for name in ["ml", "func"]},
                    ),
                    Test(
                        "supports wildcards",
                        context,
                        ["f*"],
                        define_aliases=ALIASES,
                        exit_code=0,
                        output=CommandOutput(
                            stdout="'unset foo'\n'unset func'\n", stderr=""
                        ),
                        aliases={"ml": ALIASES["ml"]},
                    ),
                    Test(
                        "supports multiple parameters",
                        context,
                        ["ml", "func"],
                        define_aliases=ALIASES,
                        exit_code=0,
                        output=CommandOutput(
                            stdout="'unset ml'\n'unset func'\n", stderr=""
                        ),
                        aliases={"foo": ALIASES["foo"]},
                    ),
                    Test(
                        "complains when no patterns are provided",
                        context,
                        [],
                        define_aliases=ALIASES,
                        exit_code=1,
                        output=CommandOutput(stdout="", stderr=USAGE),
                        aliases=ALIASES,
                    ),
                    Test(
                        "complains when a pattern doesn't match any aliases",
                        context,
                        ["no-such-alias", "f*"],
                        define_aliases=ALIASES,
                        exit_code=1,
                        output=CommandOutput(
                            stdout="'unset foo'\n'unset func'\n",
                            stderr='No aliases matching "no-such-alias" were found.\n',
                        ),
                        aliases={"ml": ALIASES["ml"]},
                    ),
                    Test(
                        "doesn't remove aliases with --dry-run",
                        context,
                        ["--dry-run", "*"],
                        define_aliases=ALIASES,
                        exit_code=0,
                        output=CommandOutput(
                            stdout="[dry-run] 'unset foo'\n[dry-run] 'unset ml'\n[dry-run] 'unset func'\n",
                            stderr="",
                        ),
                        aliases=ALIASES,
                    ),
                ],
            )
        )

    return Suite("unalias", tests)
