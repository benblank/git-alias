from dataclasses import dataclass
from typing import Sequence

from testlib import COMMON_ALIASES, CommandOutput, Suite, Test


@dataclass
class TestParameters:
    extra_arguments: Sequence[str]
    stdout_with_aliases: str
    stdout_without_aliases: str = ""


TEST_PARAMETERS = [
    TestParameters([], "git alias func '!f() {}; f'\n"),
    TestParameters(["--shell"], "git alias func '!f() {}; f'\n"),
    TestParameters(["--config"], '[alias]\n\tfunc = "!f() {}; f"\n', "[alias]\n"),
    TestParameters(["--config-no-header"], 'func = "!f() {}; f"\n'),
    TestParameters(["--json"], '{\n  "func": "!f() {}; f"\n}\n', "{}\n"),
    TestParameters(["--json-compact"], '{"func":"!f() {}; f"}', "{}"),
    TestParameters(["--names-only"], "func\n", ""),
]


def get_suite() -> Suite:
    tests: list[Test] = []

    for test_parameters in TEST_PARAMETERS:
        if not test_parameters.extra_arguments:
            name = "(no formatting flags)"
        elif len(test_parameters.extra_arguments) == 1:
            name = test_parameters.extra_arguments[0] + " flag"
        else:
            name = " ".join(test_parameters.extra_arguments) + " flags"

        tests.append(
            Test(
                name,
                [
                    "git",
                    "alias-abs",
                    "--global",
                    *test_parameters.extra_arguments,
                    "func",
                ],
                define_aliases={("--global",): COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(
                    stdout=test_parameters.stdout_with_aliases, stderr=""
                ),
            )
        )

    return Suite(
        "alias",
        [
            Suite(
                "one positional parameter",
                [Suite("formatting flags", [Suite("with aliases defined", tests)])],
            )
        ],
    )
