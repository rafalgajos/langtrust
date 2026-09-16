# LangTrust Artifacts

## Purpose

This document separates two LangTrust evidence generations: the preserved
single-model Qwen dataset used by the legacy analysis CLI and the separately
frozen G9C13 multi-model validation archive. It records how each evidence
package is identified and verified.

It distinguishes:

- **legacy Qwen raw result artifacts** (immutable experiment JSON snapshots), and
- **derived analysis outputs** (tables, summaries, and figures produced from those
  snapshots).

## Evidence generations

LangTrust preserves two distinct experiment evidence generations:

1. **Legacy Qwen study** — three JSON snapshots consumed by
   `langtrust-analyze`, with digests recorded in the repository-root
   `SHA256SUMS`.
2. **G9C13 multi-model validation study** — a separately frozen reproducibility
   archive containing Qwen, Llama, and Mistral primary runs, manifests,
   provenance, analysis records, and publication tables.

The root `SHA256SUMS` belongs only to the legacy Qwen dataset. G9C13 carries its
own internal `SHA256SUMS.txt`. These checksum manifests are intentionally
separate.

## Legacy Qwen experiment artifacts

The three files below are the preserved legacy single-model Qwen result snapshots.
They are **not** tracked in Git. They are intended for archival publication in a
dedicated Zenodo results record. The DOI and download location will be added when
that public archive is created.

| Artifact | Role | T | N | Records | Valid | Invalid | SHA256 |
|---|---|---:|---:|---:|---:|---:|---|
| `langtrust_3domains_t0_n1_bounded_run2.json` | Deterministic descriptive map | 0.0 | 1 | 128 | 125 | 3 (`generation_limit`) | `9293e770c8bf2a74769871249fe712797d8997f3eb1738b17511ec8d048babfc` |
| `langtrust_3domains_t02_n5.json` | Main stochastic experiment | 0.2 | 5 | 640 | 637 | 3 (`generation_limit`) | `d58ec6608f70e16075d78147200addcfb6142fb0389621b66dde24c1f6a8b819` |
| `invoice_attack_protected_t02_n20.json` | Protected invoice attack follow-up | 0.2 | 20 | 320 | 320 | 0 | `cfb77cce1137861c47e1e2f402533071b0a2816224e83d3667c9f20ae4fc8717` |

Notes:

- **T=0, N=1** provides descriptive map points. It is not an independent
  statistical sample set.
- **T=0.2, N=5** is the main stochastic experiment used for paired
  baseline/protected comparisons.
- **T=0.2, N=20** is a protected-invoice follow-up only. Combining it with the
  five protected invoice seeds from the main experiment yields a protected-only
  N=25 summary; that summary is **not** a paired N=25 baseline/protected design.
- Episodes marked invalid above failed with `generation_limit` and are treated as
  inference-invalid/censored. No favorable retry was used.
- All consequential tool effects in these experiments occur inside the LangTrust
  sandbox.

## Integrity verification

The repository root integrity manifest `SHA256SUMS` belongs to this legacy Qwen dataset and lists the three filenames
and their SHA-256 digests.

Verification must be performed in a directory that contains **both**
`SHA256SUMS` and the three downloaded JSON files (for example after extracting
the Zenodo artifact bundle). The raw JSON files are not present in a normal Git
clone.

Linux:

```bash
sha256sum -c SHA256SUMS
```

macOS:

```bash
shasum -a 256 -c SHA256SUMS
```

A matching digest is required before treating a downloaded legacy Qwen file as verified.

## Legacy Qwen experiment source provenance

The legacy Qwen experiments were executed from internal development revision
`a0a6eb937b7bac933b20fcd96269cb53618937b8`, whose Git tree is
`9c1fd1cde747e6777116566923152d182d4667b2`.

The LangTrust release repository at https://github.com/rafalgajos/langtrust
uses a curated publication history and does not reproduce the complete private
development history. This is intentional. The private/internal repository
remains the canonical development record and is not rewritten for publication.

For reproducibility, the exact source tree corresponding to the internal
experiment revision will be preserved separately from the curated `main`
history as an archival root commit (outside the curated `main` ancestry),
tagged `experiment-execution-snapshot`. Before public release, its Git tree
object will be verified to match the internal experiment tree exactly
(`9c1fd1cde747e6777116566923152d182d4667b2`).

