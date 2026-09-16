from src.langtrust.backend.qwen_backend import QwenBackend
from src.langtrust.security.pipeline import SecurityPipeline
from src.langtrust.scenarios.loader import ScenarioLoader


loader = ScenarioLoader("scenarios")

scenario = loader.load(
    "invoice_001.yaml"
)


pipeline = SecurityPipeline(
    scenario
)


backend = QwenBackend(
    protected=False
)


language_assignment = {
    "user_instruction": "en",
    "tool_description": "en",
    "untrusted_content": "en",
    "attack_payload": "en",
}


result = backend.run(
    language_assignment,
    scenario
)


print("================ QWEN OUTPUT ================")
print(result.answer)

print()
print("================ LANGTRUST DECISION ================")

decision = pipeline.evaluate(
    result.answer
)

print(decision)
