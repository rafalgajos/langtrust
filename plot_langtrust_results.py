#!/usr/bin/env python3

import csv
from pathlib import Path

import matplotlib.pyplot as plt


INDIR = Path("analysis_outputs")
OUTDIR = INDIR / "figures"

OUTDIR.mkdir(parents=True, exist_ok=True)


def read_csv(name):
    path = INDIR / name
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(fig, stem):
    fig.tight_layout()
    fig.savefig(
        OUTDIR / f"{stem}.pdf",
        bbox_inches="tight",
    )
    fig.savefig(
        OUTDIR / f"{stem}.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)


def pct(x):
    return 100.0 * float(x)


# ============================================================
# FIGURE 1
# Attack UTRR: baseline vs protected by domain
# ============================================================

rows = read_csv(
    "main_domain_condition_summary.csv"
)

attack = [
    r for r in rows
    if r["condition"] == "attack"
]

domains = [
    "calendar",
    "files",
    "invoice",
]

baseline = []
protected = []

for domain in domains:

    b = next(
        r for r in attack
        if (
            r["domain"] == domain
            and r["protected"] == "False"
        )
    )

    p = next(
        r for r in attack
        if (
            r["domain"] == domain
            and r["protected"] == "True"
        )
    )

    baseline.append(
        pct(b["UTRR"])
    )

    protected.append(
        pct(p["UTRR"])
    )


fig, ax = plt.subplots(
    figsize=(7.2, 4.8)
)

x = list(range(len(domains)))
width = 0.36

bars_b = ax.bar(
    [v - width / 2 for v in x],
    baseline,
    width=width,
    label="Baseline",
)

bars_p = ax.bar(
    [v + width / 2 for v in x],
    protected,
    width=width,
    label="Protected prompt",
)

ax.set_xticks(
    x,
    [d.capitalize() for d in domains],
)

ax.set_ylabel(
    "Unauthorized Tool Request Rate (%)"
)

ax.set_ylim(0, 108)

ax.set_title(
    "Attack susceptibility by domain"
)

ax.legend(
    frameon=False
)

ax.spines[
    ["top", "right"]
].set_visible(False)

for bars in [
    bars_b,
    bars_p,
]:
    for bar in bars:
        value = bar.get_height()
        ax.text(
            bar.get_x()
            + bar.get_width() / 2,
            value + 2,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9,
        )

save(
    fig,
    "fig1_attack_utrr_by_domain",
)


# ============================================================
# FIGURE 2
# Paired protection effect with seed-level CI
# ============================================================

rows = read_csv(
    "protection_effect_summary.csv"
)

lookup = {
    r["domain"]: r
    for r in rows
}

means = [
    pct(
        lookup[d][
            "mean_RD_baseline_minus_protected"
        ]
    )
    for d in domains
]

lower = [
    pct(
        lookup[d]["CI95_low"]
    )
    for d in domains
]

upper = [
    pct(
        lookup[d]["CI95_high"]
    )
    for d in domains
]

xerr_low = [
    m - lo
    for m, lo
    in zip(means, lower)
]

xerr_high = [
    hi - m
    for m, hi
    in zip(means, upper)
]


fig, ax = plt.subplots(
    figsize=(7.2, 4.5)
)

y = list(range(len(domains)))

ax.errorbar(
    means,
    y,
    xerr=[
        xerr_low,
        xerr_high,
    ],
    fmt="o",
    capsize=5,
)

ax.axvline(
    0,
    linewidth=1,
    linestyle="--",
)

ax.set_yticks(
    y,
    [d.capitalize() for d in domains],
)

ax.set_xlabel(
    "Reduction in UTRR: baseline − protected (percentage points)"
)

ax.set_title(
    "Paired protection effect (T=0.2, 5 seeds)"
)

ax.spines[
    ["top", "right"]
].set_visible(False)

for yi, m, lo, hi in zip(
    y,
    means,
    lower,
    upper,
):
    ax.text(
        hi + 1.5,
        yi,
        f"{m:.1f} pp\n[{lo:.1f}, {hi:.1f}]",
        va="center",
        fontsize=9,
    )

ax.set_xlim(
    min(0, min(lower) - 5),
    max(upper) + 16,
)

save(
    fig,
    "fig2_protection_effect",
)


# ============================================================
# FIGURE 3
# Protected Invoice language contrasts N=25
# ============================================================

rows = read_csv(
    "invoice_protected_n25_language_contrasts.csv"
)

factor_order = [
    "user_instruction",
    "tool_description",
    "untrusted_content",
    "attack_payload",
]

factor_labels = {
    "user_instruction":
        "User instruction",
    "tool_description":
        "Tool description",
    "untrusted_content":
        "Untrusted content",
    "attack_payload":
        "Attack payload",
}

lookup = {
    r["factor"]: r
    for r in rows
}

means = [
    pct(
        lookup[f][
            "mean_seed_RD_PL_minus_EN"
        ]
    )
    for f in factor_order
]

lower = [
    pct(
        lookup[f]["CI95_low"]
    )
    for f in factor_order
]

upper = [
    pct(
        lookup[f]["CI95_high"]
    )
    for f in factor_order
]

xerr_low = [
    m - lo
    for m, lo
    in zip(means, lower)
]

xerr_high = [
    hi - m
    for m, hi
    in zip(means, upper)
]


fig, ax = plt.subplots(
    figsize=(7.6, 5.0)
)

y = list(range(
    len(factor_order)
))

ax.errorbar(
    means,
    y,
    xerr=[
        xerr_low,
        xerr_high,
    ],
    fmt="o",
    capsize=5,
)

ax.axvline(
    0,
    linewidth=1,
    linestyle="--",
)

ax.set_yticks(
    y,
    [
        factor_labels[f]
        for f in factor_order
    ],
)

ax.set_xlabel(
    "UTRR risk difference: PL − EN (percentage points)"
)

ax.set_title(
    "Language-factor contrasts in protected Invoice (25 seeds)"
)

ax.spines[
    ["top", "right"]
].set_visible(False)

ax.invert_yaxis()

for yi, m, lo, hi in zip(
    y,
    means,
    lower,
    upper,
):
    ax.text(
        max(hi, m) + 1.2,
        yi,
        f"{m:+.1f} pp",
        va="center",
        fontsize=9,
    )

ax.set_xlim(
    min(lower) - 5,
    max(upper) + 10,
)

save(
    fig,
    "fig3_invoice_language_contrasts",
)


# ============================================================
# FIGURE 4
# Protected Invoice cell-level UTRR N=25
# ============================================================

rows = read_csv(
    "invoice_protected_n25_cells.csv"
)

rows = sorted(
    rows,
    key=lambda r: int(
        r["cell_index"]
    ),
)

labels = [
    f"Cell {int(r['cell_index'])}"
    for r in rows
]

rates = [
    pct(r["UTRR"])
    for r in rows
]

lower = [
    pct(r["Wilson95_low"])
    for r in rows
]

upper = [
    pct(r["Wilson95_high"])
    for r in rows
]

xerr_low = [
    r - lo
    for r, lo
    in zip(rates, lower)
]

xerr_high = [
    hi - r
    for r, hi
    in zip(rates, upper)
]


fig, ax = plt.subplots(
    figsize=(8.0, 7.5)
)

y = list(range(
    len(rows)
))

ax.errorbar(
    rates,
    y,
    xerr=[
        xerr_low,
        xerr_high,
    ],
    fmt="o",
    capsize=3,
)

ax.set_yticks(
    y,
    labels,
)

ax.set_xlim(
    0,
    105,
)

ax.set_xlabel(
    "Unauthorized Tool Request Rate (%)"
)

ax.set_title(
    "Protected Invoice susceptibility by factorial cell (25 seeds/cell)"
)

ax.spines[
    ["top", "right"]
].set_visible(False)

ax.invert_yaxis()

for yi, value, r in zip(
    y,
    rates,
    rows,
):
    k = int(
        r["vulnerable_episodes"]
    )
    n = int(
        r["n"]
    )

    text_x = min(
        value + 2,
        92,
    )

    ax.text(
        text_x,
        yi,
        f"{k}/{n}",
        va="center",
        fontsize=8,
    )

save(
    fig,
    "fig4_invoice_cells_n25",
)


# ============================================================
# FIGURE 5
# Benign consequential-action fidelity
# ============================================================

rows = read_csv(
    "benign_fidelity.csv"
)

groups = []

for domain in domains:
    for protected_flag in [
        "False",
        "True",
    ]:

        r = next(
            row for row in rows
            if (
                row["domain"] == domain
                and
                row["protected"]
                == protected_flag
            )
        )

        groups.append(
            (
                domain,
                protected_flag,
                r,
            )
        )


required = [
    pct(
        r[
            "required_tool_execution_rate"
        ]
    )
    for _, _, r in groups
]

correct = [
    pct(
        r[
            "consequential_action_correct_rate"
        ]
    )
    for _, _, r in groups
]

task = [
    pct(
        r["TSR"]
    )
    for _, _, r in groups
]


labels = []

for domain, protected_flag, _ in groups:

    condition = (
        "P"
        if protected_flag == "True"
        else "B"
    )

    labels.append(
        f"{domain.capitalize()}\n{condition}"
    )


fig, ax = plt.subplots(
    figsize=(9.0, 5.0)
)

x = list(range(
    len(groups)
))

width = 0.25

ax.bar(
    [
        v - width
        for v in x
    ],
    required,
    width=width,
    label="Required tool executed",
)

ax.bar(
    x,
    correct,
    width=width,
    label="Consequential action correct",
)

ax.bar(
    [
        v + width
        for v in x
    ],
    task,
    width=width,
    label="Task success",
)

ax.set_xticks(
    x,
    labels,
)

ax.set_ylim(
    0,
    108,
)

ax.set_ylabel(
    "Rate among inference-valid benign episodes (%)"
)

ax.set_title(
    "Benign utility and consequential-action fidelity"
)

ax.legend(
    frameon=False,
    ncol=3,
    loc="upper center",
)

ax.spines[
    ["top", "right"]
].set_visible(False)

# Zero-height bars are otherwise visually indistinguishable
# from missing values. Label them explicitly.
for i, value in enumerate(correct):
    if value == 0:
        ax.text(
            i,
            1.5,
            "0%",
            ha="center",
            va="bottom",
            fontsize=8,
        )

for i, value in enumerate(task):
    if value == 0:
        ax.text(
            i + width,
            1.5,
            "0%",
            ha="center",
            va="bottom",
            fontsize=8,
        )

ax.text(
    0.01,
    -0.18,
    "B = baseline, P = protected prompt",
    transform=ax.transAxes,
    fontsize=9,
)

save(
    fig,
    "fig5_benign_fidelity",
)


print("=" * 80)
print("FIGURES GENERATED")
print("=" * 80)

for path in sorted(
    OUTDIR.iterdir()
):
    print(path)
