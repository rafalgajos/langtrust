from src.langtrust.analysis.statistics import ResultAnalyzer


analyzer = ResultAnalyzer(
    "results/results.json"
)

data = analyzer.load()


print("===== SUMMARY =====")

print(
    analyzer.summary(data)
)


print("\n===== ATTACK PAYLOAD =====")

print(
    analyzer.group_by_factor(
        data,
        "attack_payload"
    )
)


print("\n===== UNTRUSTED CONTENT =====")

print(
    analyzer.group_by_factor(
        data,
        "untrusted_content"
    )
)


print("\n===== LANGUAGE CONSISTENCY =====")

print(
    analyzer.group_by_language_consistency(data)
)
