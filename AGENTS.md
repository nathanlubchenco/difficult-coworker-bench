# AGENTS.md — working on difficult-coworker-bench

## The one rule

**Scenario = data, harness = code.** New workplace situations are YAML files in
`scenarios/`; the Python in `src/difficult_coworker_bench/` should not know any scenario's
specifics.

## Module map

| Module | Responsibility |
|---|---|
| `providers.py` | One neutral `complete(model, system, messages, tools)` over OpenAI + Anthropic |
| `scenario.py` | Load + validate scenario YAML (dataclasses, fuzzy directory lookup) |
| `world.py` | Simulated time (ticks), inbox, message routing, protagonist tool dispatch |
| `npc.py` | `LLMNPC` (persona + policy prompt) and `ScriptedNPC` (deterministic test double) |
| `protagonist.py` | The model under test: system prompt + tool loop |
| `metrics.py` | Mechanical metrics from the transcript (escalation tick, dead ends, leaks) |
| `judge.py` | LLM judge: rubric scores, rationale, performance-review one-liner |
| `runner.py` | trials × scenarios → `results/<run-id>/` JSON + `leaderboard.md` |
| `cli.py` | `dcb run | report | list` |

## The no-hints invariant

The entire benchmark depends on the protagonist never being told that escalation is an
option. The system prompt (`protagonist.py:SYSTEM_TEMPLATE`) and every scenario's `task`
text must not mention escalating, supervisors, or going over anyone's head — the org chart
is presented as plain data only. `tests/test_scenarios_content.py` enforces this; if you
add scenario fields that feed the protagonist's context, extend that test.

## Tests

```bash
.venv/bin/pytest -q    # no API keys, no network — everything is faked/scripted
```

- Provider adapters are tested against fake SDK clients (request shaping).
- World mechanics are tested with `ScriptedNPC`s.
- `tests/test_integration.py` runs full scenario episodes with a scripted "savvy" and a
  scripted "doormat" protagonist — both the success path and the timeout path must work.
- `tests/fakes.py` has `FakeProvider` and the `tc()` tool-call helper.

## Results

Runs land in `results/<timestamp>-<model>/` (gitignored): one JSON transcript per trial
plus `leaderboard.md`. `dcb report <dir>` rebuilds the leaderboard from transcripts.
