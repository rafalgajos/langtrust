from src.langtrust.backend.qwen_backend import QwenBackend
from src.langtrust.scenarios.loader import ScenarioLoader


loader = ScenarioLoader(
    "scenarios"
)

scenario = loader.load(
    "invoice_001.yaml"
)


language_assignment = {
    "user_instruction": "en",
    "tool_description": "en",
    "untrusted_content": "en",
    "attack_payload": "en",
}


for mode in [False, True]:

    print()
    print("==============================")
    print("PROTECTED:", mode)
    print("==============================")


    backend = QwenBackend(
        protected=mode
    )


    result = backend.run(
        language_assignment,
        scenario
    )


    print(result.answer)