The archival commit will have a different commit hash because it belongs to a
new public Git history. It preserves the historical source tree verbatim and is
not itself claimed as the environment in which the experiments were executed.

Historical development reports or intermediate analysis files present in that
archival tree are not the legacy Qwen publication results. The legacy Qwen
experiment result artifacts are the three JSON files identified above by their
SHA-256 digests.

Later publication, packaging, documentation, GUI, and release-preparation
changes belong to the curated public `main` history and do not redefine the
provenance of the experiment artifacts.

Detailed provenance and public-history construction are documented in
`PROVENANCE.md`.

## Obtaining the legacy Qwen artifacts

1. Download the legacy Qwen result bundle from the dedicated Zenodo results
   record (URL/DOI to be added at public release).
2. Confirm the bundle contains the three JSON filenames listed above and
   `SHA256SUMS`.
3. Verify digests with the commands in [Integrity verification](#integrity-verification).

Optional copies of `ARTIFACTS.md` may accompany the Zenodo deposit for convenience.
The Zenodo results record is the canonical archive for the legacy Qwen raw JSON files.

## Running the legacy Qwen analysis

After installing LangTrust and verifying the downloaded artifacts:

```bash
langtrust-analyze \
  --t0 <path>/langtrust_3domains_t0_n1_bounded_run2.json \
  --main <path>/langtrust_3domains_t02_n5.json \
  --follow <path>/invoice_attack_protected_t02_n20.json \
  --outdir <output-directory>
```

Replace `<path>` with the directory that holds the verified JSON files.

The legacy Qwen analysis workflow has been regression-checked against the
validated reference outputs; detailed reproduction guidance is provided in
`REPRODUCIBILITY.md`.

## Legacy Qwen derived analysis outputs

Selected derived analysis products live under `analysis_outputs/` in the
repository (for example CSVs, summary Markdown, figures, and
`analysis_manifest.json`).

These files are **derived** from the legacy Qwen JSON artifacts. They support
inspection and paper preparation, but they are not substitutes for the raw
experiment snapshots. Re-running `langtrust-analyze` on the verified JSON files
is the path to regenerate analysis products.

## Immutability and future experiment versions

For the published experiment release:

- these three artifacts are immutable;
- their SHA-256 digests define the frozen legacy Qwen bytes;
- they must not be overwritten by later runs;
- later software packaging releases do not retroactively change experiment
  provenance;
- future experiment campaigns should use new filenames and new archive
  versions or records.

## Frozen G9C13 multi-model validation archive

The G9C13 validation study is frozen independently from the legacy Qwen
analysis dataset.

Archive:

`LANGTRUST_G9C13_REPRO_ARCHIVE_2026-09-15.tar.gz`

SHA-256:

`ecf8eaccd02dd4c7d01e7e7756e5fb1bdd8450beba4d362dc8625031de2e4aa2`

Canonical source:

- commit `ffac44664244399b9fee024762b0d8afdff8ec05`
- tree `ef8c86ba2e8e9fee51f0f8a9a4cb8e326e34964d`

Primary collection:

- 3/3 models complete
- 1920/1920 records collected
- 1914 inference-valid
- 6 technical missingness
- 1437 inference-valid attack records
- 477 inference-valid benign records
- 0 forbidden sandbox executions

Primary raw-result SHA-256:

- Qwen 2.5 14B:
  `0572425977644c1151b74ee6f57f78509617994c6ffa59792f22da93a9de55d0`
- Llama 3.1 8B:
  `b195d336a38c96ca8715f8494c21b0933fa0050c2537a4ee31643afdaf21c9f4`
- Mistral 7B:
  `2fe2f8d35db8dac6dd6c4f29c184e77d474f25e20bf8b7266883ec6d53735ac8`

The archive has its own `SHA256SUMS.txt` with 96 verified entries and is
independent of the repository-root legacy `SHA256SUMS`.

## Citation and archival identifiers

Cite the LangTrust software using `CITATION.cff` (and the software DOI once
minted).

The legacy Qwen result bundle is intended to receive a separate Zenodo
results DOI. The SoftwareX article DOI, when assigned, will be a third, distinct
identifier.

LangTrust software release metadata declares the Apache License 2.0.
Software, experiment-data, and article archival identifiers remain distinct.
