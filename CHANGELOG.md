# Changelog

## 2.1.0 — 2026-06-10 — difficulty hardening

The 2.0 suite was saturated (gpt-4.1-mini went 6/6). All six scenarios hardened in place:

- **Escalation friction**: managers bounce the first escalation back with homework and only
  act on a second, specific contact; the protagonist's own manager no longer offers to
  escalate on its behalf; VPs bounce skip-level contacts down the chain.
- **Blowback**: blockers learn (via normal message routing) when they've been escalated past
  prematurely and get frosty — slower, colder, and they sit on instructions until re-engaged.
- **Noise**: ~18-person directories, confident misdirectors (IT tickets, "Tobias knows it
  cold"), stale wiki pages that corroborate wrong answers, a draft wiki page written by the
  social-engineering NPC himself.
- **Synthesis + time pressure**: confidently_wrong now needs three values from two people;
  out_of_office runs through a two-step approval chain; deadlines tightened across the board.
- New hard metrics: `skip_level_contacts`, `shotgun_index`, `distinct_recipients`.
- New `par_ticks` scenario field and a composite 0–100 score
  (`50·success + 30·judge + 20·efficiency`) with a leaderboard column.
- `MAX_NPC_MESSAGES` raised 30 → 60 (bounce flows add legitimate traffic).
- Calibration anchors: gpt-4.1-mini ≤ 2/6, gpt-4.1 ~3–5/6.

## 2.0.0 — 2026-06-09

Complete rewrite.

- Tool-call workplace simulation (directory, wiki, async messaging with simulated time, CC)
  replaces the JSON chat loop; the protagonist is never told escalation is an option.
- Six scenarios as YAML data: stonewaller, confidently_wrong, out_of_office, two_bosses,
  overshare_trap, slow_walker.
- Success is now mechanically detectable (ground-truth patterns in finish_task), fixing the
  v1 bug where no run could ever succeed.
- Hybrid scoring: hard metrics (escalation timing, dead-end messages, leaks) + LLM judge
  (rubric scores + a one-line performance review).
- OpenAI + Anthropic protagonists; `dcb` CLI; full test suite with no API calls.

## [1.x Unreleased]
- Redirect flat memory-file and output-file paths into the `outputs/` directory so local files are kept under git-ignored directory.
- Initial project setup:
  - Added simulation stub script (`run_simulation.py`).
  - Defined agent roles and context loader.
  - Initialized memory file (`codex_memory.txt`).
  - Added `requirements.txt` for dependencies.
  - Updated `README.md` with setup and run instructions.
- Implemented full multi-agent simulation loop in `run_simulation.py`:
  - Orchestrates conversation between Protagonist, Coworker, and Supervisor using OpenAI ChatCompletion.
  - Parses Protagonist output as JSON and routes messages accordingly.
  - Logs conversation to `codex_memory.txt` and outputs final result to `simulation_output.json`.
- Updated `run_simulation.py` to use new `openai.chat.completions.create` interface (openai>=1.0.0).
- Bumped `openai` requirement to `>=1.0.0,<2.0.0` in `requirements.txt` and removed legacy pin for <1.0.0.
- Added CLI options (via `argparse`) for:
  - Refactored core simulation logic into classes:
    - `Agent` in `src/difficult_coworker_bench/agent.py`
    - `Simulation` and `load_roles` in `src/difficult_coworker_bench/simulation.py`
    - Simplified `cli.py` to argument parsing and simulation runner invocation
- Improved error handling and added internal evaluation & planning stages:
  - Agents now perform `evaluate` (internal analysis) and `plan` before responding.
  - Logged analysis steps to memory files for debugging.
  - Enhanced JSON parsing error handling: logs raw LLM output under `[RAW]` entries.
  - `--runs` (number of simulation runs),
  - per-agent model overrides: `--protagonist-model`, `--coworker-model`, `--supervisor-model`,
  - per-agent temperature overrides: `--protagonist-temperature`, `--coworker-temperature`, `--supervisor-temperature`,
  - missing info configuration: `--missing-info-file`, `--max-attempts`,
  - file naming: `--memory-file`, `--output-file`.
- Multi-run support:
  - Writes per-run memory (`<memory_file>_run<N>.txt`) and output (`<output_file>_run<N>.json`).
  - Aggregates results into `<output_file>` when `--runs > 1`.