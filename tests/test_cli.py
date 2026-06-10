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


def test_run_rejects_unknown_scenario(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "scenarios_dir", lambda: tmp_path)
    monkeypatch.setattr("sys.argv",
                        ["dcb", "run", "--protagonist", "m", "--scenario", "nope"])
    with pytest.raises(SystemExit):
        cli.main()
