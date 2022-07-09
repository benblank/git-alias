from testlib import NO_ALIASES, CommandOutput, Suite, Test


FORMAT_FLAGS = [
    ["--shell"],
    ["--config"],
    ["--config-no-header"],
    ["--json"],
    ["--json-compact"],
]


def get_suite() -> Suite:
    return Suite(
        "alias",
        [
            Suite(
                "define",
                [
                    Suite(
                        "complains when formatting flags are present",
                        [
                            Test(
                                " ".join(flags) + " flag(s)",
                                ["git-alias.sh", "--global", *flags, "foo", "diff a b"],
                                exit_code=0,
                                output=CommandOutput(
                                    stdout="",
                                    stderr="Format flags have no meaning when creating an alias.\n",
                                ),
                                aliases={
                                    **NO_ALIASES,
                                    ("--global",): {"foo": "diff a b"},
                                },
                            )
                            for flags in FORMAT_FLAGS
                        ],
                    )
                ],
            )
        ],
    )
