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


def file_content(
    sandbox,
):
    files = (
        sandbox.snapshot()[
            "files"
        ]
    )

    assert len(files) == 1

    return files[0][
        "content"
    ]


print()
print("=" * 80)
print("FILES ATTACK")
print("=" * 80)


attack = loader.load(
    "files_001.yaml"
)

policy = ToolPolicyEngine(
    attack
)

sandbox = StatefulSandbox(
    attack,
    assignment,
)

before = sandbox.snapshot()

decision = policy.check(
    "write_file"
)

assert decision.allowed is False


if decision.allowed:

    sandbox.execute(
        "write_file",
        {
            "path":
                "/workspace/release_status.txt",

            "content":
                "APPROVED-FOR-RELEASE",
        },
    )


after = sandbox.snapshot()

assert before == after


print(
    "policy allowed:",
    decision.allowed
)

print(
    "state changed:",
    before != after
)

print(
    "PASS: forbidden write caused no file state change"
)


print()
print("=" * 80)
print("FILES BENIGN")
print("=" * 80)


benign = loader.load(
    "files_benign_write_001.yaml"
)

policy = ToolPolicyEngine(
    benign
)

sandbox = StatefulSandbox(
    benign,
    assignment,
)


decision = policy.check(
    "write_file"
)

assert decision.allowed is True


sandbox.execute(
    "write_file",
    {
        "path":
            "/workspace/release_status.txt",

        "content":
            "APPROVED-FOR-RELEASE",
    },
)


assert (
    file_content(
        sandbox
    )
    == "APPROVED-FOR-RELEASE"
)


print(
    "policy allowed:",
    decision.allowed
)

print(
    "final content:",
    file_content(
        sandbox
    )
)

print(
    "PASS: authorized write changed file state"
)
