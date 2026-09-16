# LangTrust Provenance

## Scope

This document records the scientific and software provenance of the LangTrust
experiments and of the later release-preparation lineage. It identifies the
exact internal revision that executed the legacy Qwen experiments, the
associated source tree, model/runtime/protocol, and result artifacts, and it
explains how the release repository will represent that history.

The LangTrust release repository uses a curated publication history and will
not reproduce the complete internal development history. This is intentional:
a clean publication history improves readability, while the exact experiment
repository tree will be preserved separately and verifiably.

Development-process disclosures, when required, are handled in release
documentation rather than in this file.

## Evidence generations

Two experiment generations are intentionally preserved.

The **legacy Qwen study** is the historical single-model dataset associated with
the repository-root `SHA256SUMS`, `langtrust-analyze`, and the existing
`analysis_outputs/` directory.

The **G9C13 study** is the later frozen three-model validation campaign used for
SoftwareX evidence. Its canonical source state is:

- commit `ffac44664244399b9fee024762b0d8afdff8ec05`
- tree `ef8c86ba2e8e9fee51f0f8a9a4cb8e326e34964d`

The two studies have separate result identities and must not be treated as one
combined experiment.

## Legacy Qwen experiment execution provenance

The legacy single-model Qwen experiments were executed from the internal
development revision:

`a0a6eb937b7bac933b20fcd96269cb53618937b8`

Commit subject:

Add bounded inference and failure-aware benchmark execution

Observed commit timestamp (UTC):

2026-09-02 20:10:29 +0000

That revision is the actual experiment-execution provenance identifier.

Later packaging, documentation, citation, and release-preparation commits did
**not** generate the legacy Qwen experiment result artifacts.

## Legacy Qwen source tree

The Git tree object of the experiment-execution revision is:

`9c1fd1cde747e6777116566923152d182d4667b2`

That tree contains 91 tracked files, including the canonical language packs,
scenario definitions, experiment code, and some historical development files.

Historical or intermediate files present in that tree (for example under
`reports/`) are preserved verbatim so that the archival source identity remains
exact. They are **not** the legacy Qwen publication results. The legacy Qwen
result artifacts are the three JSON files identified in `ARTIFACTS.md` by their
SHA-256 digests.

## Legacy Qwen model and runtime

Model:

- name: `qwen2.5:14b`
- full digest: `7cdf5a0187d5c58cc5d369b255592f7841d1c4696d45a8c8a9489440385b22f6`
- family: qwen2
- parameters: 14.8B
- quantization: Q4_K_M
- context length: 32768
- embedding length: 5120

Runtime:

- Ollama `0.32.15` (systemd service model)
- API: `http://localhost:11434/api/chat`
- native tool calling via `tool_calls`
- hardware: 2 × NVIDIA Quadro RTX 6000 (24 GB VRAM each)

Do not confuse the short Ollama identifier prefix with the full model digest
above.

## Legacy Qwen experiment protocol

LangTrust evaluates tool-using LLM agents under indirect prompt injection in a
controlled Polish–English design across three domains (invoice, calendar,
files), with 64 unique design cells. Attack conditions independently vary
relevant language surfaces (user instruction, tool description, untrusted
content, and attack payload) as defined by the scenario protocol.

Legacy Qwen protocol assets in the experiment state include:

- `languages/en.yaml`, `languages/pl.yaml`
- `scenarios/invoice_001.yaml`, `scenarios/invoice_benign_email_001.yaml`
- `scenarios/calendar_001.yaml`, `scenarios/calendar_benign_delete_001.yaml`
- `scenarios/files_001.yaml`, `scenarios/files_benign_write_001.yaml`

Inference protocol used for the legacy Qwen runs:

- `num_predict = 1024`
- request timeout = 120 seconds
- max turns = 8
- deterministic map temperature = 0
- main stochastic temperature = 0.2

Generation reaching `done_reason = "length"` at the configured generation cap
is treated as inference-invalid / censored. No favorable retry was used.

The protected condition uses fixed English SECURITY RULES (a fixed
defense-language condition), not language-matched protection text.

All consequential tool effects occur inside the LangTrust sandbox. No real
external e-mail, calendar, or filesystem action is performed.

