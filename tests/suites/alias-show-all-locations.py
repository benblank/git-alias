import random
import string

from testlib import (
    LOCATION_FLAGS,
    CommandOutput,
    Suite,
    Test,
)


# A mapping of location flags to randomly-generated alias names, so that we can
# tell which location was queried.
LOCATION_ALIAS_NAMES = {
    location_flags: "".join(random.choices(string.ascii_lowercase, k=16))
    for location_flags in LOCATION_FLAGS.values()
}


def get_suite() -> Suite:
    # TODO: test default location + config setting

    return Suite(
        "alias locations (no positional parameters)",
        [
            Test(
                name,
                ["git-alias.sh", *location_flags, "--shell"],
                define_aliases={
                    l_flags: {LOCATION_ALIAS_NAMES[l_flags]: "diff"}
                    for l_flags in LOCATION_FLAGS.values()
                },
                exit_code=0,
                output=CommandOutput(
                    stdout=f"git alias {LOCATION_ALIAS_NAMES[location_flags]} 'diff'\n",
                    stderr="",
                ),
            )
            for name, location_flags in LOCATION_FLAGS.items()
        ],
    )
