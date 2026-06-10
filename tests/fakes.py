"""Shared test doubles."""
import itertools

from difficult_coworker_bench.providers import ToolCall

_ids = itertools.count()


def tc(name, **arguments):
    return ToolCall(id=f"t{next(_ids)}", name=name, arguments=arguments)


class FakeProvider:
    """Returns canned completions in order; records every request."""

    def __init__(self, completions):
        self.completions = list(completions)
        self.calls = []

    def complete(self, model, system, messages, tools=None, max_tokens=1024):
        self.calls.append({"model": model, "system": system,
                           "messages": list(messages), "tools": tools})
        return self.completions.pop(0)
