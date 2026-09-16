from src.langtrust.reporting.reporter import ReportGenerator


reporter = ReportGenerator(
    "results/results.json"
)


data = reporter.load()

summary = reporter.create_summary(
    data
)


print(summary)


print(
    reporter.save_json(summary)
)


print(
    reporter.save_markdown(summary)
)
