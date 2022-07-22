from testlib import (
    COMMON_ALIASES,
    LOCATION_FLAGS,
    CommandOutput,
    Suite,
    Test,
    pick,
)


ALL_ALIASES = {
    location_flags: COMMON_ALIASES for location_flags in LOCATION_FLAGS.values()
}


def get_suite() -> Suite:
    # TODO: test default location + config setting

    return Suite(
        "unalias locations",
        [
            Test(
                name,
                ["git-unalias.sh", *location_flags, "ml"],
                define_aliases=ALL_ALIASES,
                exit_code=0,
                output=CommandOutput(stdout="'unset ml'\n", stderr=""),
                aliases={
                    **ALL_ALIASES,
                    location_flags: pick(COMMON_ALIASES, ["foo", "func"]),
                },
            )
            for name, location_flags in LOCATION_FLAGS.items()
        ],
    )
