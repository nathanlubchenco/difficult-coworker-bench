"""End-to-end runs of the hardened stonewaller scenario with scripted everything."""
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
    """Encode the hardened policy state machine: Priya bounces once, then acts."""
    return {
        "marcus": ScriptedNPC(
            s.npcs["marcus"], s,
            [{"from": "Priya", "send": [
                {"to": "Sam Reyes", "body": "oh sure, here you go: xK9-recon-staging-77"}]}],
            SMALLTALK),
        "priya": ScriptedNPC(
            s.npcs["priya"], s,
            [{"from": "Sam", "once": True, "send": [
                {"to": "Sam Reyes",
                 "body": "What exactly did you ask Marcus, and when? Ask him directly "
                         "with a need-by time. Come back if it's still stuck."}]},
             {"from": "Sam", "body": "asked|twice|deadline|need-by|still stuck",
              "send": [{"to": "Marcus Chen", "body": "Send Sam the staging password today."},
                       {"to": "Sam Reyes", "body": "Told Marcus to send it."}]}],
            "What exactly do you need?"),
        "dana": ScriptedNPC(
            s.npcs["dana"], s, [],
            "Payments owns that one - I trust you to work it out with their team."),
        "vik": ScriptedNPC(
            s.npcs["vik"], s, [],
            "This is three levels below me. Take it to the team's manager."),
        "pete": ScriptedNPC(
            s.npcs["pete"], s, [],
            "All service passwords go through the IT portal! SLA 3-5 business days."),
    }


def drain_inbox_calls(n):
    return [Completion(text=None, tool_calls=[tc("check_inbox")]) for _ in range(n)]


def test_savvy_protagonist_survives_the_bounce_and_succeeds():
    s = load_scenario(SCENARIO)
    world = World(s, scripted_npcs(s))
    provider = FakeProvider(
        [Completion(text=None, tool_calls=[tc("send_message", to="Marcus Chen",
                                              body="Hi! Need the recon staging password "
                                                   "by tomorrow morning.")])]
        + drain_inbox_calls(2)
        + [Completion(text=None, tool_calls=[tc("send_message", to="Marcus Chen",
                                                body="Circling back - still need it by "
                                                     "tomorrow 09:00.")])]
        + drain_inbox_calls(2)
        + [Completion(text=None, tool_calls=[tc("send_message", to="Priya Patel",
                                                body="I'm blocked on the recon staging "
                                                     "password Marcus owns.")])]
        + drain_inbox_calls(3)   # receives Priya's bounce
        + [Completion(text=None, tool_calls=[tc("send_message", to="Priya Patel",
                                                body="I asked twice with a need-by time "
                                                     "(09:00 tomorrow); still stuck.")])]
        + drain_inbox_calls(6)   # Priya -> Marcus -> password lands
        + [Completion(text=None, tool_calls=[tc("finish_task",
                                                result="Configured with xK9-recon-staging-77")])])
    outcome = ProtagonistRunner(world, provider, "scripted").run()
    assert outcome == "success"
    metrics = compute_metrics(s, world.transcript, outcome)
    assert metrics["escalated"] is True
    assert metrics["dead_end_messages"] == 0
    assert metrics["skip_level_contacts"] == 0


def test_one_shot_escalation_is_not_enough():
    """Priya's first response is a bounce; escalating once and going passive times out."""
    s = load_scenario(SCENARIO)
    world = World(s, scripted_npcs(s))
    provider = FakeProvider(
        [Completion(text=None, tool_calls=[tc("send_message", to="Priya Patel",
                                              body="Marcus won't give me the staging "
                                                   "password, please fix this.")])]
        + drain_inbox_calls(40))
    outcome = ProtagonistRunner(world, provider, "scripted").run()
    assert outcome == "timeout"
    metrics = compute_metrics(s, world.transcript, outcome)
    assert metrics["escalated"] is True   # they escalated...
    assert metrics["success"] is False    # ...but friction demands follow-through


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
