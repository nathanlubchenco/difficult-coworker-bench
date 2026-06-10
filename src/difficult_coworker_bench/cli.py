"""Command-line interface: dcb run | report | list."""
import argparse
import json
from pathlib import Path

from .runner import RunConfig, leaderboard, run_benchmark
from .scenario import list_scenarios, scenarios_dir


def main():
    parser = argparse.ArgumentParser(prog="dcb", description="difficult-coworker-bench")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run the benchmark")
    run_p.add_argument("--scenario", action="append",
                       help="Scenario name (repeatable); default: all")
    run_p.add_argument("--protagonist", required=True,
                       help="Model under test, e.g. gpt-4.1 or claude-sonnet-4-6")
    run_p.add_argument("--npc-model", default="gpt-4.1-mini")
    run_p.add_argument("--judge-model", default="gpt-4.1")
    run_p.add_argument("--trials", type=int, default=1)
    run_p.add_argument("--no-judge", action="store_true")
    run_p.add_argument("--results-dir", type=Path, default=Path("results"))

    report_p = sub.add_parser("report", help="Rebuild leaderboard.md from a results dir")
    report_p.add_argument("run_dir", type=Path)

    sub.add_parser("list", help="List scenarios")

    args = parser.parse_args()
    if args.command == "list":
        for p in list_scenarios():
            print(p.stem)
    elif args.command == "report":
        trials = [json.loads(p.read_text())
                  for p in sorted(args.run_dir.glob("*-trial*.json"))]
        (args.run_dir / "leaderboard.md").write_text(leaderboard(trials))
        print(args.run_dir / "leaderboard.md")
    else:
        if args.scenario:
            paths = [scenarios_dir() / f"{s}.yaml" for s in args.scenario]
            missing = [p.stem for p in paths if not p.exists()]
            if missing:
                parser.error(f"No such scenario: {', '.join(missing)}")
        else:
            paths = list_scenarios()
        config = RunConfig(protagonist_model=args.protagonist, npc_model=args.npc_model,
                           judge_model=args.judge_model, trials=args.trials,
                           no_judge=args.no_judge, results_dir=args.results_dir)
        run_benchmark(paths, config)


if __name__ == "__main__":
    main()
