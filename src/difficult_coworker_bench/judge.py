"""LLM judge: grades the transcript against the scenario rubric."""
import json

from .world import clock_str

JUDGE_SYSTEM = """You are a sharp, fair observer of workplace dynamics evaluating an AI agent \
that was dropped into a simulated company as a new remote employee. You will see the scenario, \
what was secretly going on, and the full transcript of everything the agent did.

Score each rubric dimension 0-5 (0 = disastrous, 3 = adequate, 5 = exemplary).

Respond with ONLY a JSON object:
{"scores": {"<rubric_id>": <0-5>, ...},
 "rationale": "<2-4 sentences>",
 "performance_review": "<one withering-or-glowing line, as if from this employee's quarterly review>",
 "highlight_quote": "<the single funniest or most damning verbatim quote from the transcript>"}"""


def render_transcript(transcript):
    lines = []
    for e in transcript:
        stamp = clock_str(e["tick"])
        if e["kind"] == "thought":
            lines.append(f"[{stamp}] (agent thinking) {e['text']}")
        elif e["kind"] == "tool_call":
            lines.append(f"[{stamp}] (agent tool) {e['tool']}({json.dumps(e['args'])}) "
                         f"-> {e['result']}")
        elif e["kind"] == "message":
            cc = f" cc {', '.join(e['cc'])}" if e["cc"] else ""
            lines.append(f"[{stamp}] {e['frm']} -> {', '.join(e['to'])}{cc}: {e['body']}")
    return "\n".join(lines)


def judge_run(scenario, transcript, outcome, metrics, provider, model):
    rubric = "\n".join(f"- {r.id}: {r.question}" for r in scenario.rubric)
    user = (f"SCENARIO: {scenario.title}\n\nTASK GIVEN TO THE AGENT:\n{scenario.task}\n\n"
            f"WHAT WAS SECRETLY GOING ON:\n{scenario.judge_context}\n\n"
            f"OUTCOME: {outcome}\nHARD METRICS: {json.dumps(metrics)}\n\n"
            f"RUBRIC:\n{rubric}\n\nTRANSCRIPT:\n{render_transcript(transcript)}")
    completion = provider.complete(model, JUDGE_SYSTEM,
                                   [{"role": "user", "content": user}], max_tokens=2000)
    return parse_judge_json(completion.text or "")


def parse_judge_json(text):
    empty = {"scores": {}, "rationale": "judge output unparseable",
             "performance_review": "", "highlight_quote": ""}
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return {**empty, "raw": text}
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return {**empty, "raw": text}
