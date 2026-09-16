# Main security and utility results

| Domain | Baseline UTRR | Protected UTRR | Protection RD (baseline − protected) | Seed-level 95% CI | Baseline attack TSR | Protected attack TSR |
|---|---:|---:|---:|---:|---:|---:|
| Calendar | 28/80 (35.00%) | 0/80 (0.00%) | +35.00 pp | [+18.91, +51.09] pp | 38/80 (47.50%) | 58/80 (72.50%) |
| Files | 26/80 (32.50%) | 0/80 (0.00%) | +32.50 pp | [+26.01, +38.99] pp | 65/80 (81.25%) | 79/80 (98.75%) |
| Invoice | 80/80 (100.00%) | 69/80 (86.25%) | +13.75 pp | [+7.26, +20.24] pp | 35/80 (43.75%) | 31/80 (38.75%) |

Notes:

- UTRR is measured before runtime policy enforcement.
- Protection effects are based on the paired T=0.2, five-seed experiment.
- All 203 unauthorized native tool requests observed in the main stochastic experiment were blocked before sandbox execution; unauthorized executions = 0.
- The targeted protected-invoice follow-up is not included in the paired protection effect above. Across 25 protected-invoice seeds, UTRR was 358/400 (89.50%), with seed-level 95% CI [87.88%, 91.12%].
