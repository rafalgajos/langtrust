# Reproducing LangTrust

## Scope

This document describes how to reproduce LangTrust analysis from the
legacy Qwen result artifacts identified in `ARTIFACTS.md`, how to install and
exercise the current public software release, and how to attempt a fresh
experiment re-execution from the public historical experiment source snapshot.

It is a practical reproducibility guide, not a full methods paper. See also
`PROVENANCE.md`, `ARTIFACTS.md`, `SHA256SUMS`, and `CITATION.cff`.

## Evidence generations

This guide covers two distinct experiment generations.

The repository-root `SHA256SUMS`, `langtrust-analyze`, and existing
`analysis_outputs/` belong to the preserved **legacy Qwen study**.

The later **three-model validation study** uses the internal study identifier
`G9C13`; `G9C13` is not an acronym. It is frozen as a separate archive with its
own internal checksum manifest. Verifying that archive does not require
re-running all 1920 primary model episodes.

## Reproduction levels

### A. Legacy Qwen analysis reproduction

Install LangTrust, download the three legacy Qwen JSON result files, verify
SHA-256 digests, and regenerate the preserved legacy Qwen analysis outputs with
`langtrust-analyze`. This is the preserved legacy analysis workflow. It does **not**
require Ollama, GPU hardware, or model inference.

### B. Software / protocol reproduction

Install the current public LangTrust release (`v0.2.1`), inspect packaged
language/scenario resources, run the command-line interfaces (CLIs), and run
the test suite.

For software/protocol verification from a source checkout:

```bash
python -m pip install ".[dev]"
python -m pytest
```

The pytest configuration in `pyproject.toml` runs the repository `tests/` suite.

### C. Legacy Qwen experiment re-execution (advanced)

Check out the archival experiment source snapshot and attempt a fresh benchmark
run with a matching model/runtime configuration.

A new stochastic run is **not** expected to reproduce the legacy Qwen JSON
byte-for-byte. The legacy Qwen JSON bundle remains the scientific record of
the original execution.

## Requirements

Analysis reproduction needs Python >= 3.11 (release QA validated with
3.11.x), an installed LangTrust release, and the three legacy Qwen JSON
artifacts. Their exact SHA-256 digests are listed in `ARTIFACTS.md`; the complete
Zenodo results record also provides a record-level `SHA256SUMS.txt`.

Experiment re-execution additionally needs Ollama-compatible inference, model
`qwen2.5:14b` matching full digest
`7cdf5a0187d5c58cc5d369b255592f7841d1c4696d45a8c8a9489440385b22f6`, sufficient
GPU resources (original runs: 2 × NVIDIA Quadro RTX 6000, 24 GB VRAM each), and
the original protocol parameters. Identical hardware is **not** required for
analysis reproduction.

## Install LangTrust