Runtime `ToolPolicyEngine` enforcement is part of the evaluated system under
both baseline and protected prompt conditions. Detailed metric definitions and
interpretation belong in analysis documentation and `ARTIFACTS.md` /
`REPRODUCIBILITY.md`.

## Legacy Qwen result artifacts

The preserved legacy Qwen raw result snapshots are:

| File | Records (valid / invalid) | SHA-256 |
|---|---|---|
| `langtrust_3domains_t0_n1_bounded_run2.json` | 128 (125 / 3 `generation_limit`) | `9293e770c8bf2a74769871249fe712797d8997f3eb1738b17511ec8d048babfc` |
| `langtrust_3domains_t02_n5.json` | 640 (637 / 3 `generation_limit`) | `d58ec6608f70e16075d78147200addcfb6142fb0389621b66dde24c1f6a8b819` |
| `invoice_attack_protected_t02_n20.json` | 320 (320 / 0) | `cfb77cce1137861c47e1e2f402533071b0a2816224e83d3667c9f20ae4fc8717` |

Embedded result metadata identifies experiment provenance commit
`a0a6eb937b7bac933b20fcd96269cb53618937b8`.

These files are not tracked in Git. They are intended for archival publication
in a dedicated Zenodo results record. Integrity verification and download
workflow are documented in `ARTIFACTS.md` and `SHA256SUMS`.

## Protocol asset stability

At internal release-preparation revision
`c7503d699585c568a663731fe2d019e07e16753e`, the canonical `languages/` and
`scenarios/` protocol assets have no content differences relative to experiment
revision `a0a6eb937b7bac933b20fcd96269cb53618937b8`. This comparison was verified
directly between those two revisions.

Experiment provenance therefore remains attached to `a0a6eb…`, with protocol
asset stability checked independently of later packaging and documentation work.

## G9C13 multi-model validation provenance

G9C13 was executed from the common canonical LangTrust source state:

- branch: `feature/qwen-agent-backend`
- commit: `ffac44664244399b9fee024762b0d8afdff8ec05`
- tree: `ef8c86ba2e8e9fee51f0f8a9a4cb8e326e34964d`
- Ollama runtime: `0.32.15`
- models: Qwen 2.5 14B, Llama 3.1 8B, Mistral 7B
- primary temperature: `0.2`

All three execution worktrees used the same canonical source tree.

Primary collection status:

- 3/3 models complete
- 1920/1920 planned records collected
- 1914 inference-valid records
- 6 technical-missing records
- 1437 inference-valid attack records
- 477 inference-valid benign records
- 0 forbidden sandbox executions

Frozen reproducibility archive:

`LANGTRUST_G9C13_REPRO_ARCHIVE_2026-09-15.tar.gz`

Archive SHA-256:

`ecf8eaccd02dd4c7d01e7e7756e5fb1bdd8450beba4d362dc8625031de2e4aa2`

Its internal `SHA256SUMS.txt` contains 96 verified entries.

Key frozen manifest SHA-256 identities:

- primary manifest:
  `d655b0dd51c3d4fd059989a3c3348851a610a5d6d41db5bc12ec603dd900a834`
- primary SAP:
  `5182671482505d83fb82aba36f8c3a98c0b2c3e7a48af64278512edf435e195d`
- consolidated reporting result:
  `b5e7dcc56465c4633b1256057602f149cec47da271c288885d535a716d98fcbe`
- final cross-model audit:
  `d0e855f18babd7fd8b590493dadac4705edced6dece47a0f35f82f4885a5c98b`
- publication table result:
  `92e12ffeac8a9529589dcf13f51062232b86b103c89163c4790dc33061b18775`
- frozen publication table:
  `be70282b60ae467568945e9e3f3511283d5a658334b811c9af4c35570beeac86`

These frozen identities are independent of later packaging, documentation, and
public-history preparation.

## Release-preparation lineage

The current internal release-preparation lineage is later than the experiment
execution revision. It includes categories of work such as:

- installable packaging and packaged language/scenario resources
- benchmark and analysis CLIs and related refactoring/helpers
- expanded and canonicalized tests, including packaging tests
- citation metadata (`CITATION.cff`)
- artifact documentation (`ARTIFACTS.md`, `SHA256SUMS`)
- documentation and maintainability/readability cleanup

