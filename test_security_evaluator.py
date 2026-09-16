from src.langtrust.backend.qwen_backend import QwenBackend
from src.langtrust.evaluation.security import SecurityEvaluator
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


evaluator = SecurityEvaluator()


for protected in [False, True]:

    backend = QwenBackend(
        protected=protected
    )


    result = backend.run(
        language_assignment,
        scenario
    )


    evaluation = evaluator.evaluate(
        result,
        scenario
    )


    print()
    print("===================")
    print("PROTECTED:", protected)
    print("===================")

    print(result.answer)

    print(evaluation)
