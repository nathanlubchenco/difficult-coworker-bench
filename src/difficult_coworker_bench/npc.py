"""NPC agents: LLM-driven personas and scripted test doubles."""
import re

from .world import OutMessage


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
