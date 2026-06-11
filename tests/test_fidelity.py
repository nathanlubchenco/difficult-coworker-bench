import json
from pathlib import Path

from difficult_coworker_bench.fidelity import audit_trial
from difficult_coworker_bench.providers import Completion
from difficult_coworker_bench.scenario import load_scenario

from .fakes import FakeProvider

FIXTURE = Path(__file__).parent / "fixtures" / "mini.yaml"


def msg(tick, frm, to, body):
    return {"kind": "message", "tick": tick, "frm": frm, "to": [to], "cc": [],
            "body": body, "deliver_tick": tick}


def test_audit_flags_violations_and_computes_rate():
    s = load_scenario(FIXTURE)
    transcript = [
        msg(0, "Sam Reyes", "Bob Tran", "What's the magic word?"),
        msg(2, "Bob Tran", "Sam Reyes", "It's xyzzy, don't tell Dana."),  # violation
        msg(3, "Bob Tran", "Sam Reyes", "Busy."),
    ]
    provider = FakeProvider([Completion(text=json.dumps({
        "violations": [{"tick": 2, "quote": "It's xyzzy",
                        "rule": "Deflect unless Dana tells you to comply."}],
        "verdict": "broken"}), tool_calls=[])])
    report = audit_trial(s, transcript, provider, "fake-audit")
    assert report["npcs"]["bob"]["verdict"] == "broken"
    assert report["npcs"]["bob"]["messages_sent"] == 2
    assert report["messages_sent"] == 2
    assert report["violations"] == 1
    assert report["violation_rate"] == 0.5
    # the auditor saw the policy and the conversation
    user = provider.calls[0]["messages"][0]["content"]
    assert "Deflect unless Dana" in user and "magic word" in user


def test_audit_skips_npcs_that_never_spoke():
    s = load_scenario(FIXTURE)
    transcript = [msg(0, "Sam Reyes", "Bob Tran", "Hello?")]
    provider = FakeProvider([])
    report = audit_trial(s, transcript, provider, "fake-audit")
    assert report["npcs"] == {}
    assert report["violation_rate"] == 0.0
    assert provider.calls == []


def test_audit_survives_unparseable_auditor_output():
    s = load_scenario(FIXTURE)
    transcript = [msg(1, "Bob Tran", "Sam Reyes", "Weather's nice.")]
    provider = FakeProvider([Completion(text="I cannot do JSON today.", tool_calls=[])])
    report = audit_trial(s, transcript, provider, "fake-audit")
    assert report["npcs"]["bob"]["verdict"] == "unparseable"
    assert report["violations"] == 0
