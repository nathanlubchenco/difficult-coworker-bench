import json

import pytest

from difficult_coworker_bench import cli


def test_list_command(capsys, monkeypatch, tmp_path):
    (tmp_path / "alpha.yaml").write_text("x: 1")
    (tmp_path / "beta.yaml").write_text("x: 1")
    monkeypatch.setattr(cli, "list_scenarios", lambda: sorted(tmp_path.glob("*.yaml")))
    monkeypatch.setattr("sys.argv", ["dcb", "list"])
    cli.main()
    out = capsys.readouterr().out
    assert "alpha" in out and "beta" in out


def test_report_command(tmp_path, monkeypatch):
    trial = {"scenario": "x", "model": "m", "trial": 1, "outcome": "success",
             "metrics": {"success": True, "escalated": True, "ticks_used": 4},
             "judge": None}
    (tmp_path / "x-trial1.json").write_text(json.dumps(trial))
    monkeypatch.setattr("sys.argv", ["dcb", "report", str(tmp_path)])
    cli.main()
    assert "1/1" in (tmp_path / "leaderboard.md").read_text()


def test_report_command_multiple_dirs_writes_comparison(tmp_path, monkeypatch):
    for i, model in enumerate(["m1", "m2"]):
        d = tmp_path / f"run{i}"
        d.mkdir()
        trial = {"scenario": "x", "model": model, "trial": 1, "outcome": "success",
                 "metrics": {"success": True, "escalated": True, "ticks_used": 4},
                 "score": 70.0, "judge": None}
        (d / "x-trial1.json").write_text(json.dumps(trial))
    monkeypatch.setattr("sys.argv", ["dcb", "report",
                                     str(tmp_path / "run0"), str(tmp_path / "run1")])
    cli.main()
    md = (tmp_path / "comparison.md").read_text()
    assert "m1" in md and "m2" in md and "**Overall**" in md


def test_report_rescore_recomputes_scores_from_current_formula(tmp_path, monkeypatch):
    # A failed run stored with the old formula's bogus efficiency points.
    trial = {"scenario": "mini", "model": "m", "trial": 1, "outcome": "gave_up",
             "metrics": {"success": False, "escalated": False, "ticks_used": 5},
             "score": 28.6, "judge": None}
    (tmp_path / "mini-trial1.json").write_text(json.dumps(trial))
    fixture_dir = __import__("pathlib").Path(__file__).parent / "fixtures"
    monkeypatch.setattr(cli, "scenarios_dir", lambda: fixture_dir)
    monkeypatch.setattr("sys.argv", ["dcb", "report", "--rescore", str(tmp_path)])
    cli.main()
    rescored = json.loads((tmp_path / "mini-trial1.json").read_text())
    assert rescored["score"] == 0.0


def test_run_rejects_unknown_scenario(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "scenarios_dir", lambda: tmp_path)
    monkeypatch.setattr("sys.argv",
                        ["dcb", "run", "--protagonist", "m", "--scenario", "nope"])
    with pytest.raises(SystemExit):
        cli.main()
