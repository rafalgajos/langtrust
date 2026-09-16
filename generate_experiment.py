import itertools
from pathlib import Path
import yaml


CONFIG_FILE = "experiment.yaml"


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_language_matrix(languages):
    """
    Generates full factorial design.

    Example:
    en/pl × en/pl × en/pl × en/pl

    Returns:
    16 combinations
    """

    axes = [
        "user_instruction",
        "tool_description",
        "untrusted_content",
        "attack_payload",
    ]

    combinations = []

    for values in itertools.product(languages, repeat=len(axes)):
        case = {
            axis: language
            for axis, language in zip(axes, values)
        }

        combinations.append(case)

    return combinations


def save_cases(cases, output_dir):
    output = Path(output_dir)
    output.mkdir(exist_ok=True)

    for index, case in enumerate(cases, start=1):

        filename = (
            output
            / f"case_{index:03d}_"
            f"{case['user_instruction']}_"
            f"{case['tool_description']}_"
            f"{case['untrusted_content']}_"
            f"{case['attack_payload']}.yaml"
        )

        data = {
            "case_id": index,
            "language_assignment": case,
        }

        with open(filename, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                allow_unicode=True,
                sort_keys=False
            )


def main():

    config = load_config()

    languages = config["languages"]

    cases = generate_language_matrix(languages)

    print(
        f"Generated factorial design: {len(cases)} cases"
    )

    save_cases(
        cases,
        config["output"]["directory"]
    )

    print(
        f"Saved to: {config['output']['directory']}"
    )


if __name__ == "__main__":
    main()
