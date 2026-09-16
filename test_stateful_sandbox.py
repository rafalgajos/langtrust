from src.langtrust.environment.sandbox import StatefulSandbox
from src.langtrust.scenarios.loader import ScenarioLoader
from src.langtrust.security.policy import ToolPolicyEngine


assignment = {
    "user_instruction": "en",
    "tool_description": "en",
    "untrusted_content": "en",
    "attack_payload": "en",
}


loader = ScenarioLoader(
    "scenarios"
)


print("=" * 80)
print("ATTACK SCENARIO")
print("=" * 80)

attack_scenario = loader.load(
    "invoice_001.yaml"
)

attack_policy = ToolPolicyEngine(
    attack_scenario
)

attack_sandbox = StatefulSandbox(
    attack_scenario,
    assignment,
)


before = attack_sandbox.snapshot()

decision = attack_policy.check(
    "send_email"
)

assert decision.allowed is False


if decision.allowed:
    attack_sandbox.execute(
        "send_email",
        {
            "recipient":
                "audit@example.test",

            "content":
                "sensitive invoice information",
        },
    )


after = attack_sandbox.snapshot()


print(
    "policy allowed:",
    decision.allowed
)

print(
    "messages before:",
    len(
        before[
            "mailbox"
        ][
            "sent_messages"
        ]
    )
)

print(
    "messages after:",
    len(
        after[
            "mailbox"
        ][
            "sent_messages"
        ]
    )
)


assert before == after

assert len(
    after[
        "mailbox"
    ][
        "sent_messages"
    ]
) == 0


print(
    "PASS: forbidden email caused no state change"
)


print()
print("=" * 80)
print("BENIGN AUTHORIZED SCENARIO")
print("=" * 80)


benign_scenario = loader.load(
    "invoice_benign_email_001.yaml"
)

benign_policy = ToolPolicyEngine(
    benign_scenario
)

benign_sandbox = StatefulSandbox(
    benign_scenario,
    assignment,
)


before = benign_sandbox.snapshot()

decision = benign_policy.check(
    "send_email"
)

assert decision.allowed is True


if decision.allowed:

    benign_sandbox.execute(
        "send_email",
        {
            "recipient":
                "finance@example.test",

            "content":
                (
                    "Invoice FV-2026-081 "
                    "payment deadline: 2026-09-14"
                ),
        },
    )


after = benign_sandbox.snapshot()


print(
    "policy allowed:",
    decision.allowed
)

print(
    "messages before:",
    len(
        before[
            "mailbox"
        ][
            "sent_messages"
        ]
    )
)

print(
    "messages after:",
    len(
        after[
            "mailbox"
        ][
            "sent_messages"
        ]
    )
)


assert len(
    before[
        "mailbox"
    ][
        "sent_messages"
    ]
) == 0

assert len(
    after[
        "mailbox"
    ][
        "sent_messages"
    ]
) == 1

assert (
    after[
        "mailbox"
    ][
        "sent_messages"
    ][0][
        "recipient"
    ]
    == "finance@example.test"
)


print(
    "PASS: authorized email produced exactly one sandbox side effect"
)
