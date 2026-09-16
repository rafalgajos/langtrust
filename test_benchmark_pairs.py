from src.langtrust.benchmark.pairs import (
    group_benchmark_pairs,
)


pairs = group_benchmark_pairs(
    "scenarios"
)


print()
print("=" * 80)
print("LANGTRUST BENCHMARK PAIRS")
print("=" * 80)


for pair_id, pair in sorted(
    pairs.items()
):

    attack = pair["attack"]
    benign = pair["benign"]

    domain = (
        attack[
            "benchmark"
        ][
            "domain"
        ]
    )

    print()
    print(
        "PAIR:",
        pair_id
    )

    print(
        "DOMAIN:",
        domain
    )

    print(
        "ATTACK:",
        attack[
            "_scenario_file"
        ]
    )

    print(
        "BENIGN:",
        benign[
            "_scenario_file"
        ]
    )

    print(
        "ATTACK FACTORS:",
        attack[
            "benchmark"
        ][
            "active_language_factors"
        ]
    )

    print(
        "BENIGN FACTORS:",
        benign[
            "benchmark"
        ][
            "active_language_factors"
        ]
    )


assert set(
    pairs
) == {
    "invoice_email_001",
    "calendar_delete_001",
    "file_write_001",
}


assert (
    pairs[
        "invoice_email_001"
    ][
        "attack"
    ][
        "benchmark"
    ][
        "domain"
    ]
    == "invoice"
)


assert (
    pairs[
        "calendar_delete_001"
    ][
        "attack"
    ][
        "benchmark"
    ][
        "domain"
    ]
    == "calendar"
)


assert (
    pairs[
        "file_write_001"
    ][
        "attack"
    ][
        "benchmark"
    ][
        "domain"
    ]
    == "files"
)


for pair_id in pairs:

    attack_factors = (
        pairs[
            pair_id
        ][
            "attack"
        ][
            "benchmark"
        ][
            "active_language_factors"
        ]
    )

    benign_factors = (
        pairs[
            pair_id
        ][
            "benign"
        ][
            "benchmark"
        ][
            "active_language_factors"
        ]
    )

    assert (
        "attack_payload"
        in attack_factors
    )

    assert (
        "attack_payload"
        not in benign_factors
    )


assert (
    pairs[
        "file_write_001"
    ][
        "benign"
    ][
        "benchmark"
    ][
        "active_language_factors"
    ]
    == [
        "user_instruction",
        "tool_description",
    ]
)


print()
print(
    "PASS: all 3 benchmark pairs "
    "are valid"
)
