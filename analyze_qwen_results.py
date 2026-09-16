import json
from collections import defaultdict


data = json.load(
    open("results/qwen_results.json")
)


stats = defaultdict(
    lambda: {
        "total":0,
        "attacks":0,
        "blocked":0
    }
)


for r in data:

    key = (
        "protected"
        if r["protected"]
        else "baseline"
    )

    stats[key]["total"] += 1

    if r["model_behavior"]["tool_call_detected"]:
        stats[key]["attacks"] += 1

    if r["security_decision"]["blocked"]:
        stats[key]["blocked"] += 1



for k,v in stats.items():

    print()
    print("================")
    print(k)
    print("================")

    print(
        "cases:",
        v["total"]
    )

    print(
        "attack attempts:",
        v["attacks"]
    )

    print(
        "attack rate:",
        v["attacks"]/v["total"]
    )

    print(
        "blocked:",
        v["blocked"]
    )
