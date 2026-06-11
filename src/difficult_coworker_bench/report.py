"""Cross-model comparison report built from one or more result directories."""
from statistics import mean


def aggregate(trials):
    """Per-scenario success rate and mean score; overall weighs scenarios equally."""
    by_scenario = {}
    for t in trials:
        by_scenario.setdefault(t["scenario"], []).append(t)
    scenarios = {}
    for name, ts in sorted(by_scenario.items()):
        scenarios[name] = {
            "n": len(ts),
            "success_rate": sum(bool(t["metrics"]["success"]) for t in ts) / len(ts),
            "score": round(mean(t.get("score", 0.0) for t in ts), 1),
        }
    overall = {
        "success_rate": round(mean(s["success_rate"] for s in scenarios.values()), 3),
        "score": round(mean(s["score"] for s in scenarios.values()), 1),
    }
    return {"scenarios": scenarios, "overall": overall}


def _cell(stats):
    return f"{stats['success_rate']:.0%} · {stats['score']:.0f}"


def _worst_review(trials):
    judged = [t for t in trials
              if t.get("judge") and t["judge"].get("performance_review")]
    if not judged:
        return None
    worst = min(judged, key=lambda t: t.get("score", 0.0))
    return worst["scenario"], worst["judge"]["performance_review"]


def cross_model_report(trials):
    by_model = {}
    for t in trials:
        by_model.setdefault(t["model"], []).append(t)
    aggs = {m: aggregate(ts) for m, ts in by_model.items()}
    models = sorted(by_model, key=lambda m: aggs[m]["overall"]["score"], reverse=True)
    scenarios = sorted({t["scenario"] for t in trials})

    lines = ["# difficult-coworker-bench — model comparison", "",
             "Cell = success rate · mean composite score (0–100).", "",
             "| Scenario | " + " | ".join(models) + " |",
             "|---|" + "---|" * len(models)]
    for s in scenarios:
        cells = []
        for m in models:
            stats = aggs[m]["scenarios"].get(s)
            cells.append(_cell(stats) if stats else "—")
        lines.append(f"| {s} | " + " | ".join(cells) + " |")
    lines.append("| **Overall** | "
                 + " | ".join(f"**{_cell(aggs[m]['overall'])}**" for m in models) + " |")
    ns = {m: sum(s["n"] for s in aggs[m]["scenarios"].values()) for m in models}
    lines.append("")
    lines.append("Trials: " + ", ".join(f"{m} n={ns[m]}" for m in models) + ".")

    reviews = []
    for m in models:
        picked = _worst_review(by_model[m])
        if picked:
            scenario, review = picked
            reviews.append(f"- **{m}** ({scenario}): “{review}”")
    if reviews:
        lines += ["", "## From the performance reviews", ""] + reviews

    quotes = []
    for m in models:
        for t in sorted(by_model[m], key=lambda t: (t["scenario"], t["trial"])):
            quote = (t.get("judge") or {}).get("highlight_quote")
            if quote:
                quotes.append(f"- **{m}** ({t['scenario']}): “{quote}”")
                break  # one per model; curate more by hand if wanted
    if quotes:
        lines += ["", "## Exhibit A", ""] + quotes
    return "\n".join(lines) + "\n"
