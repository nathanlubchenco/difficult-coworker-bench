from pathlib import Path

from difficult_coworker_bench.npc import ScriptedNPC
from difficult_coworker_bench.protagonist import ProtagonistRunner
from difficult_coworker_bench.providers import Completion
from difficult_coworker_bench.scenario import load_scenario
from difficult_coworker_bench.world import World

from .fakes import FakeProvider, tc

FIXTURE = Path(__file__).parent / "fixtures" / "mini.yaml"


def make_world():
    s = load_scenario(FIXTURE)
    npcs = {"bob": ScriptedNPC(s.npcs["bob"], s, [], "Lovely weather."),
            "dana": ScriptedNPC(s.npcs["dana"], s, [], "Noted.")}
    return World(s, npcs)


def test_happy_path_runs_tools_until_finish():
    world = make_world()
    provider = FakeProvider([
        Completion(text="Let me look around.", tool_calls=[tc("list_directory")]),
        Completion(text=None, tool_calls=[tc("finish_task", result="xyzzy")]),
    ])
    outcome = ProtagonistRunner(world, provider, "fake").run()
    assert outcome == "success"
    system = provider.calls[0]["system"]
    assert "Sam Reyes" in system and "Pylon Analytics" in system
    assert "magic word" in system          # task text included
    assert "escalat" not in system.lower()  # no hints!
    assert "supervisor" not in system.lower()
    # tool result was timestamped and fed back
    tool_msg = provider.calls[1]["messages"][-1]
    assert tool_msg["role"] == "tool" and "[Day 1, 09:00]" in tool_msg["content"]


def test_text_only_responses_get_nudged_then_stall():
    world = make_world()
    provider = FakeProvider([Completion(text="Thinking...", tool_calls=[])] * 4)
    outcome = ProtagonistRunner(world, provider, "fake").run()
    assert outcome == "stalled"
    assert any("tools" in m["content"] for m in provider.calls[-1]["messages"]
               if m["role"] == "user")


def test_timeout_ends_run():
    world = make_world()
    provider = FakeProvider([Completion(text=None, tool_calls=[tc("check_inbox")])
                             for _ in range(30)])
    outcome = ProtagonistRunner(world, provider, "fake").run()
    assert outcome == "timeout"
