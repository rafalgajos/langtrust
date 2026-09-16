from pathlib import Path

import pytest

from langtrust.benchmark.design import generate_language_cells
from langtrust.benchmark.pairs import group_benchmark_pairs


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"

EXPECTED_COUNTS = {
    ("calendar_delete_001", "attack"): 16,
    ("calendar_delete_001", "benign"): 4,
    ("invoice_email_001", "attack"): 16,
    ("invoice_email_001", "benign"): 8,
    ("file_write_001", "attack"): 16,
    ("file_write_001", "benign"): 4,
}


@pytest.fixture(scope="module")
def benchmark_pairs():
    return group_benchmark_pairs(str(SCENARIO_DIR))


@pytest.mark.parametrize(
    ("pair_id", "condition", "expected_count"),
    [
        (pair_id, condition, count)
        for (pair_id, condition), count in EXPECTED_COUNTS.items()
    ],
)
def test_language_cell_counts_and_factor_consistency(
    benchmark_pairs,
    pair_id,
    condition,
    expected_count,
):
    scenario = benchmark_pairs[pair_id][condition]
    cells = generate_language_cells(scenario)

    assert len(cells) == expected_count

    cell_keys = [cell["cell_key"] for cell in cells]
    assert len(cell_keys) == len(set(cell_keys))

    for cell in cells:
        assert set(
            cell["active_language_assignment"]
        ) == set(
            cell["active_language_factors"]
        )


def test_factorial_design_contains_exactly_64_unique_cells(
    benchmark_pairs,
):
    total = 0

    for pair_id, condition in EXPECTED_COUNTS:
        scenario = benchmark_pairs[pair_id][condition]
        total += len(generate_language_cells(scenario))

    assert total == 64
