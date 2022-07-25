from dataclasses import dataclass
from typing import Sequence

from testlib import (
    COMMON_ALIASES,
    CommandOutput,
    Suite,
    Test,
)


@dataclass
class TestParameters:
    extra_arguments: Sequence[str]
    stdout_with_aliases: str
    stdout_without_aliases: str = ""


TEST_PARAMETERS = [
    TestParameters(
        [],
        "git alias foo 'diff'\ngit alias ml '!echo foo\necho bar'\ngit alias func '!f() {}; f'\n",
    ),
    TestParameters(
        ["--shell"],
        "git alias foo 'diff'\ngit alias ml '!echo foo\necho bar'\ngit alias func '!f() {}; f'\n",
    ),
    TestParameters(
        ["--config"],
        '[alias]\n\tfoo = "diff"\n\tml = "!echo foo\\necho bar"\n\tfunc = "!f() {}; f"\n',
        "[alias]\n",
    ),
    TestParameters(
        ["--config-no-header"],
        'foo = "diff"\nml = "!echo foo\\necho bar"\nfunc = "!f() {}; f"\n',
    ),
    TestParameters(
        ["--json"],
        '{\n  "foo": "diff",\n  "ml": "!echo foo\\necho bar",\n  "func": "!f() {}; f"\n}\n',
        "{}\n",
    ),
    TestParameters(
        ["--json-compact"],
        '{"foo":"diff","ml":"!echo foo\\necho bar","func":"!f() {}; f"}',
        "{}",
    ),
    TestParameters(["--names-only"], "foo\nml\nfunc\n", ""),
]


def get_suite() -> Suite:
    no_aliases_tests: list[Test] = []
    aliases_tests: list[Test] = []

    for test_parameters in TEST_PARAMETERS:
        if not test_parameters.extra_arguments:
            name = "(no formatting flags)"
        elif len(test_parameters.extra_arguments) == 1:
            name = test_parameters.extra_arguments[0] + " flag"
        else:
            name = " ".join(test_parameters.extra_arguments) + " flags"

        no_aliases_tests.append(
            Test(
                name,
                ["git-alias.sh", "--global", *test_parameters.extra_arguments],
                exit_code=0,
                output=CommandOutput(
                    stdout=test_parameters.stdout_without_aliases, stderr=""
                ),
            ),
        )

        aliases_tests.append(
            Test(
                name,
                ["git", "alias-abs", "--global", *test_parameters.extra_arguments],
                define_aliases={("--global",): COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(
                    stdout=test_parameters.stdout_with_aliases, stderr=""
                ),
            ),
        )

    return Suite(
        "alias",
        [
            Suite(
                "no positional parameters",
                [
                    Suite(
                        "formatting flags",
                        [
                            Suite("without aliases defined", no_aliases_tests),
                            Suite("with aliases defined", aliases_tests),
                        ],
                    )
                ],
            )
        ],
    )
