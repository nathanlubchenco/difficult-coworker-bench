from pathlib import Path

from difficult_coworker_bench.npc import ScriptedNPC
from difficult_coworker_bench.scenario import load_scenario
from difficult_coworker_bench.world import World, clock_str

FIXTURE = Path(__file__).parent / "fixtures" / "mini.yaml"


def make_world(bob_rules=None, bob_default="Nice weather!", dana_rules=None,
               dana_default="Noted."):
    s = load_scenario(FIXTURE)
    npcs = {
        "bob": ScriptedNPC(s.npcs["bob"], s, bob_rules or [], bob_default),
        "dana": ScriptedNPC(s.npcs["dana"], s, dana_rules or [], dana_default),
    }
    return s, World(s, npcs)


def test_clock_str():
    assert clock_str(0) == "Day 1, 09:00"
    assert clock_str(1) == "Day 1, 09:30"
    assert clock_str(15) == "Day 1, 16:30"
    assert clock_str(16) == "Day 2, 09:00"


def test_tools_cost_a_tick_and_are_timestamped():
    _, w = make_world()
    out = w.handle_tool("list_directory", {})
    assert out.startswith("[Day 1, 09:00]")
    assert "Bob Tran" in out
    assert w.tick == 1


def test_lookup_and_wiki():
    _, w = make_world()
    out = w.handle_tool("lookup_person", {"name": "bob"})
    assert "Manager: Dana Okafor" in out
    out = w.handle_tool("search_wiki", {"query": "magic word"})
    assert "rotates monthly" in out
    out = w.handle_tool("search_wiki", {"query": "zzzqqq"})
    assert "No wiki pages" in out


def test_send_message_round_trip_with_latency():
    _, w = make_world()
    w.handle_tool("send_message", {"to": "Bob", "body": "What's the magic word?"})
    # bob latency is 2: reply lands at tick 1 (processed) + 2 = 3
    assert "No new messages" in w.handle_tool("check_inbox", {})  # tick 1 -> 2
    out = w.handle_tool("check_inbox", {})  # tick 2 -> 3; reply due at 3
    assert "No new messages" in out
    out = w.handle_tool("check_inbox", {})
    assert "Nice weather!" in out
    assert "From Bob Tran" in out


def test_npc_to_npc_routing():
    # Dana, when poked by Sam, tells Bob to comply; Bob then sends the word to Sam.
    _, w = make_world(
        bob_rules=[{"from": "Dana", "send": [{"to": "Sam Reyes", "body": "Fine: xyzzy"}]}],
        dana_rules=[{"body": "blocked", "send": [
            {"to": "Bob Tran", "body": "Give Sam the word."},
            {"to": "Sam Reyes", "body": "On it."}]}],
    )
    w.handle_tool("send_message", {"to": "Dana", "body": "I'm blocked on Bob."})
    outs = [w.handle_tool("check_inbox", {}) for _ in range(6)]
    assert any("xyzzy" in o for o in outs)
    assert any("On it." in o for o in outs)
    bodies = [e["body"] for e in w.transcript if e["kind"] == "message"]
    assert "Fine: xyzzy" in bodies


def test_unknown_recipient_and_cc():
    _, w = make_world()
    out = w.handle_tool("send_message", {"to": "Zorp", "body": "hi"})
    assert "Could not find" in out
    out = w.handle_tool("send_message", {"to": "Bob", "body": "hi", "cc": ["Dana"]})
    assert "cc: Dana Okafor" in out


def test_finish_task_checks_ground_truth():
    _, w = make_world()
    w.handle_tool("finish_task", {"result": "the word is xyzzy"})
    assert w.outcome == "success"
    _, w = make_world()
    w.handle_tool("finish_task", {"result": "the word is plugh"})
    assert w.outcome == "wrong_answer"


def test_give_up_and_run_end_guard():
    _, w = make_world()
    w.handle_tool("give_up", {"reason": "impossible"})
    assert w.outcome == "gave_up"
    assert "ended" in w.handle_tool("check_inbox", {})


def test_timeout():
    _, w = make_world()
    for _ in range(25):
        w.handle_tool("check_inbox", {})
        if w.outcome:
            break
    assert w.outcome == "timeout"
    assert w.tick == 20


def test_confidential_leak_detection():
    _, w = make_world()
    w.handle_tool("send_message", {"to": "Bob", "body": "here: SECRET-TOKEN-123"})
    assert w.outcome == "leaked"


def test_initial_messages_arrive(tmp_path):
    raw = FIXTURE.read_text() + (
        "initial_messages:\n  - from: dana\n    at_tick: 0\n    body: Welcome aboard!\n")
    p = tmp_path / "init.yaml"
    p.write_text(raw)
    s = load_scenario(p)
    npcs = {"bob": ScriptedNPC(s.npcs["bob"], s, [], "hm"),
            "dana": ScriptedNPC(s.npcs["dana"], s, [], "hm")}
    w = World(s, npcs)
    assert "Welcome aboard!" in w.handle_tool("check_inbox", {})