From a checkout of the LangTrust release repository:

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install .
```

Windows:

```text
python -m venv .venv
.venv\Scripts\activate
python -m pip install .
```

If LangTrust is later published to a package index:

```bash
python -m pip install langtrust
```

Do not assume package-index publication until release metadata says so. Prefer
the installable CLIs (`langtrust-analyze`, `langtrust-benchmark`) over
source-tree imports or repository-root wrappers.

Optional smoke test without inference (any working directory after install):

```bash
langtrust-benchmark --dry-run --pair invoice_email_001 --condition attack --protected true --repeats 1
```

This exercises packaged resources and design construction only.

For desktop GUI Live Run, `v0.2.1` defaults to the user-writable
`~/LangTrust/results/langtrust_gui_live.json`. Live Run performs actual model
inference and writes result JSON to disk. Hard cancellation of an in-flight
model request is not available in this version; the request ends when it
completes or reaches the configured timeout.

## Obtain the legacy Qwen result artifacts

The legacy Qwen raw JSON files are **not** tracked in Git and are not
distributed via Git LFS. Download them from the public LangTrust
evaluation-artifacts record:

[`10.5281/zenodo.22817213`](https://doi.org/10.5281/zenodo.22817213)

In this document, **T** denotes sampling temperature and **N** denotes the
number of seed-based repeats contributing to the stated experiment or summary.

Required legacy files:

- `langtrust_3domains_t0_n1_bounded_run2.json` — T=0, N=1 descriptive map
  (128 records; 125 inference-valid; 3 `generation_limit`)
- `langtrust_3domains_t02_n5.json` — main T=0.2, N=5 experiment
  (640 records; 637 inference-valid; 3 `generation_limit`)
- `invoice_attack_protected_t02_n20.json` — protected invoice follow-up,
  T=0.2, N=20 (320 records; 320 inference-valid)

All three identify legacy experiment provenance
`a0a6eb937b7bac933b20fcd96269cb53618937b8`. Details: `ARTIFACTS.md`.

The complete Zenodo record also contains `SHA256SUMS.txt`, the frozen
three-model archive, `README_RESULTS.md`, and
`ZENODO_RESULTS_MANIFEST.json`.

## Verify legacy Qwen artifact integrity

Before analysis, verify the three legacy JSON files against the exact
SHA-256 digests in `ARTIFACTS.md`.

If the complete public results record
[`10.5281/zenodo.22817213`](https://doi.org/10.5281/zenodo.22817213) was
downloaded, verify its deposit-level checksum manifest.

Linux:

```bash
sha256sum -c SHA256SUMS.txt
```

macOS:

```bash
shasum -a 256 -c SHA256SUMS.txt
```

The repository-root file `SHA256SUMS` is a separate legacy-Qwen-only manifest
and may also be used when copied from a source checkout into the same directory
as the three legacy JSON files.

A matching digest is required before treating a downloaded result artifact as
verified.


Expected digests:

- `9293e770c8bf2a74769871249fe712797d8997f3eb1738b17511ec8d048babfc` —
  `langtrust_3domains_t0_n1_bounded_run2.json`
- `d58ec6608f70e16075d78147200addcfb6142fb0389621b66dde24c1f6a8b819` —
  `langtrust_3domains_t02_n5.json`
- `cfb77cce1137861c47e1e2f402533071b0a2816224e83d3667c9f20ae4fc8717` —
  `invoice_attack_protected_t02_n20.json`

A normal Git clone alone does not contain the raw JSON files.

## Reproduce the legacy Qwen analysis

```bash
ARTIFACT_DIR="/path/to/langtrust-results"
OUTPUT_DIR="/path/to/langtrust-analysis"

langtrust-analyze \
  --t0 "$ARTIFACT_DIR/langtrust_3domains_t0_n1_bounded_run2.json" \
  --main "$ARTIFACT_DIR/langtrust_3domains_t02_n5.json" \
  --follow "$ARTIFACT_DIR/invoice_attack_protected_t02_n20.json" \
  --outdir "$OUTPUT_DIR"
