import yaml
from pathlib import Path


class ScenarioLoader:
    """
    Loads security scenarios used
    in LangTrust experiments.
    """

    def __init__(self, scenarios_path):
        self.scenarios_path = Path(scenarios_path)


    def load(self, scenario_file):

        path = self.scenarios_path / scenario_file

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            return yaml.safe_load(f)
