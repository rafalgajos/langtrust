# Discussion

## Prompt-level protection varied substantially across the evaluated domains

In the evaluated scenarios, prompt-level protection could not be characterized by a single benchmark-wide effectiveness value. In the calendar and files domains, no unauthorized tool request was observed under the protected condition across 80 attack episodes per domain. In contrast, the invoice domain remained highly susceptible: UTRR decreased from 100% in baseline to 86.25% in the paired five-seed experiment.

The targeted invoice follow-up strengthened this observation. Across 25 protected-condition seeds and 400 attack episodes, mean UTRR was 89.5%. Twelve of sixteen factorial cells produced unauthorized requests in all 25 repetitions, and no cell remained free of observed unauthorized requests across all 25 runs.

These results suggest that the effectiveness of a prompt-level defense depends substantially on the structure of the task and tool interaction. The benchmark therefore should not summarize prompt protection solely using a single pooled robustness number across heterogeneous domains.

## Multilingual susceptibility is component-specific rather than a single language effect

The factorial design separated the language of the user instruction, tool description, untrusted content, and attack payload. This distinction proved important because the dominant language effect differed between domains and protection conditions.

In baseline calendar and files scenarios, attack-payload language showed the largest descriptive contrast, with English payloads associated with substantially higher UTRR than Polish payloads. However, in the protected invoice follow-up, attack-payload language showed little difference. Instead, the largest contrast concerned the language of the untrusted content: Polish untrusted content produced 100% UTRR compared with 79% for English untrusted content. User-instruction language also showed a smaller but consistent PL–EN contrast.

This pattern argues against treating an attack as simply “English” or “Polish.” In tool-using agents, multiple linguistic surfaces coexist within the same episode, and changing different surfaces may have different effects on model behavior.

The observed contrasts should nevertheless be interpreted as properties of the evaluated model, prompts, scenarios, and execution protocol. They do not establish a general hierarchy of language vulnerability across other models or deployments.

## Model susceptibility and execution safety are distinct properties

A central result of the benchmark is the separation between model-level susceptibility and system-level enforcement.

Across the main stochastic attack experiment, the model generated 203 native requests for actions forbidden by the scenario policy. The runtime policy engine blocked all 203 observed requests before sandbox execution. The same behavior was observed in the deterministic experiment and in the targeted invoice follow-up.

Thus, a system can exhibit substantial pre-enforcement vulnerability while still preventing unauthorized state changes through an external enforcement layer. Conversely, reporting only the absence of unauthorized executions would conceal substantial model susceptibility.

This distinction motivates reporting at least two separate security outcomes: Unauthorized Tool Request Rate before enforcement and Unauthorized Execution Rate after enforcement. Blocking rate characterizes the runtime policy layer rather than the intrinsic robustness of the model.

The observed 100% blocking rate should be interpreted as an invariant of the evaluated policy-controlled scenarios, not as evidence of universal enforcement reliability outside the benchmark.

## Authorized execution does not imply consequential-action correctness

The benign invoice scenario exposed a separate failure mode that is not captured by conventional measures of tool selection or authorization.

Across all 77 inference-valid benign invoice episodes, the model requested and executed the required authorized email action. The runtime policy did not overblock the action, and the model did not underact. Nevertheless, consequential-action correctness was 0/77 and task success was 0/77.

The failures included unresolved placeholders, incorrect factual values, and missing required facts in the executed action payload. In these episodes, the model could produce a correct factual final answer while executing an email containing incorrect information.

Within the evaluated invoice scenarios, this shows that successful reasoning in the natural-language answer and successful tool invocation did not guarantee fidelity of the consequential action. For tool-using systems, evaluation should therefore distinguish at least: whether the required action was requested, whether it was authorized and executed, whether its arguments were factually correct, and whether the final task requirements were satisfied.

## No universal security–utility trade-off was observed

In calendar and files attack scenarios, prompt protection reduced UTRR while task success increased. Calendar attack TSR increased from 47.5% to 72.5%, and files increased from 81.25% to 98.75%.

Invoice again behaved differently: attack TSR decreased from 43.75% to 38.75% while UTRR was only partially reduced. Thus, the relation between security-oriented prompting and task utility was also domain-dependent.

Across the evaluated domains, the results did not exhibit a universal security–utility trade-off. Instead, prompt protection may simultaneously improve instruction following and reduce susceptibility in some environments while offering weaker security gains or lower utility in others.

## Inference reliability should be reported separately from task outcomes

The bounded-inference protocol recorded three generation-limit failures among 640 planned episodes in the main stochastic experiment. All three occurred in benign invoice scenarios.

These episodes were not classified as safe attack outcomes or ordinary task failures. Treating inference termination as a separate reliability dimension avoids artificially improving security metrics by counting failed generations as non-attacks and avoids degrading utility metrics by treating generation-budget termination as an ordinary task failure.

The concentration of the observed generation-limit events in one scenario family may warrant investigation in future work, but three events are insufficient to establish a language- or domain-level causal explanation.

## Limitations

The present experiments evaluate one model family and one specific quantized checkpoint under a fixed local inference stack. The language space is limited to Polish and English, and the benchmark currently contains three consequential-action domains.

The five-seed main experiment provides repeated stochastic observations for paired baseline-versus-protected comparisons, but the number of seed-level replicates remains modest. The additional 20-seed experiment was intentionally targeted to the protected invoice condition and therefore cannot be used as a 25-seed paired estimate of prompt-protection effectiveness.

The scenarios execute consequential actions only in a local sandbox. The benchmark therefore measures native tool requests, policy decisions, and sandbox state transitions rather than effects on external production systems.

The current prompt-level protection represents one defense formulation. The results should not be interpreted as a general evaluation of all prompt-based indirect-prompt-injection defenses.

Finally, the observed language contrasts describe the fixed factorial benchmark cells and stochastic seeds evaluated here. Generalization to additional languages, models, domains, attack constructions, and tool interfaces requires further experimentation.

## Implications for LangTrust

The results support a benchmark design in which multilingual agent security is evaluated across multiple independently controlled linguistic surfaces rather than through translation of the user prompt alone.

They also support separating three layers of evaluation:

1. model susceptibility before runtime enforcement;
2. runtime prevention of unauthorized consequential actions;
3. correctness and fidelity of authorized consequential actions.

This separation prevents a system with strong runtime blocking from being mistaken for a model intrinsically resistant to prompt injection, and prevents correct tool selection from being mistaken for correct consequential execution.

The invoice results further support including domain diversity in the benchmark. A defense that appeared fully effective in two domains remained highly vulnerable in a third, demonstrating that conclusions drawn from a single tool or workflow may substantially overestimate robustness.
