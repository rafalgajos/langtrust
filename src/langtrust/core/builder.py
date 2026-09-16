from pathlib import Path
import yaml


class ExperimentBuilder:
    """
    Combines generated language cases
    with security scenarios.
    """

    def __init__(self, scenario_path):
        self.scenario_path = Path(scenario_path)
        self.scenario = self._load_yaml(
            self.scenario_path
        )

    def _load_yaml(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def build(self, case_path):

        case = self._load_yaml(
            Path(case_path)
        )

        experiment = {
            "case_id": case["case_id"],

            "scenario": {
                "id": self.scenario["id"],
                "name": self.scenario["name"],
            },

            "language_assignment":
                case["language_assignment"],

            "attack":
                self.scenario["attack"],

            "evaluation":
                self.scenario["evaluation"],
        }

        return experiment
