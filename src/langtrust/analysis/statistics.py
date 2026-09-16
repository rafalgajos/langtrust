import json
from pathlib import Path


class ResultAnalyzer:
    """
    Performs statistical analysis
    on LangTrust experiment results.
    """

    def __init__(self, results_path):
        self.results_path = Path(results_path)

    def load(self):
        with open(
            self.results_path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    def attack_success_rate(self, data):
        """
        Calculates Attack Success Rate (ASR).
        """

        successful = sum(
            item["evaluation"]["attack_success"]
            for item in data
        )

        return successful / len(data)

    def mean_risk_score(self, data):
        """
        Calculates average risk score.
        """

        scores = [
            item["evaluation"]["risk_score"]
            for item in data
        ]

        return sum(scores) / len(scores)

    def summary(self, data):
        return {
            "cases": len(data),
            "attack_success_rate":
                self.attack_success_rate(data),
            "mean_risk_score":
                self.mean_risk_score(data),
        }

    def group_by_factor(self, data, factor):
        """
        Groups results by one experimental factor.
        """

        groups = {}

        for item in data:

            value = item["language_assignment"][factor]

            if value not in groups:
                groups[value] = []

            groups[value].append(item)

        results = {}

        for key, items in groups.items():

            results[key] = {
                "cases": len(items),

                "attack_success_rate":
                    sum(
                        x["evaluation"]["attack_success"]
                        for x in items
                    )
                    /
                    len(items),

                "mean_risk_score":
                    sum(
                        x["evaluation"]["risk_score"]
                        for x in items
                    )
                    /
                    len(items),
            }

        return results

    def group_by_language_consistency(self, data):
        """
        Compares fully consistent language contexts
        against mixed language contexts.
        """

        groups = {
            "fully_consistent": [],
            "mixed": []
        }

        for item in data:

            langs = item["language_assignment"]

            values = [
                langs["user_instruction"],
                langs["tool_description"],
                langs["untrusted_content"],
                langs["attack_payload"],
            ]

            if len(set(values)) == 1:
                groups["fully_consistent"].append(item)

            else:
                groups["mixed"].append(item)

        results = {}

        for key, items in groups.items():

            results[key] = {
                "cases": len(items),

                "attack_success_rate":
                    sum(
                        x["evaluation"]["attack_success"]
                        for x in items
                    )
                    /
                    len(items),

                "mean_risk_score":
                    sum(
                        x["evaluation"]["risk_score"]
                        for x in items
                    )
                    /
                    len(items),
            }

        return results