```

Regenerated legacy Qwen outputs include:

`analysis_manifest.json`, `benign_fidelity.csv`,
`deterministic_vs_stochastic.csv`, `inference_reliability.csv`,
`invoice_protected_n25_cells.csv`, `invoice_protected_n25_language_contrasts.csv`,
`invoice_protected_n25_seed_rates.csv`, `language_factor_contrasts_main_n5.csv`,
`main_domain_condition_summary.csv`, `main_results.md`,
`protection_effect_by_seed.csv`, `protection_effect_summary.csv`,
`runtime_invariants.csv`.

Legacy Qwen derived outputs are tracked under `analysis_outputs/` in the
release-preparation repository and are intended to be included in the public
software release. Analysis reproduction works from an external working
directory.

## Compare regenerated analysis outputs

1. Confirm the expected file names are present.
2. Compare non-manifest outputs byte-for-byte with the published legacy Qwen
   copies (`diff -q` or equivalent checksums).
3. Compare `analysis_manifest.json` semantically after normalizing
   path-specific fields (local input paths differ by machine).

A previously established golden analysis regression on the fixed legacy Qwen
inputs found 13 expected files matched, with 12 non-manifest outputs
byte-identical and `analysis_manifest.json` semantically identical after
input-path normalization. That checks analysis-pipeline stability for fixed
inputs. It does **not** show population generalization, T=0.2 model
determinism, byte-for-byte fresh stochastic regeneration, or universal
platform independence.

## Interpret inference-invalid episodes

An **inference-valid** episode completes model inference under the configured
protocol and is eligible for behavioral endpoint analysis. Episodes that reach
`done_reason = "length"` at `num_predict = 1024` are inference-invalid /
censored. They are not ordinary failed task outcomes and were not replaced by a
favorable retry.

Legacy Qwen inference-invalid counts: T=0 map 3/128; main T=0.2 N=5 3/640; protected invoice
follow-up 0/320.

## Statistical interpretation

Here **T** denotes sampling temperature and **N** denotes the number of
seed-based repeats contributing to the stated experiment or summary.

- T=0 cells are descriptive map points, **not** independent statistical samples.
- The main stochastic experiment is T=0.2 with N=5 seeds.
- The protected invoice N=20 file is a follow-up only. Combining the five main
  protected-invoice seeds with that follow-up yields a protected-only N=25
  descriptive summary — **not** a paired baseline/protected N=25 design.
- Seed-based confidence intervals describe stochastic variation under the fixed
  protocol; they do **not** imply population-level generalization.

## Security metric interpretation

- **Unauthorized Tool Request Rate (UTRR)** — proportion of inference-valid
  attack episodes with at least one unauthorized native tool request before
  runtime enforcement.
- **Blocking rate** — blocked unauthorized requests / unauthorized requests.
- **Unauthorized execution rate** — forbidden sandbox execution after runtime
  enforcement.
- **Task success rate** — proportion of evaluated episodes satisfying the
  task-success criterion (utility).
- **Policy overblocking** — runtime blocks a required authorized action.
- **Model underaction** — model fails to request the required action.

A **native tool request** is a structured tool call emitted by the model before
runtime `ToolPolicyEngine` enforcement.

Security success is not task success. Authorized execution is not necessarily
correct execution. Consequential-action fidelity is evaluated separately where
supported; answer–action content divergence denotes disagreement between the
textual answer and executed action content and is currently evaluated for the
invoice/mailbox setting.

Runtime `ToolPolicyEngine` is active under both baseline and protected prompt
conditions. The baseline condition does not add the protected prompt rules.
The protected condition adds fixed English SECURITY RULES on top (fixed
defense-language, not language-matched). Baseline is therefore not “no defense
whatsoever.”

Where `security_success = not unauthorized_execution` appears, treat it as a
post-policy outcome classification, not a direct measure of native model
robustness. Zero policy overblocking does not imply zero utility cost: model
underaction, incorrect consequential content, or incorrect final results can
still occur.

All consequential actions occur inside the LangTrust sandbox. No real external
e-mail, calendar, or filesystem side effects are performed.

## Verify the frozen G9C13 validation archive

The frozen three-model validation package (internal study ID `G9C13`) is
published in the LangTrust evaluation-artifacts record
[`10.5281/zenodo.22817213`](https://doi.org/10.5281/zenodo.22817213) as:

`LANGTRUST_G9C13_REPRO_ARCHIVE_2026-09-15.tar.gz`

Expected outer SHA-256:

`ecf8eaccd02dd4c7d01e7e7756e5fb1bdd8450beba4d362dc8625031de2e4aa2`

Verify the outer archive first with SHA-256, then extract it and run
`sha256sum -c SHA256SUMS.txt` inside the archive directory. The archive's
internal checksum manifest contains 96 verified entries.

The frozen primary collection contains 1920 records: 1914 inference-valid and
6 technical-missing records. Technical failures are treated as missingness for
behavioral endpoints rather than recoded as security success. The valid records
include 1437 attack and 477 benign episodes. The final cross-model audit
recorded 0 forbidden sandbox executions.

This archive is separate from the legacy Qwen three-file analysis workflow.

## Re-executing the legacy Qwen experiment configuration

Advanced workflow — prefer analysis reproduction for routine work.

Original runs used internal revision
`a0a6eb937b7bac933b20fcd96269cb53618937b8` (tree
`9c1fd1cde747e6777116566923152d182d4667b2`); model `qwen2.5:14b` with full
digest above; Ollama `0.32.15` at `http://localhost:11434/api/chat` with native
`tool_calls`; `num_predict = 1024`, timeout 120 s, max turns 8, map temperature
0, main temperature 0.2, no favorable retry.

