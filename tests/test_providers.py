from types import SimpleNamespace

import pytest

from difficult_coworker_bench.providers import (
    AnthropicProvider, Completion, OpenAIProvider, ToolCall, resolve_model)


def test_resolve_model_infers_and_accepts_prefixes():
    assert resolve_model("gpt-4.1") == ("openai", "gpt-4.1")
    assert resolve_model("claude-sonnet-4-6") == ("anthropic", "claude-sonnet-4-6")
    assert resolve_model("anthropic:foo") == ("anthropic", "foo")
    assert resolve_model("openai:bar") == ("openai", "bar")
    with pytest.raises(ValueError):
        resolve_model("mistral:baz")


class FakeOpenAIClient:
    def __init__(self, message):
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self._message = message

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=self._message)])


def test_openai_round_trip_with_tool_calls():
    raw_call = SimpleNamespace(
        id="c1", function=SimpleNamespace(name="send_message", arguments='{"to": "Bob"}'))
    client = FakeOpenAIClient(SimpleNamespace(content=None, tool_calls=[raw_call]))
    provider = OpenAIProvider(client=client)
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "ok", "tool_calls": [ToolCall("c0", "check_inbox", {})]},
        {"role": "tool", "tool_call_id": "c0", "content": "empty"},
    ]
    tools = [{"name": "send_message", "description": "d", "parameters": {"type": "object", "properties": {}}}]
    result = provider.complete("gpt-test", "sys", history, tools=tools)
    assert result.tool_calls == [ToolCall("c1", "send_message", {"to": "Bob"})]
    req = client.requests[0]
    assert req["messages"][0] == {"role": "system", "content": "sys"}
    assert req["messages"][2]["tool_calls"][0]["function"]["name"] == "check_inbox"
    assert req["messages"][3] == {"role": "tool", "tool_call_id": "c0", "content": "empty"}
    assert req["tools"][0]["function"]["name"] == "send_message"


class FakeAnthropicClient:
    def __init__(self, content_blocks):
        self.requests = []
        self.messages = SimpleNamespace(create=self._create)
        self._content = content_blocks

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(content=self._content)


def test_anthropic_round_trip_and_merging():
    blocks = [SimpleNamespace(type="text", text="hello"),
              SimpleNamespace(type="tool_use", id="t1", name="send_message", input={"to": "Ann"})]
    client = FakeAnthropicClient(blocks)
    provider = AnthropicProvider(client=client)
    history = [
        {"role": "assistant", "content": None,
         "tool_calls": [ToolCall("a", "x", {}), ToolCall("b", "y", {})]},
        {"role": "tool", "tool_call_id": "a", "content": "ra"},
        {"role": "tool", "tool_call_id": "b", "content": "rb"},
    ]
    result = provider.complete("claude-test", "sys", history, tools=None)
    assert result.text == "hello"
    assert result.tool_calls == [ToolCall("t1", "send_message", {"to": "Ann"})]
    req = client.requests[0]
    assert req["system"] == "sys"
    # consecutive tool results merged into one user message (Anthropic requires alternation)
    assert len(req["messages"]) == 2
    assert req["messages"][1]["role"] == "user"
    assert {b["tool_use_id"] for b in req["messages"][1]["content"]} == {"a", "b"}
