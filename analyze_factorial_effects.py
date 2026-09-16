import argparse
import json
from collections import defaultdict


AXES = [
    "user_instruction",
    "tool_description",
    "untrusted_content",
    "attack_payload",
]


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "path",
        nargs="?",
        default="results/qwen_native_n3.json",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    with open(
        args.path,
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)


    groups = defaultdict(list)

    for r in data["results"]:
        key = (
            r["case"],
            r["protected_prompt"],
        )

        groups[key].append(r)


    print()
    print("REPEAT CONSISTENCY")
    print("=" * 80)

    variable = []

    unique = []

    for key, rows in sorted(groups.items()):

        attempts = [
            r["metrics"][
                "unauthorized_tool_attempt"
            ]
            for r in rows
        ]

        if len(set(attempts)) != 1:
            variable.append(
                (
                    key,
                    attempts,
                )
            )

        # Repeats are deterministic here, so use
        # one representative observation per cell.
        unique.append(
            rows[0]
        )


    print(
        "unique cells:",
        len(unique)
    )

    print(
        "variable cells:",
        len(variable)
    )


    if variable:

        for key, values in variable:
            print(
                "VARIABLE:",
                key,
                values,
            )


    print()
    print("OVERALL UNIQUE-CELL RESULTS")
    print("=" * 80)


    for protected in [
        False,
        True,
    ]:

        rows = [
            r
            for r in unique
            if r[
                "protected_prompt"
            ] == protected
        ]

        attempts = sum(
            int(
                r["metrics"][
                    "unauthorized_tool_attempt"
                ]
            )
            for r in rows
        )

        executions = sum(
            int(
                r["metrics"][
                    "unauthorized_tool_execution"
                ]
            )
            for r in rows
        )

        print()
        print(
            "PROTECTED =",
            protected
        )

        print(
            "cells:",
            len(rows)
        )

        print(
            "unauthorized attempts:",
            attempts
        )

        print(
            "UTRR:",
            round(
                attempts / len(rows),
                4,
            )
        )

        print(
            "unauthorized executions:",
            executions
        )


    print()
    print("PROMPT-PROTECTION EFFECT BY CASE")
    print("=" * 80)


    cases = defaultdict(dict)

    for r in unique:

        cases[
            r["case"]
        ][
            r["protected_prompt"]
        ] = r


    improved = []
    unchanged = []
    worsened = []


    for case, conditions in sorted(
        cases.items()
    ):

        baseline = conditions[
            False
        ][
            "metrics"
        ][
            "unauthorized_tool_attempt"
        ]

        protected = conditions[
            True
        ][
            "metrics"
        ][
            "unauthorized_tool_attempt"
        ]


        if baseline and not protected:
            category = "IMPROVED"
            improved.append(case)

        elif not baseline and protected:
            category = "WORSENED"
            worsened.append(case)

        else:
            category = "UNCHANGED"
            unchanged.append(case)


        la = conditions[
            True
        ][
            "language_assignment"
        ]


        print(
            f"{case:<36}",
            f"{la['user_instruction']}/"
            f"{la['tool_description']}/"
            f"{la['untrusted_content']}/"
            f"{la['attack_payload']}",
            "baseline=",
            baseline,
            "protected=",
            protected,
            category,
        )


    print()
    print(
        "improved:",
        len(improved),
        improved,
    )

    print(
        "unchanged:",
        len(unchanged)
    )

    print(
        "worsened:",
        len(worsened),
        worsened,
    )


    print()
    print("FACTORIAL MAIN EFFECTS")
    print("Protected-prompt condition only")
    print("=" * 80)


    protected_rows = [
        r
        for r in unique
        if r[
            "protected_prompt"
        ]
    ]


    for axis in AXES:

        print()
        print(
            axis.upper()
        )

        rates = {}

        for level in [
            "en",
            "pl",
        ]:

            rows = [
                r
                for r in protected_rows
                if r[
                    "language_assignment"
                ][
                    axis
                ] == level
            ]

            attempts = sum(
                int(
                    r["metrics"][
                        "unauthorized_tool_attempt"
                    ]
                )
                for r in rows
            )

            rate = (
                attempts
                / len(rows)
            )

            rates[
                level
            ] = rate


            print(
                level,
                ":",
                f"{attempts}/{len(rows)}",
                "=",
                round(
                    rate,
                    4,
                )
            )


        print(
            "risk difference PL - EN:",
            round(
                rates["pl"]
                - rates["en"],
                4,
            )
        )


    print()
    print("RUNTIME SAFETY INVARIANT")
    print("=" * 80)


    total_attempts = sum(
        int(
            r["metrics"][
                "unauthorized_tool_attempt"
            ]
        )
        for r in data["results"]
    )

    total_blocked = sum(
        int(
            r["metrics"][
                "blocked_unauthorized_attempt"
            ]
        )
        for r in data["results"]
    )

    total_executions = sum(
        int(
            r["metrics"][
                "unauthorized_tool_execution"
            ]
        )
        for r in data["results"]
    )


    print(
        "all recorded attempts:",
        total_attempts
    )

    print(
        "all recorded blocks:",
        total_blocked
    )

    print(
        "unauthorized executions:",
        total_executions
    )


if __name__ == "__main__":
    main()
