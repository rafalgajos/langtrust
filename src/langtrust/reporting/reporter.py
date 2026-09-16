import json
from pathlib import Path


class ReportGenerator:
    """
    Generates human-readable reports
    from LangTrust experiment results.
    """

    def __init__(
        self,
        results_path,
        output_dir="reports"
    ):

        self.results_path = Path(results_path)
        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            exist_ok=True
        )


    def load(self):

        with open(
            self.results_path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)


    def create_summary(self, data):

        cases = len(data)

        successful = sum(
            item["evaluation"]["attack_success"]
            for item in data
        )

        risk = sum(
            item["evaluation"]["risk_score"]
            for item in data
        ) / cases


        return {
            "cases": cases,
            "successful_attacks": successful,
            "attack_success_rate": successful / cases,
            "mean_risk_score": risk
        }


    def save_json(self, summary):

        path = self.output_dir / "summary.json"

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                summary,
                f,
                indent=2
            )


        return path


    def save_markdown(self, summary):

        path = self.output_dir / "summary.md"


        text = f"""
# LangTrust Experiment Report


## Overview

Cases: {summary["cases"]}

Successful attacks:
{summary["successful_attacks"]}


Attack Success Rate:

{summary["attack_success_rate"]:.2%}


Mean Risk Score:

{summary["mean_risk_score"]:.3f}

"""


        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(text)


        return path
