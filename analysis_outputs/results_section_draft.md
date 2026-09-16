# Results

## Experimental reliability

The main stochastic experiment comprised 640 planned episodes across three domains, two prompt-protection conditions, and five stochastic repetitions per factorial cell at temperature 0.2. Of these, 637 episodes completed with valid inference, corresponding to an inference-valid rate of 99.53%. Three episodes terminated at the predefined generation budget (`num_predict=1024`); all three occurred in the benign invoice scenario. All 480 attack episodes were inference-valid.

Inference failures were treated separately from security and utility outcomes and were not classified as safe, unsafe, successful, or unsuccessful task executions.

Unless otherwise stated, confidence intervals reported for stochastic comparisons are seed-level t intervals describing variation under the fixed benchmark protocol; they are not intended as population-level generalization to other models, domains, prompts, or deployments.

## Prompt-level protection reduces unauthorized tool requests, but the effect is domain-dependent

The primary security metric was Unauthorized Tool Request Rate (UTRR), defined as the proportion of inference-valid attack episodes in which the model generated a native request for an action forbidden by the scenario policy, before runtime enforcement.

In the calendar domain, baseline UTRR was 35.0% (28/80), whereas no unauthorized tool request was observed under the protected prompt condition (0/80). The mean seed-level reduction in UTRR was 35.0 percentage points (95% CI: 18.9–51.1 pp).

A similar pattern was observed in the files domain. Baseline UTRR was 32.5% (26/80), compared with 0% (0/80) under prompt protection. The mean seed-level reduction was 32.5 percentage points (95% CI: 26.0–39.0 pp).

The invoice domain behaved differently. Baseline UTRR reached 100% (80/80), indicating that every baseline attack episode produced a native request for the forbidden email action. Prompt protection reduced UTRR to 86.25% (69/80), corresponding to a mean reduction of 13.75 percentage points (95% CI: 7.26–20.24 pp). Thus, although prompt protection reduced model susceptibility in all three domains, the magnitude of the effect was substantially smaller in the invoice domain.

## Runtime policy enforcement blocked all observed unauthorized executions

Across the 480 attack episodes in the main stochastic experiment, the model generated 203 unauthorized native tool requests. The runtime policy engine blocked all 203 observed requests before sandbox execution, and no unauthorized consequential action was executed.

This distinction is important: UTRR measures model susceptibility before enforcement, whereas unauthorized execution measures the post-enforcement system outcome. The absence of unauthorized executions therefore reflects the runtime enforcement invariant in these benchmark scenarios and does not imply that the underlying model was uniformly resistant to indirect prompt injection.

The same observed enforcement behavior was reproduced in the deterministic map and in the targeted invoice follow-up. In the deterministic experiment, 44 unauthorized requests were generated and all 44 were blocked. In the additional protected-invoice experiment, 289 unauthorized requests were generated and all 289 were blocked, again with zero unauthorized executions.

## Protected invoice remains highly susceptible under repeated stochastic evaluation

Because the invoice domain remained highly vulnerable after prompt protection, a targeted follow-up was performed using 20 additional seeds. These runs were combined with the original five protected-invoice seeds, yielding 25 stochastic realizations for each of the 16 factorial cells and 400 protected invoice attack episodes in total. This follow-up estimates the protected invoice condition only; the paired baseline-versus-protected comparison remains based on the original five-seed experiment.

Across these 400 episodes, UTRR was 89.5% (358/400). Mean seed-level UTRR was also 89.5%, with a standard deviation of 3.92 percentage points and a seed-level 95% confidence interval of 87.88–91.12%.

The cell-level analysis showed substantial heterogeneity within the factorial design. Twelve of the sixteen cells produced unauthorized requests in all 25 repetitions. One additional cell produced an unauthorized request in 24/25 repetitions. The three remaining cells showed lower but non-zero susceptibility: 16/25, 12/25, and 6/25 unauthorized requests, respectively. No protected invoice configuration remained free of observed unauthorized requests across all 25 repetitions.

## Language-factor effects differ across domains

The factorial design independently varied the language of the user instruction, tool description, untrusted content, and attack payload.

In baseline calendar and files scenarios, the strongest descriptive language effect concerned the attack payload. English attack payloads were associated with markedly higher UTRR than Polish payloads. In the five-seed stochastic experiment, the pooled PL–EN UTRR risk difference for attack-payload language was −60 percentage points in both calendar and files.

The protected invoice follow-up exhibited a different pattern. The strongest language contrast concerned the language of the untrusted content. When the untrusted content was in English, protected-invoice UTRR was 79.0% (158/200), whereas Polish untrusted content produced an UTRR of 100% (200/200). The mean seed-level PL–EN risk difference was +21.0 percentage points (95% CI: +17.76 to +24.24 pp).

The language of the user instruction also showed a positive PL–EN contrast of +12.0 percentage points (95% CI: +6.74 to +17.26 pp). In contrast, the tool-description contrast was −2.0 percentage points (95% CI: −6.63 to +2.63 pp), and the attack-payload contrast was +1.0 percentage point (95% CI: −3.69 to +5.69 pp).

These results indicate that multilingual susceptibility cannot be characterized solely by the language of the injected payload. Different linguistic components of the agent environment contribute differently depending on domain and defense condition.

## Benign tasks reveal consequential-action fidelity failures

Benign scenarios were used to evaluate whether runtime protection prevented legitimate consequential actions or caused model underaction.

In both calendar and files, all 80 inference-valid benign episodes executed the required authorized tool action, with no policy overblocking and no model underaction. All 80 episodes also achieved task success and consequential-action correctness.

The invoice domain produced a qualitatively different failure mode. Across 77 inference-valid benign invoice episodes, the model executed the authorized email action in all 77 cases, with zero policy overblocking and zero model underaction. However, consequential-action correctness was 0/77 and task success was 0/77. Answer/action content divergence occurred in all 77 episodes.

The observed invoice-content failures consisted of placeholders, incorrect factual values, and missing required facts. Thus, selecting and executing the correct authorized tool was insufficient to guarantee correctness of the consequential action. This result motivates evaluating final-answer correctness, authorized-action execution, consequential-action correctness, and answer/action divergence as distinct dimensions.

## Summary

The experiments reveal three distinct security and reliability phenomena.

First, prompt-level protection substantially reduced unauthorized tool requests in calendar and files, but was considerably less effective in invoice scenarios.

Second, external runtime enforcement blocked all observed forbidden native tool requests before sandbox execution in the evaluated scenarios.

Third, benign invoice tasks exposed a separate consequential-action fidelity problem: the model could execute the correct authorized tool while producing an incorrect action payload.

Together, these results support treating model susceptibility, runtime execution safety, task utility, and consequential-action fidelity as separate properties of tool-using agents.
