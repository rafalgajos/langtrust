from src.langtrust.models.language_risk import LanguageRiskModel


model = LanguageRiskModel()


cases = [
    (
        "en",
        "en",
        "en",
        "en",
    ),
    (
        "en",
        "pl",
        "en",
        "pl",
    ),
    (
        "pl",
        "pl",
        "pl",
        "pl",
    ),
]


for case in cases:

    risk = model.calculate(*case)

    print(
        case,
        "=>",
        risk
    )
