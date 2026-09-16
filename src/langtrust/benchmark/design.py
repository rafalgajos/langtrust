from itertools import product


ALL_LANGUAGE_FACTORS = (
    "user_instruction",
    "tool_description",
    "untrusted_content",
    "attack_payload",
)

DEFAULT_LANGUAGES = (
    "en",
    "pl",
)

DEFAULT_INACTIVE_LANGUAGE = "en"


def generate_language_cells(
    scenario,
    languages=DEFAULT_LANGUAGES,
    inactive_language=DEFAULT_INACTIVE_LANGUAGE,
):
    """
    Generate only experimentally active language cells.

    Inactive factors are fixed to one canonical language instead
    of being factorially varied. This prevents artificial duplicate
    cells and pseudoreplication.
    """

    benchmark = scenario["benchmark"]

    active_factors = list(
        benchmark[
            "active_language_factors"
        ]
    )

    unknown = (
        set(active_factors)
        - set(ALL_LANGUAGE_FACTORS)
    )

    if unknown:
        raise ValueError(
            "Unknown language factors: "
            + ", ".join(
                sorted(unknown)
            )
        )


    cells = []

    combinations = product(
        languages,
        repeat=len(active_factors),
    )


    for cell_index, values in enumerate(
        combinations,
        start=1,
    ):
        full_assignment = {
            factor: inactive_language
            for factor in ALL_LANGUAGE_FACTORS
        }

        active_assignment = {}


        for factor, language in zip(
            active_factors,
            values,
        ):
            full_assignment[
                factor
            ] = language

            active_assignment[
                factor
            ] = language


        if active_factors:

            cell_key = "__".join(
                (
                    f"{factor}="
                    f"{active_assignment[factor]}"
                )
                for factor
                in active_factors
            )

        else:

            cell_key = "default"


        cells.append(
            {
                "cell_index":
                    cell_index,

                "cell_key":
                    cell_key,

                "active_language_factors":
                    active_factors,

                "active_language_assignment":
                    active_assignment,

                "language_assignment":
                    full_assignment,

                "inactive_language":
                    inactive_language,
            }
        )


    return cells
