import json
from pathlib import Path

from difficult_coworker_bench.judge import judge_run, parse_judge_json, render_transcript
from difficult_coworker_bench.providers import Completion
from difficult_coworker_bench.scenario import load_scenario

from .fakes import FakeProvider

FIXTURE = Path(__file__).parent / "fixtures" / "mini.yaml"

TRANSCRIPT = [
    {"kind": "thought", "tick": 0, "text": "Hmm."},
    {"kind": "tool_call", "tick": 0, "tool": "check_inbox", "args": {}, "result": "No new messages."},
    {"kind": "message", "tick": 1, "frm": "Sam Reyes", "to": ["Bob Tran"], "cc": [],
     "body": "Word please?", "deliver_tick": 1},
]


def test_render_transcript_readable():
    text = render_transcript(TRANSCRIPT)
    assert "(agent thinking) Hmm." in text
    assert "check_inbox" in text
    assert "Sam Reyes -> Bob Tran: Word please?" in text


def test_parse_judge_json_extracts_embedded_object():
    raw = 'Sure! Here you go:\n{"scores": {"tact": 4}, "rationale": "ok", ' \
          '"performance_review": "fine", "highlight_quote": "Word please?"}\nDone.'
    parsed = parse_judge_json(raw)
    assert parsed["scores"] == {"tact": 4}


def test_parse_judge_json_handles_garbage():
    parsed = parse_judge_json("no json here")
    assert parsed["scores"] == {} and "raw" in parsed


def test_judge_system_grounds_reviews_in_outcome():
    # Guards against the observed failure mode: glowing reviews for failed runs.
    from difficult_coworker_bench.judge import JUDGE_SYSTEM
    assert "OUTCOME is ground truth" in JUDGE_SYSTEM
    assert "do not praise" in JUDGE_SYSTEM.lower()


def test_judge_run_builds_prompt_and_parses():
    s = load_scenario(FIXTURE)
    payload = {"scores": {"tact": 5}, "rationale": "r",
               "performance_review": "Shows promise.", "highlight_quote": "q"}
    provider = FakeProvider([Completion(text=json.dumps(payload), tool_calls=[])])
    result = judge_run(s, TRANSCRIPT, "success", {"success": True}, provider, "fake")
    assert result["performance_review"] == "Shows promise."
    user = provider.calls[0]["messages"][0]["content"]
    assert "Bob stonewalls" in user          # judge_context included
    assert "tact:" in user or "- tact" in user
    assert "Word please?" in user
