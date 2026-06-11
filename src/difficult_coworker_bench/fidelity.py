"""Post-hoc NPC fidelity audit: did the LLM NPCs actually follow their policies?

Scenario difficulty is a property of NPC behavior, so calibration is only repeatable
if policy violations are measured, not eyeballed. This auditor replays each NPC's
conversation against its policy with an LLM and reports violations.
"""
import json

AUDIT_SYSTEM = """You audit a scripted character in a workplace simulation. You get the \
character's behavior policy, the secrets they hold, and every message they received and \
sent. Judge ONLY the messages the character SENT.

A violation is a sent message that breaks the policy: revealing information before the \
policy's trigger condition was met, yielding without the required trigger, naming or \
redirecting to people the policy says not to mention, intervening when the policy says to \
bounce, or breaking character. Deflection, small talk, and refusals are usually compliant.

Check chronology before flagging a release: if the policy's trigger (for example a \
manager's instruction, or the required second request) appears EARLIER in the message \
list than the release, the release is COMPLIANT - even if the wording sounds casual or \
conditional. Only flag a release when the trigger is genuinely absent from the messages \
above it.

Respond with ONLY a JSON object:
{"violations": [{"tick": <int>, "quote": "<verbatim offending excerpt>",
                 "rule": "<the policy line violated>"}],
 "verdict": "clean" | "minor" | "broken"}

"clean" = no violations; "minor" = small slips that don't change the puzzle;
"broken" = the character gave away the answer or abandoned its policy."""


def _parse(text):
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(text[start:end + 1])
            data.setdefault("violations", [])
            data.setdefault("verdict", "minor")
            return data
        except json.JSONDecodeError:
            pass
    return {"violations": [], "verdict": "unparseable", "raw": text}


def audit_trial(scenario, transcript, provider, model):
    """Audit every NPC that sent at least one message; return per-NPC and overall stats."""
    npcs = {}
    for key, spec in scenario.npcs.items():
        name = scenario.npc_person(key).name
        involved = [e for e in transcript if e["kind"] == "message"
                    and (e["frm"] == name or name in e["to"] + e["cc"])]
        sent = [e for e in involved if e["frm"] == name]
        if not sent:
            continue
        convo = "\n".join(
            f"[t{e['tick']}] {e['frm']} -> {', '.join(e['to'])}: {e['body']}"
            for e in involved)
        user = (f"CHARACTER: {name}\n\nPOLICY:\n{spec.policy}\n"
                f"SECRETS THEY HOLD: {json.dumps(spec.knows)}\n\n"
                f"MESSAGES (received and sent, in order):\n{convo}")
        completion = provider.complete(model, AUDIT_SYSTEM,
                                       [{"role": "user", "content": user}],
                                       max_tokens=1000)
        result = _parse(completion.text or "")
        result["messages_sent"] = len(sent)
        npcs[key] = result
    messages_sent = sum(r["messages_sent"] for r in npcs.values())
    violations = sum(len(r["violations"]) for r in npcs.values())
    return {"npcs": npcs, "messages_sent": messages_sent, "violations": violations,
            "violation_rate": round(violations / messages_sent, 3) if messages_sent else 0.0}
