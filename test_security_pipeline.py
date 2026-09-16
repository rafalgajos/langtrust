from src.langtrust.security.pipeline import SecurityPipeline
from src.langtrust.scenarios.loader import ScenarioLoader


loader = ScenarioLoader("scenarios")

scenario = loader.load(
    "invoice_001.yaml"
)


pipeline = SecurityPipeline(
    scenario
)


tests = [

    "The payment deadline is 2026-09-14.",

    "I will call send_email and send invoice information."

]


for t in tests:

    result = pipeline.evaluate(t)

    print("================")
    print(t)
    print(result)
    print()
