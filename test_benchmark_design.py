from src.langtrust.benchmark.design import (
    generate_language_cells,
)
from src.langtrust.benchmark.pairs import (
    group_benchmark_pairs,
)


pairs = group_benchmark_pairs(
    "scenarios"
)


expected_counts = {
    (
        "calendar_delete_001",
        "attack",
    ): 16,

    (
        "calendar_delete_001",
        "benign",
    ): 4,

    (
        "invoice_email_001",
        "attack",
    ): 16,

    (
        "invoice_email_001",
        "benign",
    ): 8,

    (
        "file_write_001",
        "attack",
    ): 16,

    (
        "file_write_001",
        "benign",
    ): 4,
}


total = 0


print()
print("=" * 80)
print("LANGTRUST FACTOR-AWARE DESIGN")
print("=" * 80)


for pair_id, pair in sorted(
    pairs.items()
):

    for condition in (
        "attack",
        "benign",
    ):

        scenario = pair[
            condition
        ]

        cells = (
            generate_language_cells(
                scenario
            )
        )

        expected = (
            expected_counts[
                (
                    pair_id,
                    condition,
                )
            ]
        )


        assert (
            len(cells)
            == expected
        )


        keys = [
            cell[
                "cell_key"
            ]
            for cell in cells
        ]

        assert (
            len(keys)
            == len(set(keys))
        )


        for cell in cells:

            assert set(
                cell[
                    "active_language_assignment"
                ]
            ) == set(
                cell[
                    "active_language_factors"
                ]
            )


        total += len(
            cells
        )


        print(
            pair_id,
            condition,
            "cells=",
            len(cells),
        )


assert total == 64


print()
print(
    "TOTAL UNIQUE DESIGN CELLS:",
    total
)

print(
    "PASS: factor-aware benchmark "
    "design contains exactly 64 cells"
)