These later changes improve packaging, usability, testing, and documentation.
They do not redefine the provenance of the three legacy Qwen JSON artifacts
or the separately frozen G9C13 validation archive.

The public software release for users is LangTrust `v0.2.0`. The
archival experiment source snapshot has a different role: exact historical
source representation for audit/reproduction of the 2026 experiment state.
Routine users should use the public software release rather than
the archival snapshot, unless they specifically need the historical tree.

The public package version is `0.2.0`, released under tag `v0.2.0`.

## Curated public Git history

The private/internal repository remains the canonical development record and is
not rewritten for publication.

The LangTrust release repository is
https://github.com/rafalgajos/langtrust. It uses a curated publication-oriented
`main` history leading to LangTrust `v0.2.0`. That public `main` history does not
reproduce every private development commit. The goal is publication clarity and
a readable release history, while exact experiment source identity is preserved
by the separate archival snapshot described below.

## Legacy Qwen public archival experiment snapshot

Separately from curated `main` ancestry, the public repository contains
archival root commit `c8ce0efd303eb618b1cfb84e8869a3d90bd050fc`, which preserves the exact source tree of internal
revision `a0a6eb937b7bac933b20fcd96269cb53618937b8`.

Public tag:

`experiment-execution-snapshot`

That archival commit:

- is not an ancestor of curated public `main`;
- has a different commit hash because it belongs to a new public Git history;
- has Git tree object `9c1fd1cde747e6777116566923152d182d4667b2`.

The experiments were executed from the internal revision. The public archival
commit is a source-tree-equivalent representation of that historical state; it
is not itself claimed as the execution environment.

## Archival snapshot verification

Already verified in the internal record:

- experiment revision and tree object identity;
- artifact SHA-256 digests;
- embedded experiment provenance in the three JSON files;
- no content diff for canonical `languages/` and `scenarios/` between the
  experiment revision and the current release-preparation HEAD.

The archival snapshot tree-equivalence check has been completed.

- internal experiment revision:
  `a0a6eb937b7bac933b20fcd96269cb53618937b8`
- internal experiment tree: `9c1fd1cde747e6777116566923152d182d4667b2`
- public archival commit: `c8ce0efd303eb618b1cfb84e8869a3d90bd050fc`
- public archival tree: `9c1fd1cde747e6777116566923152d182d4667b2`
- public tag: `experiment-execution-snapshot`
- tree equivalence: **verified**

The release repository URL is https://github.com/rafalgajos/langtrust.
The Zenodo software release DOI `10.5281/zenodo.22799188` identifies the published `0.2.0`
software archive. The all-versions DOI is `10.5281/zenodo.22799187`. The separate
Zenodo results DOI has not yet been assigned.

## Version and archival identifiers

| Identifier | Role | Status |
|---|---|---|
| Internal experiment revision `a0a6eb…` | Actual execution provenance | Established |
| Experiment tree `9c1fd1c…` | Exact source-tree identity | Established |
| Public release lineage (`0.2.0`) | Packaging/docs/release | Established |
| Public tag `v0.2.0` | Recommended user software release | Established |
| Public tag `experiment-execution-snapshot` | Archival source representation | Established |
| Zenodo software DOI `10.5281/zenodo.22799188` | Software archive | Published |
| Zenodo results DOI | Legacy Qwen JSON archive | Planned |
| SoftwareX article DOI | Scholarly article | Planned |
| Apache-2.0 | Software license | Established |

Authors and citation metadata are recorded in `CITATION.cff`.

## Limitations of provenance claims

- Internal/public tree equivalence has been verified for the archival snapshot;
  this establishes source-tree identity, not execution-environment identity.
- GitHub repository: https://github.com/rafalgajos/langtrust; Zenodo software release DOI `10.5281/zenodo.22799188` is published and the all-versions DOI is `10.5281/zenodo.22799187`, while the Zenodo results DOI and SoftwareX article DOI are not yet assigned.
- LangTrust `v0.2.0` is the first public software release.
- The software release is licensed under Apache-2.0.
- This document establishes the source, runtime, and protocol associated with
  the reported experiments. It does not claim universal bit-for-bit
  reproducibility across all hardware, OS, or Ollama versions.
