from collections import defaultdict
from dataclasses import dataclass, field
from testlib import CommandOutput, Suite, Test


@dataclass
class FormattingParameters:
    name: str = field(init=False)
    arguments: list[str]
    output_func: str
    output_f_star: str
    output_all: str
    empty: str = ""

    def __post_init__(self) -> None:
        if not self.arguments:
            self.name = "(no formatting flags)"
        elif len(self.arguments) == 1:
            self.name = self.arguments[0] + " flag"
        else:
            self.name = " ".join(self.arguments) + " flags"


_COMMON_ALIASES = {"foo": "diff", "ml": "!echo foo\necho bar", "func": "!f() {}; f"}

_FORMATTING_PARAMETERS = [
    FormattingParameters(
        [],
        '[alias]\n\tfunc = "!f() {}; f"\n',
        '[alias]\n\tfoo = "diff"\n\tfunc = "!f() {}; f"\n',
        '[alias]\n\tfoo = "diff"\n\tml = "!echo foo\\necho bar"\n\tfunc = "!f() {}; f"\n',
        "[alias]\n",
    ),
    FormattingParameters(
        ["--shell"],
        "git alias add func '!f() {}; f'\n",
        "git alias add foo 'diff'\ngit alias add func '!f() {}; f'\n",
        "git alias add foo 'diff'\ngit alias add ml '!echo foo\necho bar'\ngit alias add func '!f() {}; f'\n",
    ),
    FormattingParameters(
        ["--config"],
        '[alias]\n\tfunc = "!f() {}; f"\n',
        '[alias]\n\tfoo = "diff"\n\tfunc = "!f() {}; f"\n',
        '[alias]\n\tfoo = "diff"\n\tml = "!echo foo\\necho bar"\n\tfunc = "!f() {}; f"\n',
        "[alias]\n",
    ),
    FormattingParameters(
        ["--config-no-header"],
        'func = "!f() {}; f"\n',
        'foo = "diff"\nfunc = "!f() {}; f"\n',
        'foo = "diff"\nml = "!echo foo\\necho bar"\nfunc = "!f() {}; f"\n',
    ),
    FormattingParameters(
        ["--json"],
        '{\n  "func": "!f() {}; f"\n}\n',
        '{\n  "foo": "diff",\n  "func": "!f() {}; f"\n}\n',
        '{\n  "foo": "diff",\n  "ml": "!echo foo\\necho bar",\n  "func": "!f() {}; f"\n}\n',
        "{}\n",
    ),
    FormattingParameters(
        ["--json-compact"],
        '{"func":"!f() {}; f"}',
        '{"foo":"diff","func":"!f() {}; f"}',
        '{"foo":"diff","ml":"!echo foo\\necho bar","func":"!f() {}; f"}',
        "{}",
    ),
    FormattingParameters(["--names-only"], "func\n", "foo\nfunc\n", "foo\nml\nfunc\n"),
]


def get_suite() -> Suite:
    formatting_tests: dict[str, list[Test]] = defaultdict(list)

    for parameters in _FORMATTING_PARAMETERS:
        formatting_tests["single, named alias"].append(
            Test(
                parameters.name,
                ["git-alias.sh", "--global", "show", *parameters.arguments, "func"],
                define_aliases={("--global",): _COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(stdout=parameters.output_func, stderr=""),
            )
        )

        formatting_tests["pattern matching multiple aliases"].append(
            Test(
                parameters.name,
                ["git-alias.sh", "--global", "show", *parameters.arguments, "f*"],
                define_aliases={("--global",): _COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(stdout=parameters.output_f_star, stderr=""),
            )
        )

        formatting_tests["all aliases, implicitly"].append(
            Test(
                parameters.name,
                ["git-alias.sh", "--global", "show", *parameters.arguments],
                define_aliases={("--global",): _COMMON_ALIASES},
                exit_code=0,
                output=CommandOutput(stdout=parameters.output_all, stderr=""),
            )
        )

    return Suite(
        "show",
        [
            Test(
                "complains when a pattern doesn't match any aliases",
                ["git-alias.sh", "--global", "show", "no-such-alias"],
                exit_code=1,
                output=CommandOutput(
                    stdout="",
                    stderr='No aliases matching "no-such-alias" were found.\n',
                ),
            ),
            *(Suite(name, tests) for name, tests in formatting_tests.items()),
        ],
    )
