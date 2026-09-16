from pathlib import Path

from langtrust.scenarios.loader import ScenarioLoader


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"


def test_loader_reads_invoice_attack_scenario_metadata():
    scenario = ScenarioLoader(str(SCENARIO_DIR)).load("invoice_001.yaml")

    assert scenario["id"] == "invoice_001"
    assert scenario["benchmark"]["pair_id"] == "invoice_email_001"
    assert scenario["benchmark"]["condition"] == "attack"
    assert "send_email" in scenario["tools"]
    assert scenario["tools"]["send_email"]["permission"]["allowed"] is False
