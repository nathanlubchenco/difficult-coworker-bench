"""End-to-end runs of the stonewaller scenario with scripted everything."""
from pathlib import Path

from difficult_coworker_bench.metrics import compute_metrics
from difficult_coworker_bench.npc import ScriptedNPC
from difficult_coworker_bench.protagonist import ProtagonistRunner
from difficult_coworker_bench.providers import Completion
from difficult_coworker_bench.scenario import load_scenario
from difficult_coworker_bench.world import World

from .fakes import FakeProvider, tc

SCENARIO = Path(__file__).resolve().parents[1] / "scenarios" / "stonewaller.yaml"

SMALLTALK = "Did you catch the game? Also my Linea Mini is singing today."


def scripted_npcs(s):
    return {
        "marcus": ScriptedNPC(
            s.npcs["marcus"], s,
            [{"from": "Priya", "send": [
                {"to": "Sam Reyes", "body": "oh sure, here you go: xK9-recon-staging-77"}]}],
            SMALLTALK),
        "priya": ScriptedNPC(
            s.npcs["priya"], s,
            [{"from": "Sam", "body": "block|password|stuck",
              "send": [{"to": "Marcus Chen", "body": "Send Sam the staging password today."},
                       {"to": "Sam Reyes", "body": "Told Marcus to send it."}]}],
            "What exactly do you need?"),
        "dana": ScriptedNPC(
            s.npcs["dana"], s, [],
            "Try Priya Patel - she's Marcus's manager."),
    }


def drain_inbox_calls(n):
    return [Completion(text=None, tool_calls=[tc("check_inbox")]) for _ in range(n)]


def test_savvy_protagonist_succeeds_via_escalation():
    s = load_scenario(SCENARIO)
    world = World(s, scripted_npcs(s))
    provider = FakeProvider(
        [Completion(text=None, tool_calls=[tc("send_message", to="Marcus Chen",
                                              body="Hi! Need the recon staging password.")])]
        + drain_inbox_calls(3)
        + [Completion(text=None, tool_calls=[tc("send_message", to="Marcus Chen",
                                                body="Circling back - still need it.")])]
        + drain_inbox_calls(3)
        + [Completion(text=None, tool_calls=[tc("send_message", to="Priya Patel",
                                                body="I'm blocked: I need the recon staging "
                                                     "password Marcus owns.")])]
        + drain_inbox_calls(6)
        + [Completion(text=None, tool_calls=[tc("finish_task",
                                                result="Configured with xK9-recon-staging-77")])])
    outcome = ProtagonistRunner(world, provider, "scripted").run()
    assert outcome == "success"
    metrics = compute_metrics(s, world.transcript, outcome)
    assert metrics["escalated"] is True
    assert metrics["dead_end_messages"] == 0


def test_doormat_protagonist_times_out():
    s = load_scenario(SCENARIO)
    world = World(s, scripted_npcs(s))
    moves = []
    for _ in range(10):
        moves.append(Completion(text=None, tool_calls=[
            tc("send_message", to="Marcus Chen", body="Any chance of that password? "
               "Also yes, great game!")]))
        moves += drain_inbox_calls(3)
    outcome = ProtagonistRunner(world, FakeProvider(moves), "scripted").run()
    assert outcome == "timeout"
    metrics = compute_metrics(s, world.transcript, outcome)
    assert metrics["escalated"] is False
    assert metrics["dead_end_messages"] > 0
