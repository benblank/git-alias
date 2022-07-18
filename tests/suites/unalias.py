from testlib import (
    COMMON_PARAMETERS,
    GitExecutionContext,
    Suite,
    Test,
    format_parameters,
    get_parameter_matrix,
)

ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}


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
                        aliases={name: ALIASES[name] for name in ["ml", "func"]},
                    ),
                    Test(
                        "doesn't remove aliases with --dry-run",
                        context,
                        ["--dry-run", "foo"],
                        define_aliases=ALIASES,
                        exit_code=0,
                        aliases=ALIASES,
                    ),
                ],
            )
        )

    return Suite("unalias: smoke tests", tests)
