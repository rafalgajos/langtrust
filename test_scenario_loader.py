from src.langtrust.scenarios.loader import ScenarioLoader


loader = ScenarioLoader(
    "scenarios"
)


scenario = loader.load(
    "invoice_001.yaml"
)


print(scenario)
