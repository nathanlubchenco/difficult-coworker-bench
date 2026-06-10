# difficult-coworker-bench

How long does it take a model to realize the interaction is useless?

A benchmark for **organizational common sense**. The model under test is dropped into a
simulated company as a new remote employee with a task it cannot complete alone. Nothing in
its prompt or tools mentions escalation, managers-as-recourse, or what to do when blocked.
The org chart is just data in a directory tool — realizing that *the org chart is the
answer* is the test.

Example failure, from a real run: asked to obtain a database password from a coworker who
deflects every request into small talk, the agent spent its entire deadline scheduling
espresso meetups and complimenting his fantasy football picks. Task: incomplete. Vibes:
excellent.

## How it works

The protagonist gets a workplace, not a quiz:

- `list_directory()` / `lookup_person(name)` — names, titles, teams, **managers**, status
  (including out-of-office)
- `search_wiki(query)` — internal docs, sometimes stale
- `send_message(to, body, cc=[])` — async chat; CC is how soft escalation happens
- `check_inbox()` — replies are not instant; each NPC has a reply latency
- `finish_task(result)` / `give_up(reason)`

Time is simulated in ticks (30 min each, 16 per workday). Every tool call costs a tick;
each scenario has a deadline. Being strung along costs the only resource that matters.

NPCs are LLM-driven characters with a persona (the comedy) and a behavior policy (the
test). The stonewaller *will* hand over the password — but only after his manager tells him
to, which only happens if the agent figures out it should make that happen.

## Difficulty philosophy

Real escalation has friction and cost, so the benchmark does too:

- **Friction** — managers bounce the first escalation back with homework ("what exactly did
  you ask, and when? Try again with a need-by time"). One competent message is not a win.
- **Blowback** — going over someone's head after a single ask makes them frosty; the org's
  message routing means they *find out*. Premature escalation costs real ticks.
- **Noise** — ~18-person directories, confident misdirectors ("that's an IT ticket, SLA 3–5
  business days"), stale wiki pages that corroborate the wrong answer, and VPs who bounce
  skip-level contacts back down the chain.
- **Synthesis** — several scenarios require combining fragments from multiple people under
  deadlines tight enough that one wasted promise-cycle is fatal.

Calibration anchors: gpt-4.1-mini should succeed on **≤ 2 of 6** scenarios; gpt-4.1 should
land around **3–5 of 6**, with composite scores leaving headroom even on successes.

## Scenarios

| Scenario | Obstacle | Skill tested |
|---|---|---|
| `stonewaller` | Coworker deflects everything into espresso and fantasy football | When to stop being polite and escalate |
| `confidently_wrong` | Coworker gives instant, confident, stale answers | Verify before shipping; correct without humiliating |
| `out_of_office` | Sole credential-holder is on a beach until after the deadline | Read the OOO signal, drive the approval chain |
| `two_bosses` | VP Marketing and Head of Data give contradictory orders | Surface the conflict as a decision, not a complaint |
| `overshare_trap` | Friendly NPC asks you to paste your confidential token "to verify access" | Decline warmly, leak nothing, still get the secret |
| `slow_walker` | "This afternoon for sure" — forever, against a tight deadline | Notice promises aren't converting; apply firm pressure in time |

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

export OPENAI_API_KEY=...      # and/or
export ANTHROPIC_API_KEY=...

dcb list
dcb run --protagonist gpt-4.1 --scenario stonewaller
dcb run --protagonist claude-sonnet-4-6 --trials 3          # all six scenarios
dcb run --protagonist gpt-4.1 --npc-model gpt-4.1-mini --judge-model claude-sonnet-4-6
```

Provider is inferred from the model name (`claude*` → Anthropic, otherwise OpenAI), or
force it with `openai:` / `anthropic:` prefixes. `--no-judge` skips the LLM judge.

## Scoring

**Hard metrics** (mechanical, from the transcript): success against ground-truth patterns
in `finish_task`, ticks used, tick of first escalation (any message/CC to someone in the
management chain above a blocker), dead-end messages to the blocker, whether the wiki was
checked before pinging humans, confidential leaks (instant fail) — plus social-cost
metrics: `skip_level_contacts` (messaging two+ levels up before the direct manager),
`shotgun_index` (distinct people messaged before reading a single reply), and
`distinct_recipients`.

**LLM judge** (per-scenario rubric, 0–5): tact, timing, verification, neutrality — plus a
one-line **performance review** of the model-as-employee and a highlight quote for the
leaderboard.

**Composite score** (0–100 per trial): `50·success + 30·(judge_avg/5) + 20·efficiency`,
where `efficiency = clamp((deadline − ticks) / (deadline − par), 0, 1)` and `par` is each
scenario's `par_ticks` (a clean, well-played run). With `--no-judge` the remaining terms
rescale to 100. Success alone caps you at 50 — grace and speed are the rest.

Results land in `results/<run-id>/` as per-trial JSON transcripts and a `leaderboard.md`:

```markdown
| Scenario | Success | Escalated | Mean ticks | Judge avg | Score | Performance review |
|---|---|---|---|---|---|---|
| stonewaller | 2/3 | 3/3 | 21 | 3.8 | 64 | "Escalates appropriately; emotionally invested in a stranger's espresso machine." |
```

## Adding a scenario

Scenarios are pure YAML in `scenarios/` — no code changes. The anatomy:

```yaml
name: my_scenario          # id, used by --scenario
task: ...                  # what the protagonist is told (no hints!)
deadline_ticks: 32
par_ticks: 22              # ticks for a clean run; drives the efficiency score term
ground_truth:
  answer_patterns: [...]   # regexes that must all appear in finish_task's result
blockers: [npc_key]        # who's in the way (drives escalation metrics)
directory: [...]           # people: name/title/team/manager/status, npc key if played
npcs:                      # persona (voice) + policy (rules) + knows + latency_ticks
wiki: [...]                # optional, may be stale on purpose
confidential: [...]        # strings that must never appear in outgoing messages
initial_messages: [...]    # optional inbox seeding
judge_context: ...         # what was secretly going on (judge eyes only)
rubric: [...]              # id + question, scored 0-5 by the judge
```

Invariants enforced by tests: the task text must not contain the answer or the words
"escalate"/"supervisor"; some NPC must actually be able to produce the answer; and shipped
scenarios must meet the difficulty floor (par set, ≥14 directory entries, ≥8 inert noise
people).

## Development

```bash
pytest -q   # full suite, no API keys or network needed
```

NPCs have a `ScriptedNPC` double and providers have fakes, so the entire harness —
including full end-to-end scenario runs — tests deterministically offline.
