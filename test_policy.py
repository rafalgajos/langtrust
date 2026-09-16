from src.langtrust.security.policy import ToolPolicyEngine
from src.langtrust.scenarios.loader import ScenarioLoader


loader = ScenarioLoader("scenarios")

scenario = loader.load(
    "invoice_001.yaml"
)


policy = ToolPolicyEngine(scenario)


for tool in [
    "read_invoice",
    "send_email"
]:

    result = policy.check(tool)

    print(tool)
    print(result)
    print()
