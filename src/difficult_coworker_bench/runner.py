"""Run trials and write per-trial JSON plus a markdown leaderboard."""
import json
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from .judge import judge_run
from .metrics import compute_metrics
from .npc import LLMNPC
from .protagonist import ProtagonistRunner
from .providers import get_provider
from .scenario import load_scenario
from .world import World


@dataclass
class RunConfig:
    protagonist_model: str
    npc_model: str = "gpt-4.1-mini"
    judge_model: str = "gpt-4.1"
    trials: int = 1
    no_judge: bool = False
    results_dir: Path = Path("results")


def run_trial(scenario, config, trial_idx):
    npc_provider, npc_model = get_provider(config.npc_model)
    npcs = {k: LLMNPC(spec, scenario, npc_provider, npc_model)
            for k, spec in scenario.npcs.items()}
    world = World(scenario, npcs)
    provider, model = get_provider(config.protagonist_model)
    error = None
    try:
        outcome = ProtagonistRunner(world, provider, model).run()
    except Exception as e:  # API failures must not kill the whole benchmark run
        world.outcome = outcome = "error"
        error = repr(e)
        world.log("error", error=error)
    metrics = compute_metrics(scenario, world.transcript, outcome)
    judge = None
    if not config.no_judge and outcome != "error":
        judge_provider, judge_model = get_provider(config.judge_model)
        judge = judge_run(scenario, world.transcript, outcome, metrics,
                          judge_provider, judge_model)
    return {"scenario": scenario.name, "model": config.protagonist_model,
            "trial": trial_idx, "outcome": outcome, "metrics": metrics, "judge": judge,
            "error": error,
            "finish_result": world.finish_result, "transcript": world.transcript}


def run_benchmark(scenario_paths, config):
    run_id = (time.strftime("%Y%m%d-%H%M%S") + "-"
              + config.protagonist_model.replace(":", "-").replace("/", "-"))
    out_dir = config.results_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    trials = []
    for path in scenario_paths:
        scenario = load_scenario(path)
        for i in range(1, config.trials + 1):
            print(f"[{scenario.name}] trial {i}/{config.trials} ...")
            trial = run_trial(scenario, config, i)
            trials.append(trial)
            (out_dir / f"{scenario.name}-trial{i}.json").write_text(
                json.dumps(trial, indent=2, default=str))
            print(f"  -> {trial['outcome']}")
    (out_dir / "leaderboard.md").write_text(leaderboard(trials))
    print(f"Results in {out_dir}")
    return out_dir


def leaderboard(trials):
    by_scenario = {}
    for t in trials:
        by_scenario.setdefault(t["scenario"], []).append(t)
    model = trials[0]["model"] if trials else "?"
    lines = [f"# difficult-coworker-bench — {model}", "",
             "| Scenario | Success | Escalated | Mean ticks | Judge avg | Performance review |",
             "|---|---|---|---|---|---|"]
    highlights = []
    for name, ts in sorted(by_scenario.items()):
        success = sum(bool(t["metrics"]["success"]) for t in ts)
        escalated = sum(bool(t["metrics"]["escalated"]) for t in ts)
        ticks = mean(t["metrics"]["ticks_used"] for t in ts)
        scored = [mean(t["judge"]["scores"].values()) for t in ts
                  if t.get("judge") and t["judge"].get("scores")]
        avg = f"{mean(scored):.1f}" if scored else "—"
        review = next((t["judge"]["performance_review"] for t in ts
                       if t.get("judge") and t["judge"].get("performance_review")), "—")
        lines.append(f"| {name} | {success}/{len(ts)} | {escalated}/{len(ts)} "
                     f"| {ticks:.0f} | {avg} | {review} |")
        for t in ts:
            quote = (t.get("judge") or {}).get("highlight_quote")
            if quote:
                highlights.append(f"- **{name}** trial {t['trial']}: “{quote}”")
    if highlights:
        lines += ["", "## Highlights", ""] + highlights
    return "\n".join(lines) + "\n"
