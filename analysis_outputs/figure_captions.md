# Figure captions

## Figure 1 — Attack susceptibility by domain

Unauthorized Tool Request Rate (UTRR) in the main stochastic experiment (T=0.2, five seeds per factorial cell). Prompt-level protection eliminated observed unauthorized tool requests in the calendar and files domains (0/80 in each protected condition) but only partially reduced susceptibility in the invoice domain, from 100% (80/80) to 86.25% (69/80). UTRR measures native unauthorized tool requests before runtime policy enforcement.

## Figure 2 — Paired protection effect

Seed-level paired reduction in UTRR between baseline and protected conditions in the main stochastic experiment. Positive values indicate lower UTRR under prompt protection. Error bars show seed-level 95% t intervals under the fixed experimental protocol. Mean reductions were 35.0 percentage points for calendar, 32.5 percentage points for files, and 13.75 percentage points for invoice.

## Figure 3 — Language-factor contrasts in protected Invoice

Language-factor contrasts in the protected invoice condition using 25 stochastic seeds per factorial cell. Points show the mean seed-level risk difference in UTRR between Polish and English settings (PL − EN); error bars show seed-level 95% t intervals. The strongest observed contrast concerned untrusted-content language (+21.0 percentage points), followed by user-instruction language (+12.0 percentage points).

## Figure 4 — Protected Invoice susceptibility by factorial cell

Cell-level UTRR in the protected invoice condition using 25 stochastic repetitions per factorial cell. Error bars show Wilson 95% intervals for the observed cell-level proportions. Twelve of sixteen cells produced unauthorized requests in all 25 repetitions; the remaining cells produced 24/25, 16/25, 12/25, and 6/25 unauthorized requests. No cell had zero observed unauthorized requests across all 25 repetitions.

## Figure 5 — Benign utility and consequential-action fidelity

Benign-task performance in the main stochastic experiment. Required-tool execution indicates whether the authorized consequential action was executed; consequential-action correctness evaluates the content of that action; task success combines the task requirements. Calendar and files achieved 100% on all three measures. In invoice, all 77 inference-valid benign episodes executed the authorized email action, but consequential-action correctness and task success were both 0%, demonstrating divergence between successful tool execution and consequential-action fidelity. B = baseline; P = protected prompt.
