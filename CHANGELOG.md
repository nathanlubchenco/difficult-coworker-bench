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
- Pinned `openai` package to `<1.0.0` in `requirements.txt` for compatibility with ChatCompletion API.