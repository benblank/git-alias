from dataclasses import replace

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


def get_suite() -> Suite:
    tests = []

    for parameters in get_parameter_matrix(
        pick(COMMON_PARAMETERS, ["command-alias", "location-flags"])
    ):
        context = GitExecutionContext(
            parameters["command-alias"], parameters["location-flags"]
        )

        # Also used to construct the "default" test case.
        shell_flag = Test(
            "--shell flag",
            context,
            ["--shell"],
            exit_code=0,
            output="",
        )

        # Also used to construct the "--config" test case.
        config_header_flags = Test(
            "--config --header flags",
            context,
            ["--config", "--header"],
            exit_code=0,
            output=CommandOutput(stdout="[alias]\n", stderr=""),
        )

        # Also used to construct the "--json" test case.
        json_pretty_flags = Test(
            "--json --pretty flags",
            context,
            ["--json", "--pretty"],
            exit_code=0,
            output=CommandOutput(stdout="{}\n", stderr=""),
        )

        tests.append(
            Suite(
                f"with parameters {format_parameters(parameters)}",
                [
                    replace(
                        shell_flag,
                        name="default",
                        extra_arguments=[],
                    ),
                    shell_flag,
                    replace(
                        config_header_flags,
                        name="--config flag",
                        extra_arguments=["--config"],
                    ),
                    config_header_flags,
                    Test(
                        "--config --no-header flags",
                        context,
                        ["--config", "--no-header"],
                        exit_code=0,
                        output="",
                    ),
                    replace(
                        json_pretty_flags,
                        name="--json flag",
                        extra_arguments=["--json"],
                    ),
                    json_pretty_flags,
                    Test(
                        "--json --compact flags",
                        context,
                        ["--json", "--compact"],
                        exit_code=0,
                        output=CommandOutput(stdout="{}", stderr=""),
                    ),
                ],
            )
        )

    return Suite("alias: output formatting (no aliases defined)", tests)
