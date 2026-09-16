from src.langtrust.core.builder import ExperimentBuilder


builder = ExperimentBuilder(
    "scenarios/invoice_001.yaml"
)

experiment = builder.build(
    "generated/case_001_en_en_en_en.yaml"
)


print(experiment)
