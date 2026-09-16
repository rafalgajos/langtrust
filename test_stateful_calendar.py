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


def event_count(sandbox):
    return len(
        sandbox.snapshot()[
            "calendar"
        ][
            "events"
        ]
    )


print()
print("=" * 80)
print("CALENDAR ATTACK")
print("=" * 80)


attack = loader.load(
    "calendar_001.yaml"
)

attack_policy = ToolPolicyEngine(
    attack
)

attack_sandbox = StatefulSandbox(
    attack,
    assignment,
)


assert event_count(
    attack_sandbox
) == 1


decision = attack_policy.check(
    "delete_event"
)


assert decision.allowed is False


if decision.allowed:

    attack_sandbox.execute(
        "delete_event",
        {
            "event_id":
                "EVT-2026-091"
        },
    )


assert event_count(
    attack_sandbox
) == 1


print(
    "policy allowed:",
    decision.allowed
)

print(
    "events after:",
    event_count(
        attack_sandbox
    )
)

print(
    "PASS: forbidden deletion caused "
    "no calendar state change"
)


print()
print("=" * 80)
print("CALENDAR BENIGN")
print("=" * 80)


benign = loader.load(
    "calendar_benign_delete_001.yaml"
)

benign_policy = ToolPolicyEngine(
    benign
)

benign_sandbox = StatefulSandbox(
    benign,
    assignment,
)


assert event_count(
    benign_sandbox
) == 1


decision = benign_policy.check(
    "delete_event"
)


assert decision.allowed is True


if decision.allowed:

    benign_sandbox.execute(
        "delete_event",
        {
            "event_id":
                "EVT-2026-091"
        },
    )


assert event_count(
    benign_sandbox
) == 0


print(
    "policy allowed:",
    decision.allowed
)

print(
    "events after:",
    event_count(
        benign_sandbox
    )
)

print(
    "PASS: authorized deletion changed "
    "calendar state"
)
