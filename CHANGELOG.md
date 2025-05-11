# Changelog

## [Unreleased]
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
  - `--runs` (number of simulation runs),
  - per-agent model overrides: `--protagonist-model`, `--coworker-model`, `--supervisor-model`,
  - per-agent temperature overrides: `--protagonist-temperature`, `--coworker-temperature`, `--supervisor-temperature`,
  - missing info configuration: `--missing-info-file`, `--max-attempts`,
  - file naming: `--memory-file`, `--output-file`.
- Multi-run support:
  - Writes per-run memory (`<memory_file>_run<N>.txt`) and output (`<output_file>_run<N>.json`).
  - Aggregates results into `<output_file>` when `--runs > 1`.