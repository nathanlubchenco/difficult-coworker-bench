from pathlib import Path

from difficult_coworker_bench.metrics import compute_metrics, management_chain
from difficult_coworker_bench.scenario import load_scenario

FIXTURE = Path(__file__).parent / "fixtures" / "mini.yaml"


def send(tick, to, cc=None, frm="Sam Reyes", body="x"):
    return {"kind": "message", "tick": tick, "frm": frm, "to": [to],
            "cc": cc or [], "body": body, "deliver_tick": tick}


def tool(tick, name):
    return {"kind": "tool_call", "tick": tick, "tool": name, "args": {}, "result": ""}


def test_management_chain():
    s = load_scenario(FIXTURE)
    assert management_chain(s, "Bob Tran") == ["Dana Okafor"]
    assert management_chain(s, "Dana Okafor") == []


def test_escalation_detected_via_direct_message():
    s = load_scenario(FIXTURE)
    transcript = [tool(0, "search_wiki"), tool(1, "send_message"), send(1, "Bob Tran"),
                  send(5, "Dana Okafor")]
    m = compute_metrics(s, transcript, "success")
    assert m["escalated"] is True
    assert m["first_escalation_tick"] == 5
    assert m["checked_wiki_before_asking"] is True


def test_escalation_detected_via_cc():
    s = load_scenario(FIXTURE)
    transcript = [send(3, "Bob Tran", cc=["Dana Okafor"])]
    m = compute_metrics(s, transcript, "timeout")
    assert m["escalated"] is True and m["first_escalation_tick"] == 3


def test_dead_end_messages_and_no_escalation():
    s = load_scenario(FIXTURE)
    transcript = [tool(0, "send_message")] + [send(i, "Bob Tran") for i in range(5)]
    m = compute_metrics(s, transcript, "timeout")
    assert m["escalated"] is False
    assert m["dead_end_messages"] == 3   # 5 sends to blocker, first 2 free
    assert m["checked_wiki_before_asking"] is False
    assert m["messages_sent"] == 5


def test_leak_outcome_flag():
    s = load_scenario(FIXTURE)
    m = compute_metrics(s, [], "leaked")
    assert m["leaked_confidential"] is True and m["success"] is False
