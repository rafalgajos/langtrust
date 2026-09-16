from src.langtrust.backend.simulator_backend import SimulatorBackend
from src.langtrust.scenarios.loader import ScenarioLoader


loader = ScenarioLoader(
    "scenarios"
)


scenario = loader.load(
    "invoice_001.yaml"
)


backend = SimulatorBackend()


result = backend.run(
    {
        "user_instruction": "en",
        "tool_description": "en",
        "untrusted_content": "en",
        "attack_payload": "en",
    },
    scenario
)


print(result)
