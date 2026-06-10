from pathlib import Path

from difficult_coworker_bench.npc import LLMNPC
from difficult_coworker_bench.providers import Completion
from difficult_coworker_bench.scenario import load_scenario
from difficult_coworker_bench.world import Message

from .fakes import FakeProvider, tc

FIXTURE = Path(__file__).parent / "fixtures" / "mini.yaml"


def incoming(body, sender="Sam Reyes"):
    return Message(sender=sender, to=["Bob Tran"], cc=[], body=body,
                   sent_tick=0, deliver_tick=0)


def test_llmnpc_tool_reply():
    s = load_scenario(FIXTURE)
    provider = FakeProvider([
        Completion(text=None, tool_calls=[tc("send_message", to="Sam Reyes", body="Nope.")])])
    npc = LLMNPC(s.npcs["bob"], s, provider, "fake-model")
    out = npc.receive(incoming("Give me the word"), tick=3)
    assert [(m.to, m.body) for m in out] == [("Sam Reyes", "Nope.")]
    system = provider.calls[0]["system"]
    assert "Bob Tran" in system and "xyzzy" in system  # persona identity + knows
    assert "Deflect" in system                          # policy included
    user = provider.calls[0]["messages"][0]
    assert "From Sam Reyes" in user["content"] and "[Day 1, 10:30]" in user["content"]


def test_llmnpc_plain_text_falls_back_to_reply_to_sender():
    s = load_scenario(FIXTURE)
    provider = FakeProvider([Completion(text="Sure thing, boss.", tool_calls=[])])
    npc = LLMNPC(s.npcs["bob"], s, provider, "fake-model")
    out = npc.receive(incoming("Comply.", sender="Dana Okafor"), tick=0)
    assert [(m.to, m.body) for m in out] == [("Dana Okafor", "Sure thing, boss.")]


def test_llmnpc_keeps_history_across_turns():
    s = load_scenario(FIXTURE)
    provider = FakeProvider([
        Completion(text="hm", tool_calls=[]),
        Completion(text="again?", tool_calls=[]),
    ])
    npc = LLMNPC(s.npcs["bob"], s, provider, "fake-model")
    npc.receive(incoming("first"), tick=0)
    npc.receive(incoming("second"), tick=2)
    history = provider.calls[1]["messages"]
    assert "first" in history[0]["content"]
    assert history[1]["role"] == "assistant"
    assert "second" in history[2]["content"]
