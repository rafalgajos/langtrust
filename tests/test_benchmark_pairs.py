from pathlib import Path

import pytest

from langtrust.benchmark.pairs import group_benchmark_pairs


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"

EXPECTED_DOMAINS = {
    "invoice_email_001": "invoice",
    "calendar_delete_001": "calendar",
    "file_write_001": "files",
}


@pytest.fixture(scope="module")
def benchmark_pairs():
    return group_benchmark_pairs(str(SCENARIO_DIR))


def test_expected_benchmark_pairs_are_present(benchmark_pairs):
    assert set(benchmark_pairs) == set(EXPECTED_DOMAINS)


@pytest.mark.parametrize(
    ("pair_id", "expected_domain"),
    EXPECTED_DOMAINS.items(),
)
def test_attack_pair_has_expected_domain(
    benchmark_pairs,
    pair_id,
    expected_domain,
):
    attack = benchmark_pairs[pair_id]["attack"]

    assert attack["benchmark"]["domain"] == expected_domain


@pytest.mark.parametrize(
    "pair_id",
    EXPECTED_DOMAINS,
)
def test_attack_payload_factor_only_exists_in_attack_condition(
    benchmark_pairs,
    pair_id,
):
    attack_factors = benchmark_pairs[
        pair_id
    ]["attack"]["benchmark"]["active_language_factors"]

    benign_factors = benchmark_pairs[
        pair_id
    ]["benign"]["benchmark"]["active_language_factors"]

    assert "attack_payload" in attack_factors
    assert "attack_payload" not in benign_factors


def test_file_benign_pair_has_expected_language_factors(
    benchmark_pairs,
):
    factors = benchmark_pairs[
        "file_write_001"
    ]["benign"]["benchmark"]["active_language_factors"]

    assert factors == [
        "user_instruction",
        "tool_description",
    ]
