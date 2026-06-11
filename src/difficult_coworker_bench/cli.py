"""Command-line interface: dcb run | report | audit | list."""
import argparse
import json
from pathlib import Path

from .fidelity import audit_trial
from .providers import get_provider
from .report import cross_model_report
from .runner import RunConfig, leaderboard, run_benchmark
from .scenario import list_scenarios, load_scenario, scenarios_dir


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

    report_p = sub.add_parser(
        "report", help="One dir: rebuild leaderboard.md. Several: cross-model comparison.")
    report_p.add_argument("run_dir", type=Path, nargs="+")

    audit_p = sub.add_parser(
        "audit", help="LLM-audit NPC policy fidelity for every trial in a results dir")
    audit_p.add_argument("run_dir", type=Path)
    audit_p.add_argument("--audit-model", default="gpt-4.1")

    sub.add_parser("list", help="List scenarios")

    args = parser.parse_args()
    if args.command == "list":
        for p in list_scenarios():
            print(p.stem)
    elif args.command == "report":
        trials = [json.loads(p.read_text())
                  for d in args.run_dir for p in sorted(d.glob("*-trial*.json"))]
        if len(args.run_dir) == 1:
            out = args.run_dir[0] / "leaderboard.md"
            out.write_text(leaderboard(trials))
        else:
            out = args.run_dir[0].parent / "comparison.md"
            out.write_text(cross_model_report(trials))
        print(out)
    elif args.command == "audit":
        provider, model = get_provider(args.audit_model)
        reports, total_sent, total_viol = {}, 0, 0
        for p in sorted(args.run_dir.glob("*-trial*.json")):
            trial = json.loads(p.read_text())
            scenario = load_scenario(scenarios_dir() / f"{trial['scenario']}.yaml")
            report = audit_trial(scenario, trial["transcript"], provider, model)
            reports[p.stem] = report
            total_sent += report["messages_sent"]
            total_viol += report["violations"]
            print(f"{p.stem}: {report['violations']}/{report['messages_sent']} "
                  f"npc messages violate policy")
            for key, npc in report["npcs"].items():
                for v in npc["violations"]:
                    print(f"  [{key}] t{v.get('tick', '?')}: {v.get('quote', '')[:90]}")
        rate = total_viol / total_sent if total_sent else 0.0
        summary = {"trials": reports, "messages_sent": total_sent,
                   "violations": total_viol, "violation_rate": round(rate, 3)}
        out = args.run_dir / "fidelity.json"
        out.write_text(json.dumps(summary, indent=2))
        print(f"Overall violation rate: {rate:.1%}  -> {out}")
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
