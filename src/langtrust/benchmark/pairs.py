from collections import defaultdict
from pathlib import Path

import yaml


VALID_CONDITIONS = {
    "attack",
    "benign",
}


KNOWN_LANGUAGE_FACTORS = {
    "user_instruction",
    "tool_description",
    "untrusted_content",
    "attack_payload",
}


def load_scenarios(
    scenario_dir="scenarios",
):
    scenarios = []

    for path in sorted(
        Path(
            scenario_dir
        ).glob(
            "*.yaml"
        )
    ):

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:
            scenario = yaml.safe_load(f)

        scenario["_scenario_file"] = (
            path.name
        )

        scenarios.append(
            scenario
        )

    return scenarios


def benchmark_scenarios(
    scenario_dir="scenarios",
):
    return [
        scenario
        for scenario in load_scenarios(
            scenario_dir
        )
        if "benchmark"
        in scenario
    ]


def group_benchmark_pairs(
    scenario_dir="scenarios",
):
    pairs = defaultdict(
        dict
    )

    scenarios = benchmark_scenarios(
        scenario_dir
    )


    for scenario in scenarios:

        benchmark = (
            scenario[
                "benchmark"
            ]
        )

        pair_id = (
            benchmark.get(
                "pair_id"
            )
        )

        domain = (
            benchmark.get(
                "domain"
            )
        )

        condition = (
            benchmark.get(
                "condition"
            )
        )

        factors = (
            benchmark.get(
                "active_language_factors"
            )
        )


        if not pair_id:
            raise ValueError(
                f"{scenario['_scenario_file']}: "
                "missing benchmark.pair_id"
            )


        if not domain:
            raise ValueError(
                f"{scenario['_scenario_file']}: "
                "missing benchmark.domain"
            )


        if condition not in VALID_CONDITIONS:
            raise ValueError(
                f"{scenario['_scenario_file']}: "
                f"invalid condition "
                f"{condition!r}"
            )


        if not isinstance(
            factors,
            list,
        ):
            raise TypeError(
                f"{scenario['_scenario_file']}: "
                "active_language_factors "
                "must be a list"
            )


        unknown_factors = (
            set(
                factors
            )
            - KNOWN_LANGUAGE_FACTORS
        )

        if unknown_factors:
            raise ValueError(
                f"{scenario['_scenario_file']}: "
                "unknown language factors: "
                + ", ".join(
                    sorted(
                        unknown_factors
                    )
                )
            )


        if condition in pairs[
            pair_id
        ]:
            raise ValueError(
                f"Duplicate {condition!r} "
                f"scenario for pair "
                f"{pair_id!r}"
            )


        pairs[
            pair_id
        ][
            condition
        ] = scenario


    for pair_id, pair in pairs.items():

        missing = (
            VALID_CONDITIONS
            - set(
                pair
            )
        )

        if missing:
            raise ValueError(
                f"Pair {pair_id!r} "
                f"is missing condition(s): "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
            )


        attack_domain = (
            pair[
                "attack"
            ][
                "benchmark"
            ][
                "domain"
            ]
        )

        benign_domain = (
            pair[
                "benign"
            ][
                "benchmark"
            ][
                "domain"
            ]
        )


        if (
            attack_domain
            != benign_domain
        ):
            raise ValueError(
                f"Pair {pair_id!r} "
                "contains different domains: "
                f"{attack_domain!r} vs "
                f"{benign_domain!r}"
            )


        attack_factors = set(
            pair[
                "attack"
            ][
                "benchmark"
            ][
                "active_language_factors"
            ]
        )


        if (
            "attack_payload"
            not in attack_factors
        ):
            raise ValueError(
                f"Attack scenario in "
                f"{pair_id!r} must activate "
                "'attack_payload'"
            )


        benign_factors = set(
            pair[
                "benign"
            ][
                "benchmark"
            ][
                "active_language_factors"
            ]
        )


        if (
            "attack_payload"
            in benign_factors
        ):
            raise ValueError(
                f"Benign scenario in "
                f"{pair_id!r} must not activate "
                "'attack_payload'"
            )


    return dict(
        pairs
    )
