from dataclasses import replace

from testlib import (
    COMMON_PARAMETERS,
    CommandOutput,
    TestExecutionContext,
    TestCase,
    TestSuite,
    format_parameters,
    get_parameter_matrix,
)


def get_test_suite() -> TestSuite:
    tests = []

    for parameters in get_parameter_matrix(
        {
            parameter: COMMON_PARAMETERS[parameter]
            for parameter in ["command-alias", "location-flags"]
        }
    ):
        context = TestExecutionContext()

        # Also used to construct the "default" test case.
        shell_flag = TestCase(
            "--shell flag",
            context,
            [*parameters["command-alias"], *parameters["location-flags"], "--shell"],
            exit_code=0,
            output="",
        )

        # Also used to construct the "--config" test case.
        config_header_flags = TestCase(
            "--config --header flags",
            context,
            [
                *parameters["command-alias"],
                *parameters["location-flags"],
                "--config",
                "--header",
            ],
            exit_code=0,
            output=CommandOutput(stdout="[alias]\n", stderr=""),
        )

        # Also used to construct the "--json" test case.
        json_pretty_flags = TestCase(
            "--json --pretty flags",
            context,
            [
                *parameters["command-alias"],
                *parameters["location-flags"],
                "--json",
                "--pretty",
            ],
            exit_code=0,
            output=CommandOutput(stdout="{}\n", stderr=""),
        )

        tests.append(
            TestSuite(
                f"with parameters {format_parameters(parameters)}",
                [
                    replace(
                        shell_flag,
                        name="default",
                        command_line=[
                            *parameters["command-alias"],
                            *parameters["location-flags"],
                        ],
                    ),
                    shell_flag,
                    replace(
                        config_header_flags,
                        name="--config flag",
                        command_line=[
                            *parameters["command-alias"],
                            *parameters["location-flags"],
                            "--config",
                        ],
                    ),
                    config_header_flags,
                    TestCase(
                        "--config --no-header flags",
                        context,
                        [
                            *parameters["command-alias"],
                            *parameters["location-flags"],
                            "--config",
                            "--no-header",
                        ],
                        exit_code=0,
                        output="",
                    ),
                    replace(
                        json_pretty_flags,
                        name="--json flag",
                        command_line=[
                            *parameters["command-alias"],
                            *parameters["location-flags"],
                            "--json",
                        ],
                    ),
                    json_pretty_flags,
                    TestCase(
                        "--json --compact flags",
                        context,
                        [
                            *parameters["command-alias"],
                            *parameters["location-flags"],
                            "--json",
                            "--compact",
                        ],
                        exit_code=0,
                        output=CommandOutput(stdout="{}", stderr=""),
                    ),
                ],
            )
        )

    return TestSuite("alias: output formatting (no aliases defined)", tests)
