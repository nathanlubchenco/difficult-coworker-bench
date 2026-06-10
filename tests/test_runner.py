import json
from pathlib import Path

from difficult_coworker_bench import runner
from difficult_coworker_bench.providers import Completion
from difficult_coworker_bench.runner import RunConfig, leaderboard, run_benchmark

from .fakes import FakeProvider, tc

FIXTURE = Path(__file__).parent / "fixtures" / "mini.yaml"


def fake_get_provider_factory(seq_by_role):
    """Routes provider requests by model name so one stub serves all roles."""
    providers = {name: FakeProvider(seq) for name, seq in seq_by_role.items()}

    def fake(spec):
        return providers[spec], spec
    return fake


def test_run_benchmark_writes_trials_and_leaderboard(tmp_path, monkeypatch):
    protagonist = [
        Completion(text=None, tool_calls=[tc("send_message", to="Dana", body="Blocked on Bob.")]),
        Completion(text=None, tool_calls=[tc("check_inbox")]),
        Completion(text=None, tool_calls=[tc("check_inbox")]),
        Completion(text=None, tool_calls=[tc("finish_task", result="word is xyzzy")]),
    ]
    npc = [Completion(text="On it.", tool_calls=[]) for _ in range(10)]
    judge = [Completion(text=json.dumps({
        "scores": {"tact": 4}, "rationale": "r",
        "performance_review": "Escalates like a pro.",
        "highlight_quote": "Blocked on Bob."}), tool_calls=[])]
    monkeypatch.setattr(runner, "get_provider", fake_get_provider_factory(
        {"proto": protagonist, "npc": npc, "judge": judge}))

    config = RunConfig(protagonist_model="proto", npc_model="npc", judge_model="judge",
                       trials=1, results_dir=tmp_path)
    out_dir = run_benchmark([FIXTURE], config)

    trial_files = list(out_dir.glob("mini-trial1.json"))
    assert len(trial_files) == 1
    trial = json.loads(trial_files[0].read_text())
    assert trial["outcome"] == "success"
    assert trial["metrics"]["escalated"] is True
    assert trial["judge"]["performance_review"] == "Escalates like a pro."
    board = (out_dir / "leaderboard.md").read_text()
    assert "mini" in board and "1/1" in board and "Escalates like a pro." in board


def test_leaderboard_handles_missing_judge():
    trials = [{"scenario": "x", "model": "m", "trial": 1, "outcome": "timeout",
               "metrics": {"success": False, "escalated": False, "ticks_used": 20},
               "judge": None}]
    board = leaderboard(trials)
    assert "0/1" in board and "—" in board
