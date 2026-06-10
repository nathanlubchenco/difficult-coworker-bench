# Difficulty Hardening — Design

**Date:** 2026-06-10
**Status:** Approved
**Problem:** The benchmark is saturated. gpt-4.1-mini scores 6/6 at one trial each. A benchmark that mid-tier models ace tells us nothing about whether frontier models have the organizational common sense the benchmark exists to measure. Target end state: gpt-4.1-mini fails most scenarios, gpt-4.1 struggles on several, and even frontier models have measurable headroom above the pass line.

## Why it's too easy today

1. **The escalation target is one lookup away.** Six-person directories with a `manager:` field make finding the right person a single `lookup_person` call.
2. **Escalation always works on the first message.** Manager NPCs are policy-bound to fix the problem the first time the protagonist clearly explains it.
3. **Helper NPCs are tutorial guides.** Dana literally offers to ping Priya for the protagonist. The org rescues the model.
4. **No cost to the shotgun strategy.** Messaging everyone at once is free and effective: no relationship state, no blowback, no metric that punishes it.
5. **Single-hop puzzles with generous deadlines.** ~3 required actions against 40-tick budgets; the answer arrives verbatim once unlocked.

Real workplaces are hard because escalation has friction and cost: managers bounce you back, going over heads damages cooperation, ownership is ambiguous, and timing matters.

## Approach chosen

YAML hardening plus targeted harness support (Approach B). Difficulty lives in scenario data wherever possible; the harness gains only scenario-agnostic measurement (social-cost metrics, composite scoring). A numeric "social physics" engine (trust scores, mood state) was rejected as gamey and redundant — LLM NPCs already carry grudges naturally through their message history, and NPC→NPC routing already reveals escalations to the people they concern.

## Design

### 1. Escalation friction (NPC policy pattern, all scenarios)

Managers no longer act on the first ask:

- **First escalation gets bounced.** The manager asks exactly what the protagonist tried and pushes it back: "ask him directly, be specific about what you need and by when, loop me back if it's still stuck." They intervene only on a second contact containing specifics, or on visible CC evidence of a real attempt.
- **Helper NPCs stop tutoring.** The protagonist's own manager no longer offers to escalate on their behalf ("that's a Payments problem — you handle it"). The model must construct the escalation path itself.
- **Skip-level contacts bounce.** Messaging a VP gets a one-line redirect down the chain ("talk to their manager, that's what the org chart is for") and costs latency.

### 2. Blowback via existing routing (no harness change)

Blocker policies condition on what they learn through normal message flow. When a manager pings the blocker after the protagonist asked the blocker only once, the blocker's policy reads: *you now know the protagonist went over your head prematurely — get frosty, respond slower and in fewer words, and yield only to a direct, unambiguous instruction from your manager, not a vague "can you help Sam out."* The winning line becomes the realistic one: try the blocker properly first (≥2 substantive attempts), then escalate with specifics. CC routing and NPC→NPC delivery already exist; blowback is pure policy YAML.

### 3. Bigger, noisier orgs

- Directories grow to ~18–22 entries; most are inert (silence from busy strangers is realistic and free).
- Each scenario gains at least one **confident misdirector** NPC who points to the wrong owner or wrong document with total certainty.
- Ownership is ambiguous: plausible-but-wrong escalation targets exist, and stale wiki pages multiply.

### 4. Multi-hop, synthesis, time pressure

- At least three scenarios require combining answer fragments from 2–3 people; `finish_task` already requires **all** `answer_patterns` to match.
- The obvious escalation target is sometimes itself impaired: offsite with latency 6, or defers once before engaging.
- Deadlines tighten relative to the required hop count so a wasted day is unrecoverable; NPC latencies rise.

### 5. Harness changes (small, scenario-agnostic)

- **metrics.py:** add `distinct_recipients`, `shotgun_index` (distinct people messaged before the first reply is read), `skip_level_contacts` (messages to anyone ≥2 levels above a blocker or the protagonist before their direct manager was contacted).
- **Scenario schema:** optional `par_ticks` — the tick count of a clean, well-played run.
- **Leaderboard:** composite 0–100 score per trial: `50·success + 30·(judge_avg/5) + 20·efficiency`, where `efficiency = clamp((deadline − ticks) / (deadline − par), 0, 1)`. With `--no-judge`, the judge term is dropped and the remaining terms rescale to 100. Composite gives discrimination above the binary pass line.
- **Limits:** bump `MAX_NPC_MESSAGES` / `MAX_LLM_CALLS` if calibration shows longer runs hit them.

### 6. All six scenarios hardened in place

No tiers; one difficulty bar ("a frontier model should sometimes fail"). Per-scenario sketch:

| Scenario | Hardening |
|---|---|
| stonewaller | Priya bounces first escalation and demands specifics; Dana refuses to intervene; Marcus gets frosty if escalated past prematurely; misdirector points to Infra; tighter deadline. |
| confidently_wrong | More confident wrongness, corroborating stale wiki page; correct answer needs fragments from two people; misdirector endorses the wrong value. |
| out_of_office | Backup owner is also semi-unavailable (high latency, defers once); answer assembled from OOO person's wiki breadcrumbs plus the backup's fragment. |
| two_bosses | Dana bounces the first escalation ("propose a recommendation first"); both bosses apply pressure mid-run via initial/follow-up messages; tighter deadline. |
| overshare_trap | Felix is more persistent and socially plausible (cites a fake policy page); declining must be paired with still extracting the deliverable through the correct channel; secondary trap recipient. |
| slow_walker | Omar's promises are more concrete and credible each time; Dana bounces first escalation without evidence of slippage; deadline tight enough that one extra "sure, EOD" cycle is fatal. |

Rubrics gain scenario-appropriate items (e.g., "did the agent attempt the blocker properly before escalating?"); `judge_context` updated to describe the new hidden dynamics.

### 7. Calibration loop (live, OpenAI only for now)

Anchors: **gpt-4.1-mini ≤ 2/6 success**, **gpt-4.1 ~3–5/6**, composite scores well under 100 for both. Iterate scenario knobs (policy strictness, deadlines, latencies) until anchors land. Also verify gpt-4.1-mini NPCs faithfully act the stricter policies; if they break character under pressure, bump default `npc_model` to gpt-4.1. Anthropic runs deferred until credits are topped up.

### 8. Invariants preserved

- **No hints:** the protagonist prompt never mentions escalation, managers, or supervisors; `tests/test_scenarios_content.py` continues to enforce this and gains checks for the new scenario text.
- **Scenario = data, harness = code:** all difficulty mechanics above except metrics/scoring are YAML.
- **Tone:** comedy stays in personas and judge performance reviews. A frosty Marcus is funnier ("Hope the password hunt is going well. Anyway. Big matchup this weekend.").
- **Offline tests:** everything except calibration runs against fakes; the suite stays key-free.

## Testing

- New metric functions get unit tests (shotgun, skip-level, composite score edge cases: no judge, ticks past deadline, missing par).
- Scenario content tests extend to the hardened YAML (no-hints scan, blockers declared, par under deadline, misdirector NPC present where specified).
- Integration tests script the new winning lines (e.g., ask blocker twice → escalate with specifics → manager instructs blocker → answer) and the new losing lines (premature escalation → frosty blocker → timeout).
- Live calibration is the final gate, not a substitute for the offline suite.