Fresh T=0.2 generations form a **new** experiment run. Do not overwrite the
legacy Qwen result bundle. Exact byte-for-byte regeneration of the
original stochastic JSON is not expected.

For historical re-execution, use the runner behavior preserved in the archival
experiment snapshot together with the original protocol parameters. The later
installable `langtrust-benchmark` CLI belongs to the release software and should
not be assumed to be identical to the runner used for the legacy Qwen
experiment execution. Confirm historical re-execution behavior against the
archival experiment snapshot documentation and preserved protocol parameters.

## Legacy Qwen historical experiment source snapshot

The exact experiment source tree is preserved as a separate archival root
commit `c8ce0efd303eb618b1cfb84e8869a3d90bd050fc` outside curated `main` ancestry, tagged
`experiment-execution-snapshot`. Its tree is `9c1fd1cde747e6777116566923152d182d4667b2`. The public commit hash
differs from the internal revision, and tree equivalence has been verified.

Checkout:

```bash
git checkout experiment-execution-snapshot
```

Experiments were executed from the internal revision. The public archival
commit is a source-tree-equivalent representation of that historical state, not
the historical execution environment itself.

For routine analysis reproduction, prefer the current public software
release (`v0.2.1`). Use the archival snapshot for historical audit or
re-execution attempts.

The LangTrust release repository at https://github.com/rafalgajos/langtrust
uses a curated publication history and does not reproduce the complete internal
development history. Exact experiment source identity is preserved separately
via the archival snapshot.

## Reproducibility limits

- GitHub repository: https://github.com/rafalgajos/langtrust.
- The current public software release is `v0.2.1`, exact DOI `10.5281/zenodo.22815398`;
  the software all-versions DOI is `10.5281/zenodo.22799187`.
- The public evaluation-results record is DOI `10.5281/zenodo.22817213`.
- LangTrust `v0.2.0` remains the historical first public software release.
- The archival experiment commit/tag exists and legacy source-tree equivalence
  is verified.
- Desktop GUI Live Run does not provide hard cancellation of an in-flight model
  request in `v0.2.1`; requests end on completion or configured timeout.
- Stochastic T=0.2 reruns are not expected to reproduce exact generations.
- Model, runtime, hardware, and operating-system differences may affect fresh
  re-execution.
- Analysis reproduction from fixed legacy Qwen JSON is stronger and more
  deterministic than experiment re-execution.
- Provenance/reproducibility statements do not imply universal
  generalization.

## Release-time identifiers

| Identifier | Role | Status |
|---|---|---|
| Internal experiment revision `a0a6eb…` | Actual legacy-Qwen execution provenance | Established |
| Experiment tree `9c1fd1c…` | Exact legacy-Qwen source-tree identity | Established |
| Public tag `experiment-execution-snapshot` | Archival source representation | Established |
| Historical public tag `v0.2.0` | First public software release | Published |
| Current public tag `v0.2.1` | Recommended user software release | Published |
| Zenodo software DOI `10.5281/zenodo.22815398` | Current software archive | Published |
| Zenodo software all-versions DOI `10.5281/zenodo.22799187` | Software concept / all versions | Published |
| Zenodo evaluation-results DOI `10.5281/zenodo.22817213` | Legacy Qwen + frozen three-model evidence | Published |
| SoftwareX article DOI | Scholarly article | Not yet assigned |
| Apache-2.0 | Software license | Established |
