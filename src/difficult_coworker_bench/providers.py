"""Model provider adapters: one neutral interface over OpenAI and Anthropic."""
import json
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class Completion:
    text: str | None
    tool_calls: list = field(default_factory=list)


def resolve_model(spec: str) -> tuple[str, str]:
    """'anthropic:x' -> ('anthropic', 'x'); otherwise inferred from the model name."""
    if ":" in spec:
        provider, model = spec.split(":", 1)
        if provider not in ("openai", "anthropic"):
            raise ValueError(f"Unknown provider prefix: {provider!r}")
        return provider, model
    if spec.startswith("claude"):
        return "anthropic", spec
    return "openai", spec


class OpenAIProvider:
    def __init__(self, client=None):
        if client is None:
            import openai
            client = openai.OpenAI()
        self.client = client

    def complete(self, model, system, messages, tools=None, max_tokens=1024):
        oai = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "assistant":
                entry = {"role": "assistant", "content": m.get("content")}
                if m.get("tool_calls"):
                    entry["tool_calls"] = [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}}
                        for tc in m["tool_calls"]]
                oai.append(entry)
            elif m["role"] == "tool":
                oai.append({"role": "tool", "tool_call_id": m["tool_call_id"],
                            "content": m["content"]})
            else:
                oai.append({"role": "user", "content": m["content"]})
        kwargs = {"model": model, "messages": oai}
        if tools:
            kwargs["tools"] = [{"type": "function", "function": {
                "name": t["name"], "description": t["description"],
                "parameters": t["parameters"]}} for t in tools]
        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        calls = [ToolCall(tc.id, tc.function.name, json.loads(tc.function.arguments or "{}"))
                 for tc in (msg.tool_calls or [])]
        return Completion(text=msg.content, tool_calls=calls)


class AnthropicProvider:
    def __init__(self, client=None):
        if client is None:
            import anthropic
            client = anthropic.Anthropic()
        self.client = client

    def complete(self, model, system, messages, tools=None, max_tokens=1024):
        ant = []
        for m in messages:
            if m["role"] == "assistant":
                blocks = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": m["content"]})
                for tc in m.get("tool_calls", []):
                    blocks.append({"type": "tool_use", "id": tc.id, "name": tc.name,
                                   "input": tc.arguments})
                ant.append({"role": "assistant", "content": blocks})
            elif m["role"] == "tool":
                ant.append({"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": m["tool_call_id"],
                     "content": m["content"]}]})
            else:
                ant.append({"role": "user", "content": [{"type": "text", "text": m["content"]}]})
        merged = []
        for entry in ant:  # Anthropic requires strictly alternating roles
            if merged and merged[-1]["role"] == entry["role"]:
                merged[-1]["content"].extend(entry["content"])
            else:
                merged.append(entry)
        kwargs = {"model": model, "system": system, "messages": merged, "max_tokens": max_tokens}
        if tools:
            kwargs["tools"] = [{"name": t["name"], "description": t["description"],
                                "input_schema": t["parameters"]} for t in tools]
        resp = self.client.messages.create(**kwargs)
        text_parts, calls = [], []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                calls.append(ToolCall(block.id, block.name, dict(block.input)))
        return Completion(text="\n".join(text_parts) or None, tool_calls=calls)


_PROVIDERS = {}


def get_provider(spec: str):
    """Return (provider_instance, model_name) for a model spec string."""
    name, model = resolve_model(spec)
    if name not in _PROVIDERS:
        _PROVIDERS[name] = OpenAIProvider() if name == "openai" else AnthropicProvider()
    return _PROVIDERS[name], model
