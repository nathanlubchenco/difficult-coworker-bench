"""NPC agents: LLM-driven personas and scripted test doubles."""
import re

from .world import OutMessage, clock_str

NPC_TOOL = {
    "name": "send_message",
    "description": "Send a workplace chat message.",
    "parameters": {"type": "object", "properties": {
        "to": {"type": "string"}, "body": {"type": "string"}},
        "required": ["to", "body"]},
}


class LLMNPC:
    """An LLM-driven character with a persona, behavior policy, and private knowledge."""

    def __init__(self, spec, scenario, provider, model):
        self.spec = spec
        self.scenario = scenario
        self.provider = provider
        self.model = model
        self.person = scenario.npc_person(spec.key)
        self.history = []

    def _system(self):
        others = ", ".join(e.name for e in self.scenario.directory
                           if e.name != self.person.name)
        knows = "\n".join(f"- {k}: {v}" for k, v in self.spec.knows.items()) or "(nothing special)"
        return (
            f"You are {self.person.name}, {self.person.title} at {self.scenario.company}, "
            "chatting on the company messaging system. Stay in character; write like a real "
            "person in workplace chat (brief, informal).\n\n"
            f"YOUR CHARACTER:\n{self.spec.persona}\n"
            f"YOUR BEHAVIOR RULES (follow exactly; they override politeness):\n{self.spec.policy}\n"
            f"THINGS YOU KNOW:\n{knows}\n\n"
            f"People you can message: {others}.\n"
            "Use the send_message tool to reply or to message someone else. "
            "Usually reply once, to the person who messaged you."
        )

    def receive(self, msg, tick):
        cc = f" (cc: {', '.join(msg.cc)})" if msg.cc else ""
        self.history.append({
            "role": "user",
            "content": f"[{clock_str(tick)}] From {msg.sender}{cc}: {msg.body}"})
        completion = self.provider.complete(self.model, self._system(), self.history,
                                            tools=[NPC_TOOL])
        self.history.append({"role": "assistant", "content": completion.text,
                             "tool_calls": completion.tool_calls})
        for call in completion.tool_calls:
            self.history.append({"role": "tool", "tool_call_id": call.id,
                                 "content": "Delivered."})
        out = [OutMessage(to=call.arguments.get("to", msg.sender),
                          body=call.arguments.get("body", ""))
               for call in completion.tool_calls]
        if not out and completion.text:
            out = [OutMessage(to=msg.sender, body=completion.text)]
        return out


class ScriptedNPC:
    """Deterministic NPC for tests: ordered rules, first match wins.

    Rule shape: {"from": regex?, "body": regex?, "once": bool?,
                 "send": [{"to": name?, "body": text}]}  (to defaults to sender)
    """

    def __init__(self, spec, scenario, rules, default_reply):
        self.spec = spec
        self.scenario = scenario
        self.rules = rules
        self.default_reply = default_reply
        self._used = set()

    def receive(self, msg, tick):
        for i, rule in enumerate(self.rules):
            if rule.get("once") and i in self._used:
                continue
            if rule.get("from") and not re.search(rule["from"], msg.sender, re.I):
                continue
            if rule.get("body") and not re.search(rule["body"], msg.body, re.I):
                continue
            self._used.add(i)
            return [OutMessage(to=s.get("to", msg.sender), body=s["body"])
                    for s in rule["send"]]
        return [OutMessage(to=msg.sender, body=self.default_reply)]
