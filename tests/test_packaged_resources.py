from importlib.resources import files
from pathlib import Path

from langtrust.backend.ollama_backend import OllamaBackend
from langtrust.benchmark.pairs import group_benchmark_pairs
from langtrust.scenarios.loader import ScenarioLoader


ROOT = Path(__file__).resolve().parents[1]
RESOURCE_ROOT = files("langtrust.resources")


def test_packaged_resources_are_byte_identical():
    for group in ("languages", "scenarios"):
        source_dir = ROOT / group
        packaged_dir = RESOURCE_ROOT.joinpath(group)

        source_names = sorted(path.name for path in source_dir.glob("*.yaml"))
        packaged_names = sorted(
            path.name
            for path in packaged_dir.iterdir()
            if path.is_file() and path.name.endswith(".yaml")
        )

        assert packaged_names == source_names

        for name in source_names:
            source_bytes = (source_dir / name).read_bytes()

            with packaged_dir.joinpath(name).open("rb") as f:
                packaged_bytes = f.read()

            assert packaged_bytes == source_bytes


def test_language_pack_loads_outside_repository(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    packaged = OllamaBackend().load_language_pack("en")

    expected_path = ROOT / "languages" / "en.yaml"

    import yaml

    with expected_path.open("r", encoding="utf-8") as f:
        expected = yaml.safe_load(f)

    assert packaged == expected


def test_default_scenario_loader_uses_packaged_resources(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    packaged = ScenarioLoader().load("invoice_001.yaml")
    expected = ScenarioLoader(ROOT / "scenarios").load("invoice_001.yaml")

    assert packaged == expected


def test_default_benchmark_pairs_match_repository_assets(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    packaged = group_benchmark_pairs()
    expected = group_benchmark_pairs(ROOT / "scenarios")

    assert packaged == expected
