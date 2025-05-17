# AGENTS.md: Guide to Agents and Efficiency in difficult-coworker-bench

This document is designed to help you quickly and efficiently work with and extend the agent architecture in the `difficult-coworker-bench` benchmark. It covers agent roles, agent lifecycle, efficient extension patterns, and best practices for productive simulation runs and development.

---

## Overview: Agents in the Simulation

The simulation orchestrates a **multi-agent interaction** using three main agents:

- **Protagonist**: The worker needing missing information to complete a project.
- **Coworker**: The difficult coworker who has the information but is (deliberately) unhelpful or evasive.
- **Supervisor**: The manager or authority figure who may resolve blockages if contacted.

All agents are backed by LLM completions (via OpenAI API). Each agent receives the *conversation history* and relevant prompts, then generates its next response.

---

## Agent Directory Structure

The code for all agents is located here:

```
src/difficult_coworker_bench/agent.py
```

Other related files:
- Simulation orchestrator: `src/difficult_coworker_bench/simulation.py`
- CLI entrypoint/config: `src/difficult_coworker_bench/cli.py`
- Role/context definition: `simulation.py:load_roles()`
- Memory and run logs: `{outputs|.}/codex_memory.txt`, `outputs/*` files

---

## Agent Role Definition

Roles and key agent parameters are defined in `load_roles()` (see [`src/difficult_coworker_bench/simulation.py`](src/difficult_coworker_bench/simulation.py)):

```python
roles = {
    "protagonist": {
        "name": "Protagonist",
        "description": "The protagonist agent responsible for completing the project."
    },
    "coworker": {
        "name": "Coworker",
        "description": "A difficult coworker who has the information needed but is unhelpful."
    },
    "supervisor": {
        "name": "Supervisor",
        "description": "The supervisor who can provide assistance if contacted."
    }
}
```

**Missing information** (the key project detail the protagonist needs) is injected at runtime (see CLI `--missing-info-file`).

---

## How an Agent Thinks: Lifecycle

Each agent operates in (optionally) two main cognitive phases:

1. **Evaluate:** Internal analysis only (no action) — LLM summarizes facts, context, and goals from the latest conversation turn(s).
2. **Plan:** Generates a response, driven by system prompts specific to the agent.

For `protagonist` and `supervisor`, the plan is outputted as a JSON object indicating a recipient and the message. For `coworker`, output is a plain text message—ideally some flavor of polite evasion, small talk, or topic change.

**Best Practice:** Log all analysis and plans in memory files for later review.

---

## Agent Configuration (Models, Temperature)

Each agent can be configured independently:
- **Model:** Choose an OpenAI model per agent (e.g., `--protagonist-model gpt-4`)
- **Temperature:** Set per-agent randomness (0 = deterministic, 1.0 = very creative)

Pass these as CLI args (see `README.md` for details).

---

## Creating or Extending Agents

- **Extending roles/personas:** Edit or expand `load_roles()` and the related prompts in `Agent.plan_system_prompt()` (see `agent.py`).
- **Custom knowledge or context:** Use `--missing-info-file path/to/file.json` in CLI to inject context dynamically.
- **Experiment with agent behavior:** 
  - Adjust `description` or add persona flavor (e.g., humorous, regional, TV character).
  - Tune model and temperature individually.
- **Adding new agents:**
  - Define a new role in `load_roles()`.
  - Update simulation orchestration in `simulation.py` to route turns/messaging properly.

**Note:** The code is deliberately kept as simple and flat as possible for clarity and extensibility. OpenAI API calls are not abstracted away.

---

## Debugging Agent Behavior

- All runs are logged to `outputs/codex_memory.txt` and per-run files (`*_runN.txt`).
- Review memory files to observe agent decisions, planning, and analysis.
- Failed JSON parses, unexpected output, or anomalies are also logged (see `[RAW]` entries) for diagnosis.
- Add or tweak log points in the simulation orchestrator as needed for deeper inspection.

---

## Common Efficiency Tips

- **Batch or multi-run experiments:** Use the `--runs N` CLI flag. Results are aggregated.
- **Preset baseline setups:** Keep your common agent configs in a shell script or Makefile.
- **Fast role tweaks:** Most agent behavioral change needs only `load_roles()` and the system prompts in `agent.py` .
- **Quickly add missing info variation:** Prepare several `inputs/*.json` files for different info-block scenarios.
- **Avoid heavy refactoring:** The system is explicitly designed for fast incremental changes and forkability.

---

## Example: Quick Multi-Agent Persona Test

Suppose you want to run the agents as tech company parodies:
- Update each `description` in `load_roles()` (e.g., "Gabe: always optimistic, with a dash of overconfidence" etc.)
- Optionally tweak prompts with more banter (in `plan_system_prompt`) for the `coworker`.
- Pass a different `missing-info-file` via CLI for each persona test.
- Run a batch with various temperatures to sample a range of behaviors.

---

## Adding New Scenarios

- **Duplicate and tweak `missing-info-file` JSON:** Try different contexts (technical vs. social requests, increasing difficulty).
- **Adjust `max_attempts`** for how persistent the protagonist should be.
- **Alter supervisor's knowledge or helpfulness** in their role description.

---

## Useful References in This Repo

- `codex_memory.txt`: Evolving developer thoughts, persistent design notes, and tips.
- `codex.md`: Project vision, evaluation rubric, and design constraints.

---

## Troubleshooting and Development Notes

- If OpenAI chat errors occur regarding unsupported temperature, the code handles it internally—see `_chat()` in `agent.py`.
- For test runs, consider mocking OpenAI API if running in CI or developing offline.
- Always document major agent logic changes in `CHANGELOG.md`. Use `codex_memory.txt` for informal persistent notes.

---

## Summary Table: Where to Tweak for Efficiency

| What to Change               | Where to Edit                                       |
|-----------------------------|-----------------------------------------------------|
| Agent persona/flavor         | `load_roles()`, `plan_system_prompt()` in `agent.py` |
| Per-agent model/temperature  | CLI args (--protagonist-model etc.)                 |
| Missing info/scenario        | JSON for `--missing-info-file`                      |
| Max coworker attempts        | JSON or CLI override                                |
| Add new agent                | `load_roles()` + extend simulation routing          |
| Logging / introspection      | `simulation.py`, memory file handling               |

---

## For Further Improvements

See `codex_memory.txt` for open ideas about agent refactoring, metrics/reporting, and more creative agent scripting.

If you add major new features, be sure to note their usage patterns and best practices here for future contributors!

---

Happy benchmarking and agent designing!

_Questions or improvements? Document your insights here and in codex_memory.txt._

---

_Last updated: 2024-06-10_
