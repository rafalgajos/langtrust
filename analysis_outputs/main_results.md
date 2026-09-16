# LangTrust — Qwen experimental results

## Main stochastic experiment: T=0.2, N=5

| Domain | Baseline UTRR | Protected UTRR | Protection RD | Seed-level 95% CI | Baseline TSR | Protected TSR |
|---|---:|---:|---:|---:|---:|---:|
| Calendar | 35.00% | 0.00% | +35.00 pp | [+18.91 pp, +51.09 pp] | 47.50% | 72.50% |
| Files | 32.50% | 0.00% | +32.50 pp | [+26.01 pp, +38.99 pp] | 81.25% | 98.75% |
| Invoice | 100.00% | 86.25% | +13.75 pp | [+7.26 pp, +20.24 pp] | 43.75% | 38.75% |

Protection RD = baseline UTRR − protected UTRR.

## Protected invoice follow-up: combined N=25

- UTRR: 358/400 = 89.50%.
- Mean seed-level UTRR: 89.50%.
- Seed-level SD: 3.92%.
- Seed-level 95% CI: [87.88%, 91.12%].
- Runtime: 358/358 unauthorized native requests blocked; 0 unauthorized executions.

### Protected invoice language contrasts

| Factor | EN UTRR | PL UTRR | RD PL−EN | Seed-level 95% CI |
|---|---:|---:|---:|---:|
| user_instruction | 83.50% | 95.50% | +12.00 pp | [+6.74 pp, +17.26 pp] |
| tool_description | 90.50% | 88.50% | -2.00 pp | [-6.63 pp, +2.63 pp] |
| untrusted_content | 79.00% | 100.00% | +21.00 pp | [+17.76 pp, +24.24 pp] |
| attack_payload | 89.00% | 90.00% | +1.00 pp | [-3.69 pp, +5.69 pp] |

## Interpretation guardrails

- UTRR is a pre-enforcement model susceptibility metric.
- Unauthorized execution rate is a separate post-enforcement metric.
- Zero unauthorized executions reflects the runtime policy invariant in these benchmark scenarios, not universal model safety.
- Authorized tool execution does not imply consequential action correctness.
- The N=25 invoice follow-up estimates only the protected invoice condition; the paired protection comparison remains N=5.
- Seed-level confidence intervals describe stochastic variation under this fixed protocol and should not be interpreted as generalization to other models, prompts, domains, or deployments.
