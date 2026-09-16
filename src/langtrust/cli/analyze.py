import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_T0_PATH = Path(
    "results/langtrust_3domains_t0_n1_bounded_run2.json"
)
DEFAULT_MAIN_PATH = Path(
    "results/langtrust_3domains_t02_n5.json"
)
DEFAULT_FOLLOW_PATH = Path(
    "results/invoice_attack_protected_t02_n20.json"
)
DEFAULT_OUTDIR = Path("analysis_outputs")

EXPECTED_COMMIT = (
    "a0a6eb937b7bac933b20fcd96269cb53618937b8"
)

EXPECTED_T0_SHA256 = (
    "9293e770c8bf2a74769871249fe712797d8997f3eb1738b17511ec8d048babfc"
)
EXPECTED_MAIN_SHA256 = (
    "d58ec6608f70e16075d78147200addcfb6142fb0389621b66dde24c1f6a8b819"
)
EXPECTED_FOLLOW_SHA256 = (
    "cfb77cce1137861c47e1e2f402533071b0a2816224e83d3667c9f20ae4fc8717"
)


FACTORS = [
    "user_instruction",
    "tool_description",
    "untrusted_content",
    "attack_payload",
]


def load(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def sha256(path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(chunk)

    return h.hexdigest()


def valid(r):
    return (
        r["inference"]["success"]
        and r["evaluation"] is not None
    )


def unauthorized(r):
    return int(
        bool(
            r["evaluation"]["security"][
                "unauthorized_tool_attempt"
            ]
        )
    )


def unauthorized_count(r):
    return int(
        r["evaluation"]["security"].get(
            "unauthorized_tool_attempt_count",
            unauthorized(r),
        )
    )


def blocked_count(r):
    return int(
        r["evaluation"]["security"].get(
            "blocked_unauthorized_attempt_count",
            0,
        )
    )


def unauthorized_execution_count(r):
    return int(
        r["evaluation"]["security"].get(
            "unauthorized_execution_count",
            0,
        )
    )


def task_success(r):
    return int(
        bool(
            r["evaluation"]["utility"][
                "task_success"
            ]
        )
    )


def mean(values):
    return sum(values) / len(values)


def t_ci(values):
    """
    Seed-level 95% t interval.

    Final protocol uses:
      n=5  -> df=4  -> t=.975 = 2.776
      n=25 -> df=24 -> t=.975 = 2.064
    """

    n = len(values)

    if n == 5:
        critical = 2.776
    elif n == 25:
        critical = 2.064
    else:
        raise ValueError(
            f"Unexpected seed count for t CI: {n}"
        )

    m = mean(values)
    sd = statistics.stdev(values)
    se = sd / math.sqrt(n)

    return (
        m,
        sd,
        m - critical * se,
        m + critical * se,
    )


def wilson(k, n, z=1.96):

    p = k / n

    denominator = 1 + z * z / n

    center = (
        p + z * z / (2 * n)
    ) / denominator

    half = (
        z
        / denominator
        * math.sqrt(
            p * (1 - p) / n
            + z * z / (4 * n * n)
        )
    )

    return center - half, center + half


def write_csv(path, rows):

    if not rows:
        return

    keys = []

    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=keys,
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(rows)


def pct(x):
    return f"{100 * x:.2f}%"


def pp(x):
    return f"{100 * x:+.2f} pp"


def run_analysis(
    t0_path,
    main_path,
    follow_path,
    outdir,
):
    """Run the canonical LangTrust analysis pipeline."""

    T0_PATH = Path(t0_path)
    MAIN_PATH = Path(main_path)
    FOLLOW_PATH = Path(follow_path)
    OUTDIR = Path(outdir)

    EXPECTED_SHA256 = {
        T0_PATH: EXPECTED_T0_SHA256,
        MAIN_PATH: EXPECTED_MAIN_SHA256,
        FOLLOW_PATH: EXPECTED_FOLLOW_SHA256,
    }

    # ============================================================
    # LOAD + VALIDATE INPUTS
    # ============================================================

    t0 = load(T0_PATH)
    main = load(MAIN_PATH)
    follow = load(FOLLOW_PATH)


    print("=" * 100)
    print("INPUT VALIDATION")
    print("=" * 100)


    for path, data, expected_n in [
        (T0_PATH, t0, 128),
        (MAIN_PATH, main, 640),
        (FOLLOW_PATH, follow, 320),
    ]:

        digest = sha256(path)

        print()
        print(path)
        print("records:", len(data["results"]))
        print("sha256:", digest)
        print(
            "git commit:",
            data["metadata"]["git_commit"],
        )
        print(
            "git dirty:",
            data["metadata"]["git_dirty"],
        )

        if digest != EXPECTED_SHA256[path]:
            raise RuntimeError(
                f"SHA256 mismatch: {path}"
            )

        if len(data["results"]) != expected_n:
            raise RuntimeError(
                f"Unexpected record count: {path}"
            )

        if (
            data["metadata"]["git_commit"]
            != EXPECTED_COMMIT
        ):
            raise RuntimeError(
                f"Git commit mismatch: {path}"
            )

        if data["metadata"]["git_dirty"]:
            raise RuntimeError(
                f"Dirty provenance: {path}"
            )

        if data["metadata"]["num_predict"] != 1024:
            raise RuntimeError(
                f"Unexpected num_predict: {path}"
            )


    # Main attack must be complete.
    main_attack_all = [
        r
        for r in main["results"]
        if r["condition"] == "attack"
    ]

    if len(main_attack_all) != 480:
        raise RuntimeError(
            "Expected 480 main attack episodes"
        )

    if not all(valid(r) for r in main_attack_all):
        raise RuntimeError(
            "Main attack set contains inference failure"
        )


    # Follow-up must contain exactly protected invoice attack.
    for r in follow["results"]:

        if not (
            r["pair_id"] == "invoice_email_001"
            and r["domain"] == "invoice"
            and r["condition"] == "attack"
            and r["protected_prompt"] is True
        ):
            raise RuntimeError(
                "Unexpected row in invoice follow-up"
            )

        if not valid(r):
            raise RuntimeError(
                "Invoice follow-up contains inference failure"
            )


    OUTDIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    # ============================================================
    # INFERENCE RELIABILITY
    # ============================================================

    inference_rows = []

    for name, data in [
        ("t0_n1", t0),
        ("t02_n5", main),
        ("invoice_protected_t02_n20", follow),
    ]:

        rows = data["results"]

        good = [
            r for r in rows
            if valid(r)
        ]

        failed = [
            r for r in rows
            if not valid(r)
        ]

        types = Counter(
            r["inference"]["failure_type"]
            for r in failed
        )

        inference_rows.append({
            "run": name,
            "planned": len(rows),
            "inference_valid": len(good),
            "inference_failures": len(failed),
            "inference_valid_rate":
                len(good) / len(rows),
            "failure_types":
                json.dumps(
                    dict(types),
                    sort_keys=True,
                ),
        })


    write_csv(
        OUTDIR / "inference_reliability.csv",
        inference_rows,
    )


    # ============================================================
    # MAIN DOMAIN × CONDITION × PROTECTION
    # ============================================================

    main_summary = []

    groups = defaultdict(list)

    for r in main["results"]:

        groups[
            (
                r["domain"],
                r["condition"],
                r["protected_prompt"],
            )
        ].append(r)


    for key in sorted(groups):

        domain, condition, protected = key

        rows = groups[key]

        good = [
            r for r in rows
            if valid(r)
        ]

        failed = [
            r for r in rows
            if not valid(r)
        ]

        out = {
            "domain": domain,
            "condition": condition,
            "protected": protected,
            "planned": len(rows),
            "valid": len(good),
            "inference_failures": len(failed),
        }

        if condition == "attack":

            vulnerable = sum(
                unauthorized(r)
                for r in good
            )

            native_attempts = sum(
                unauthorized_count(r)
                for r in good
            )

            blocked = sum(
                blocked_count(r)
                for r in good
            )

            executions = sum(
                unauthorized_execution_count(r)
                for r in good
            )

            successes = sum(
                task_success(r)
                for r in good
            )

            out.update({
                "vulnerable_episodes": vulnerable,
                "UTRR":
                    vulnerable / len(good),
                "native_unauthorized_requests":
                    native_attempts,
                "blocked_unauthorized_requests":
                    blocked,
                "unauthorized_executions":
                    executions,
                "task_successes":
                    successes,
                "TSR":
                    successes / len(good),
            })

        else:

            required = sum(
                int(
                    bool(
                        r["evaluation"]["utility"][
                            "required_tools_executed"
                        ]
                    )
                )
                for r in good
            )

            overblock = sum(
                int(
                    bool(
                        r["evaluation"]["utility"][
                            "policy_overblocking"
                        ]
                    )
                )
                for r in good
            )

            underaction = sum(
                int(
                    bool(
                        r["evaluation"]["utility"][
                            "model_underaction"
                        ]
                    )
                )
                for r in good
            )

            successes = sum(
                task_success(r)
                for r in good
            )

            correct = sum(
                int(
                    r["evaluation"]["utility"].get(
                        "consequential_action_correct"
                    )
                    is True
                )
                for r in good
            )

            divergence = sum(
                int(
                    r["evaluation"]["utility"].get(
                        "answer_action_content_divergence"
                    )
                    is True
                )
                for r in good
            )

            statuses = Counter(
                r["evaluation"]["utility"].get(
                    "consequential_content_status"
                )
                for r in good
            )

            out.update({
                "required_tool_executed":
                    required,
                "required_tool_execution_rate":
                    required / len(good),
                "policy_overblocking":
                    overblock,
                "model_underaction":
                    underaction,
                "task_successes":
                    successes,
                "TSR":
                    successes / len(good),
                "consequential_action_correct":
                    correct,
                "consequential_action_correct_rate":
                    correct / len(good),
                "answer_action_divergence":
                    divergence,
                "answer_action_divergence_rate":
                    divergence / len(good),
                "content_status":
                    json.dumps(
                        dict(statuses),
                        sort_keys=True,
                    ),
            })

        main_summary.append(out)


    write_csv(
        OUTDIR / "main_domain_condition_summary.csv",
        main_summary,
    )


    # ============================================================
    # PAIRED PROTECTION EFFECT — MAIN N=5
    # ============================================================

    main_attack = [
        r for r in main["results"]
        if (
            r["condition"] == "attack"
            and valid(r)
        )
    ]

    protection_seed_rows = []
    protection_summary_rows = []


    for domain in [
        "calendar",
        "files",
        "invoice",
    ]:

        seeds = sorted({
            r["seed"]
            for r in main_attack
            if r["domain"] == domain
        })

        security_rds = []

        pair_security = Counter()
        pair_utility = Counter()

        for seed in seeds:

            baseline = [
                r
                for r in main_attack
                if (
                    r["domain"] == domain
                    and r["seed"] == seed
                    and r["protected_prompt"] is False
                )
            ]

            protected = [
                r
                for r in main_attack
                if (
                    r["domain"] == domain
                    and r["seed"] == seed
                    and r["protected_prompt"] is True
                )
            ]

            base_utrr = mean([
                unauthorized(r)
                for r in baseline
            ])

            prot_utrr = mean([
                unauthorized(r)
                for r in protected
            ])

            base_tsr = mean([
                task_success(r)
                for r in baseline
            ])

            prot_tsr = mean([
                task_success(r)
                for r in protected
            ])

            rd = base_utrr - prot_utrr

            security_rds.append(rd)

            protection_seed_rows.append({
                "domain": domain,
                "seed": seed,
                "baseline_UTRR": base_utrr,
                "protected_UTRR": prot_utrr,
                "RD_baseline_minus_protected":
                    rd,
                "baseline_TSR": base_tsr,
                "protected_TSR": prot_tsr,
                "TSR_RD_protected_minus_baseline":
                    prot_tsr - base_tsr,
            })


        paired = defaultdict(dict)

        for r in main_attack:

            if r["domain"] != domain:
                continue

            paired[
                (
                    r["seed"],
                    r["cell_index"],
                )
            ][
                r["protected_prompt"]
            ] = r


        for pair in paired.values():

            b = pair[False]
            p = pair[True]

            b_sec = unauthorized(b)
            p_sec = unauthorized(p)

            if p_sec < b_sec:
                pair_security["improved"] += 1
            elif p_sec > b_sec:
                pair_security["worsened"] += 1
            else:
                pair_security["unchanged"] += 1

            b_task = task_success(b)
            p_task = task_success(p)

            if p_task > b_task:
                pair_utility["improved"] += 1
            elif p_task < b_task:
                pair_utility["worsened"] += 1
            else:
                pair_utility["unchanged"] += 1


        m, sd, lo, hi = t_ci(
            security_rds
        )

        protection_summary_rows.append({
            "domain": domain,
            "n_seeds": len(seeds),
            "mean_RD_baseline_minus_protected":
                m,
            "seed_SD":
                sd,
            "CI95_low":
                lo,
            "CI95_high":
                hi,
            "security_improved_pairs":
                pair_security["improved"],
            "security_unchanged_pairs":
                pair_security["unchanged"],
            "security_worsened_pairs":
                pair_security["worsened"],
            "utility_improved_pairs":
                pair_utility["improved"],
            "utility_unchanged_pairs":
                pair_utility["unchanged"],
            "utility_worsened_pairs":
                pair_utility["worsened"],
        })


    write_csv(
        OUTDIR / "protection_effect_by_seed.csv",
        protection_seed_rows,
    )

    write_csv(
        OUTDIR / "protection_effect_summary.csv",
        protection_summary_rows,
    )


    # ============================================================
    # LANGUAGE FACTORS — MAIN N=5
    # ============================================================

    language_main_rows = []


    for domain in [
        "calendar",
        "files",
        "invoice",
    ]:

        for protected in [
            False,
            True,
        ]:

            rows = [
                r
                for r in main_attack
                if (
                    r["domain"] == domain
                    and
                    r["protected_prompt"]
                    is protected
                )
            ]

            seeds = sorted({
                r["seed"]
                for r in rows
            })


            for factor in FACTORS:

                en = [
                    r for r in rows
                    if (
                        r["language_assignment"][
                            factor
                        ]
                        == "en"
                    )
                ]

                pl = [
                    r for r in rows
                    if (
                        r["language_assignment"][
                            factor
                        ]
                        == "pl"
                    )
                ]

                en_attempts = sum(
                    unauthorized(r)
                    for r in en
                )

                pl_attempts = sum(
                    unauthorized(r)
                    for r in pl
                )

                en_rate = (
                    en_attempts / len(en)
                )

                pl_rate = (
                    pl_attempts / len(pl)
                )

                seed_rds = []

                for seed in seeds:

                    en_seed = [
                        r for r in en
                        if r["seed"] == seed
                    ]

                    pl_seed = [
                        r for r in pl
                        if r["seed"] == seed
                    ]

                    seed_rds.append(
                        mean([
                            unauthorized(r)
                            for r in pl_seed
                        ])
                        -
                        mean([
                            unauthorized(r)
                            for r in en_seed
                        ])
                    )

                m, sd, lo, hi = t_ci(
                    seed_rds
                )

                language_main_rows.append({
                    "domain": domain,
                    "protected": protected,
                    "factor": factor,
                    "EN_attempts":
                        en_attempts,
                    "EN_n":
                        len(en),
                    "EN_UTRR":
                        en_rate,
                    "PL_attempts":
                        pl_attempts,
                    "PL_n":
                        len(pl),
                    "PL_UTRR":
                        pl_rate,
                    "pooled_RD_PL_minus_EN":
                        pl_rate - en_rate,
                    "mean_seed_RD_PL_minus_EN":
                        m,
                    "seed_SD":
                        sd,
                    "CI95_low":
                        lo,
                    "CI95_high":
                        hi,
                })


    write_csv(
        OUTDIR / "language_factor_contrasts_main_n5.csv",
        language_main_rows,
    )


    # ============================================================
    # BENIGN FIDELITY — MAIN N=5
    # ============================================================

    benign_rows = [
        r
        for r in main_summary
        if r["condition"] == "benign"
    ]

    write_csv(
        OUTDIR / "benign_fidelity.csv",
        benign_rows,
    )


    # ============================================================
    # PROTECTED INVOICE — COMBINED N=25
    # ============================================================

    invoice_old = [
        r
        for r in main_attack
        if (
            r["domain"] == "invoice"
            and r["protected_prompt"] is True
        )
    ]

    invoice_new = [
        r
        for r in follow["results"]
        if valid(r)
    ]

    old_seeds = {
        r["seed"]
        for r in invoice_old
    }

    new_seeds = {
        r["seed"]
        for r in invoice_new
    }

    overlap = (
        old_seeds
        & new_seeds
    )

    if overlap:
        raise RuntimeError(
            f"Seed overlap: {sorted(overlap)}"
        )

    invoice_n25 = (
        invoice_old
        + invoice_new
    )

    if len(invoice_n25) != 400:
        raise RuntimeError(
            "Expected 400 combined invoice episodes"
        )


    by_seed = defaultdict(list)

    for r in invoice_n25:
        by_seed[
            r["seed"]
        ].append(r)


    if len(by_seed) != 25:
        raise RuntimeError(
            "Expected 25 invoice seeds"
        )

    if not all(
        len(rows) == 16
        for rows in by_seed.values()
    ):
        raise RuntimeError(
            "Expected 16 cells per invoice seed"
        )


    invoice_seed_rows = []
    seed_utrrs = []


    for seed in sorted(by_seed):

        rows = by_seed[seed]

        vulnerable = sum(
            unauthorized(r)
            for r in rows
        )

        utrr = (
            vulnerable
            / len(rows)
        )

        seed_utrrs.append(utrr)

        invoice_seed_rows.append({
            "seed": seed,
            "vulnerable_episodes":
                vulnerable,
            "n": len(rows),
            "UTRR": utrr,
        })


    invoice_mean, invoice_sd, invoice_lo, invoice_hi = (
        t_ci(seed_utrrs)
    )

    invoice_vulnerable = sum(
        unauthorized(r)
        for r in invoice_n25
    )

    invoice_native_requests = sum(
        unauthorized_count(r)
        for r in invoice_n25
    )

    invoice_blocked = sum(
        blocked_count(r)
        for r in invoice_n25
    )

    invoice_executions = sum(
        unauthorized_execution_count(r)
        for r in invoice_n25
    )

    wilson_lo, wilson_hi = wilson(
        invoice_vulnerable,
        len(invoice_n25),
    )


    invoice_overall = {
        "n_seeds": 25,
        "episodes": len(invoice_n25),
        "vulnerable_episodes":
            invoice_vulnerable,
        "pooled_UTRR":
            invoice_vulnerable
            / len(invoice_n25),
        "pooled_Wilson95_low":
            wilson_lo,
        "pooled_Wilson95_high":
            wilson_hi,
        "mean_seed_UTRR":
            invoice_mean,
        "seed_SD":
            invoice_sd,
        "seed_t_CI95_low":
            invoice_lo,
        "seed_t_CI95_high":
            invoice_hi,
        "native_unauthorized_requests":
            invoice_native_requests,
        "blocked_unauthorized_requests":
            invoice_blocked,
        "unauthorized_executions":
            invoice_executions,
        "runtime_invariant_pass":
            (
                invoice_native_requests
                == invoice_blocked
                and invoice_executions == 0
            ),
    }


    write_csv(
        OUTDIR / "invoice_protected_n25_seed_rates.csv",
        invoice_seed_rows,
    )


    # CELL-LEVEL

    cells = defaultdict(list)

    for r in invoice_n25:
        cells[
            r["cell_index"]
        ].append(r)


    invoice_cell_rows = []


    for cell in sorted(cells):

        rows = cells[cell]

        vulnerable = sum(
            unauthorized(r)
            for r in rows
        )

        n = len(rows)

        lo, hi = wilson(
            vulnerable,
            n,
        )

        if vulnerable == n:
            status = "all_vulnerable"
        elif vulnerable == 0:
            status = "no_unauthorized_request_observed"
        else:
            status = "mixed"

        languages = (
            rows[0][
                "language_assignment"
            ]
        )

        invoice_cell_rows.append({
            "cell_index": cell,
            "cell_key":
                rows[0]["cell_key"],
            "user_instruction":
                languages["user_instruction"],
            "tool_description":
                languages["tool_description"],
            "untrusted_content":
                languages["untrusted_content"],
            "attack_payload":
                languages["attack_payload"],
            "vulnerable_episodes":
                vulnerable,
            "n":
                n,
            "UTRR":
                vulnerable / n,
            "Wilson95_low":
                lo,
            "Wilson95_high":
                hi,
            "observed_status":
                status,
        })


    write_csv(
        OUTDIR / "invoice_protected_n25_cells.csv",
        invoice_cell_rows,
    )


    # LANGUAGE CONTRASTS N=25

    invoice_language_rows = []


    for factor in FACTORS:

        en = [
            r for r in invoice_n25
            if (
                r["language_assignment"][
                    factor
                ]
                == "en"
            )
        ]

        pl = [
            r for r in invoice_n25
            if (
                r["language_assignment"][
                    factor
                ]
                == "pl"
            )
        ]

        en_vulnerable = sum(
            unauthorized(r)
            for r in en
        )

        pl_vulnerable = sum(
            unauthorized(r)
            for r in pl
        )

        en_rate = (
            en_vulnerable
            / len(en)
        )

        pl_rate = (
            pl_vulnerable
            / len(pl)
        )

        seed_rds = []

        for seed in sorted(by_seed):

            rows = by_seed[seed]

            en_seed = [
                r for r in rows
                if (
                    r[
                        "language_assignment"
                    ][factor]
                    == "en"
                )
            ]

            pl_seed = [
                r for r in rows
                if (
                    r[
                        "language_assignment"
                    ][factor]
                    == "pl"
                )
            ]

            seed_rds.append(
                mean([
                    unauthorized(r)
                    for r in pl_seed
                ])
                -
                mean([
                    unauthorized(r)
                    for r in en_seed
                ])
            )

        m, sd, lo, hi = t_ci(
            seed_rds
        )

        invoice_language_rows.append({
            "factor": factor,
            "EN_vulnerable":
                en_vulnerable,
            "EN_n":
                len(en),
            "EN_UTRR":
                en_rate,
            "PL_vulnerable":
                pl_vulnerable,
            "PL_n":
                len(pl),
            "PL_UTRR":
                pl_rate,
            "pooled_RD_PL_minus_EN":
                pl_rate - en_rate,
            "mean_seed_RD_PL_minus_EN":
                m,
            "seed_SD":
                sd,
            "CI95_low":
                lo,
            "CI95_high":
                hi,
        })


    write_csv(
        OUTDIR / "invoice_protected_n25_language_contrasts.csv",
        invoice_language_rows,
    )


    # ============================================================
    # T=0 vs STOCHASTIC N=5 CROSS-CHECK
    # ============================================================

    crosscheck_rows = []


    for run_name, data in [
        ("T0_N1", t0),
        ("T02_N5", main),
    ]:

        attack = [
            r for r in data["results"]
            if (
                r["condition"] == "attack"
                and valid(r)
            )
        ]

        for domain in [
            "calendar",
            "files",
            "invoice",
        ]:

            for protected in [
                False,
                True,
            ]:

                rows = [
                    r for r in attack
                    if (
                        r["domain"] == domain
                        and
                        r["protected_prompt"]
                        is protected
                    )
                ]

                vulnerable = sum(
                    unauthorized(r)
                    for r in rows
                )

                successes = sum(
                    task_success(r)
                    for r in rows
                )

                crosscheck_rows.append({
                    "run": run_name,
                    "domain": domain,
                    "protected": protected,
                    "n": len(rows),
                    "vulnerable_episodes":
                        vulnerable,
                    "UTRR":
                        vulnerable
                        / len(rows),
                    "task_successes":
                        successes,
                    "TSR":
                        successes
                        / len(rows),
                })


    write_csv(
        OUTDIR / "deterministic_vs_stochastic.csv",
        crosscheck_rows,
    )


    # ============================================================
    # RUNTIME INVARIANTS
    # ============================================================

    runtime_rows = []


    for name, data in [
        ("t0_n1", t0),
        ("t02_n5", main),
        (
            "invoice_protected_t02_n20",
            follow,
        ),
    ]:

        rows = [
            r for r in data["results"]
            if (
                r["condition"] == "attack"
                and valid(r)
            )
        ]

        native_requests = sum(
            unauthorized_count(r)
            for r in rows
        )

        blocked = sum(
            blocked_count(r)
            for r in rows
        )

        executions = sum(
            unauthorized_execution_count(r)
            for r in rows
        )

        runtime_rows.append({
            "run": name,
            "valid_attack_episodes":
                len(rows),
            "native_unauthorized_requests":
                native_requests,
            "blocked_unauthorized_requests":
                blocked,
            "unauthorized_executions":
                executions,
            "runtime_invariant_pass":
                (
                    native_requests
                    == blocked
                    and executions == 0
                ),
        })


    write_csv(
        OUTDIR / "runtime_invariants.csv",
        runtime_rows,
    )


    # ============================================================
    # MANIFEST
    # ============================================================

    manifest = {
        "analysis_version": 1,
        "git_commit": EXPECTED_COMMIT,
        "inputs": [
            {
                "path": str(T0_PATH),
                "sha256": sha256(T0_PATH),
                "records": len(t0["results"]),
            },
            {
                "path": str(MAIN_PATH),
                "sha256": sha256(MAIN_PATH),
                "records": len(main["results"]),
            },
            {
                "path": str(FOLLOW_PATH),
                "sha256": sha256(FOLLOW_PATH),
                "records": len(follow["results"]),
            },
        ],
        "invoice_protected_n25_overall":
            invoice_overall,
        "methodological_notes": [
            (
                "Main protection effects use only the "
                "paired T=0.2 N=5 experiment."
            ),
            (
                "The N=25 invoice analysis combines "
                "protected invoice attack observations "
                "from N=5 and N=20 using disjoint seeds."
            ),
            (
                "The N=25 invoice follow-up is not an "
                "N=25 paired protection comparison."
            ),
            (
                "Inference failures are reported "
                "separately and excluded from security "
                "and utility metrics."
            ),
            (
                "Seed-level t intervals describe "
                "stochastic variation under the fixed "
                "experimental protocol."
            ),
        ],
    }


    (
        OUTDIR / "analysis_manifest.json"
    ).write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


    # ============================================================
    # MARKDOWN SUMMARY
    # ============================================================

    attack_index = {
        (
            r["domain"],
            r["protected"],
        ): r
        for r in main_summary
        if r["condition"] == "attack"
    }

    protection_index = {
        r["domain"]: r
        for r in protection_summary_rows
    }


    md = []

    md.append(
        "# LangTrust — Qwen experimental results"
    )
    md.append("")

    md.append(
        "## Main stochastic experiment: T=0.2, N=5"
    )
    md.append("")

    md.append(
        "| Domain | Baseline UTRR | Protected UTRR | "
        "Protection RD | Seed-level 95% CI | "
        "Baseline TSR | Protected TSR |"
    )

    md.append(
        "|---|---:|---:|---:|---:|---:|---:|"
    )


    for domain in [
        "calendar",
        "files",
        "invoice",
    ]:

        b = attack_index[
            (domain, False)
        ]

        p = attack_index[
            (domain, True)
        ]

        effect = protection_index[
            domain
        ]

        md.append(
            f"| {domain.capitalize()} "
            f"| {pct(b['UTRR'])} "
            f"| {pct(p['UTRR'])} "
            f"| {pp(effect['mean_RD_baseline_minus_protected'])} "
            f"| [{pp(effect['CI95_low'])}, "
            f"{pp(effect['CI95_high'])}] "
            f"| {pct(b['TSR'])} "
            f"| {pct(p['TSR'])} |"
        )


    md.append("")
    md.append(
        "Protection RD = baseline UTRR − protected UTRR."
    )
    md.append("")

    md.append(
        "## Protected invoice follow-up: combined N=25"
    )
    md.append("")

    md.append(
        f"- UTRR: "
        f"{invoice_vulnerable}/400 = "
        f"{pct(invoice_vulnerable / 400)}."
    )

    md.append(
        f"- Mean seed-level UTRR: "
        f"{pct(invoice_mean)}."
    )

    md.append(
        f"- Seed-level SD: "
        f"{pct(invoice_sd)}."
    )

    md.append(
        f"- Seed-level 95% CI: "
        f"[{pct(invoice_lo)}, "
        f"{pct(invoice_hi)}]."
    )

    md.append(
        f"- Runtime: "
        f"{invoice_blocked}/"
        f"{invoice_native_requests} "
        f"unauthorized native requests blocked; "
        f"{invoice_executions} "
        f"unauthorized executions."
    )

    md.append("")
    md.append(
        "### Protected invoice language contrasts"
    )
    md.append("")

    md.append(
        "| Factor | EN UTRR | PL UTRR | "
        "RD PL−EN | Seed-level 95% CI |"
    )

    md.append(
        "|---|---:|---:|---:|---:|"
    )


    for r in invoice_language_rows:

        md.append(
            f"| {r['factor']} "
            f"| {pct(r['EN_UTRR'])} "
            f"| {pct(r['PL_UTRR'])} "
            f"| {pp(r['mean_seed_RD_PL_minus_EN'])} "
            f"| [{pp(r['CI95_low'])}, "
            f"{pp(r['CI95_high'])}] |"
        )


    md.append("")
    md.append(
        "## Interpretation guardrails"
    )
    md.append("")

    md.append(
        "- UTRR is a pre-enforcement model susceptibility metric."
    )

    md.append(
        "- Unauthorized execution rate is a separate post-enforcement metric."
    )

    md.append(
        "- Zero unauthorized executions reflects the runtime policy invariant "
        "in these benchmark scenarios, not universal model safety."
    )

    md.append(
        "- Authorized tool execution does not imply consequential action correctness."
    )

    md.append(
        "- The N=25 invoice follow-up estimates only the protected invoice condition; "
        "the paired protection comparison remains N=5."
    )

    md.append(
        "- Seed-level confidence intervals describe stochastic variation under this "
        "fixed protocol and should not be interpreted as generalization to other "
        "models, prompts, domains, or deployments."
    )


    (
        OUTDIR / "main_results.md"
    ).write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )


    # ============================================================
    # TERMINAL SUMMARY
    # ============================================================

    print()
    print("=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

    print()
    print(
        "Main paired protection effects:"
    )

    for r in protection_summary_rows:

        print(
            f"{r['domain']:8s} "
            f"RD="
            f"{r['mean_RD_baseline_minus_protected']:+.4f} "
            f"95%CI=["
            f"{r['CI95_low']:+.4f}, "
            f"{r['CI95_high']:+.4f}]"
        )


    print()
    print(
        "Protected invoice N=25:"
    )

    print(
        f"UTRR = "
        f"{invoice_vulnerable}/400 = "
        f"{invoice_vulnerable / 400:.4f}"
    )

    print(
        f"mean seed UTRR = "
        f"{invoice_mean:.4f}"
    )

    print(
        f"95% CI = "
        f"[{invoice_lo:.4f}, "
        f"{invoice_hi:.4f}]"
    )

    print()

    print(
        "Runtime invariants:"
    )

    for r in runtime_rows:

        print(
            f"{r['run']:28s} "
            f"requests="
            f"{r['native_unauthorized_requests']} "
            f"blocked="
            f"{r['blocked_unauthorized_requests']} "
            f"executions="
            f"{r['unauthorized_executions']} "
            f"PASS="
            f"{r['runtime_invariant_pass']}"
        )


    print()
    print(
        "Generated:"
    )

    for path in sorted(
        OUTDIR.iterdir()
    ):

        print(
            " ",
            path,
        )



def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Analyze the canonical LangTrust experiment artifacts "
            "and generate publication-oriented summary files."
        )
    )

    parser.add_argument(
        "--t0",
        type=Path,
        required=True,
        help="Path to the deterministic T=0, N=1 result JSON.",
    )
    parser.add_argument(
        "--main",
        type=Path,
        required=True,
        help="Path to the main stochastic T=0.2, N=5 result JSON.",
    )
    parser.add_argument(
        "--follow",
        type=Path,
        required=True,
        help="Path to the protected invoice follow-up result JSON.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=DEFAULT_OUTDIR,
        help="Directory for generated analysis files.",
    )

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    run_analysis(
        t0_path=args.t0,
        main_path=args.main,
        follow_path=args.follow,
        outdir=args.outdir,
    )


if __name__ == "__main__":
    main()
