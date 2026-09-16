from importlib.resources import files
from pathlib import Path

import yaml


class ScenarioLoader:
    """Load LangTrust scenario definitions from YAML files."""

    def __init__(self, scenarios_path=None):
        if scenarios_path is None:
            self.scenarios_path = files("langtrust.resources").joinpath("scenarios")
        else:
            self.scenarios_path = Path(scenarios_path)

    def list_files(self):
        """Return available YAML scenario filenames in deterministic order."""
        return sorted(
            path.name
            for path in self.scenarios_path.iterdir()
            if path.is_file() and path.name.endswith(".yaml")
        )

    def load(self, scenario_file):
        path = self.scenarios_path.joinpath(scenario_file)

        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
