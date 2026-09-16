from pathlib import Path

from langtrust.cli import analyze


def test_analyze_cli_parses_explicit_paths(tmp_path):
    outdir = tmp_path / "outputs"

    args = analyze.parse_args(
        [
            "--t0",
            "t0.json",
            "--main",
            "main.json",
            "--follow",
            "follow.json",
            "--outdir",
            str(outdir),
        ]
    )

    assert args.t0 == Path("t0.json")
    assert args.main == Path("main.json")
    assert args.follow == Path("follow.json")
    assert args.outdir == outdir


def test_analyze_main_delegates_to_analysis(tmp_path, monkeypatch):
    captured = {}

    def fake_run_analysis(t0_path, main_path, follow_path, outdir):
        captured.update(
            {
                "t0": t0_path,
                "main": main_path,
                "follow": follow_path,
                "outdir": outdir,
            }
        )

    monkeypatch.setattr(
        analyze,
        "run_analysis",
        fake_run_analysis,
    )

    analyze.main(
        [
            "--t0",
            "t0.json",
            "--main",
            "main.json",
            "--follow",
            "follow.json",
            "--outdir",
            str(tmp_path),
        ]
    )

    assert captured == {
        "t0": Path("t0.json"),
        "main": Path("main.json"),
        "follow": Path("follow.json"),
        "outdir": tmp_path,
    }
