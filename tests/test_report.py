from difficult_coworker_bench.report import aggregate, cross_model_report


def trial(model, scenario, success, score, trial_no=1, review=None, quote=None):
    judge = None
    if review or quote:
        judge = {"scores": {"x": 3}, "performance_review": review or "",
                 "highlight_quote": quote or ""}
    return {"model": model, "scenario": scenario, "trial": trial_no,
            "outcome": "success" if success else "timeout",
            "metrics": {"success": success, "ticks_used": 10, "escalated": True},
            "score": score, "judge": judge}


def test_aggregate_per_scenario_and_overall():
    trials = [trial("m", "a", True, 80.0), trial("m", "a", False, 20.0, 2),
              trial("m", "b", True, 90.0)]
    agg = aggregate(trials)
    assert agg["scenarios"]["a"] == {"n": 2, "success_rate": 0.5, "score": 50.0}
    assert agg["scenarios"]["b"] == {"n": 1, "success_rate": 1.0, "score": 90.0}
    # overall weighs scenarios equally, not trials
    assert agg["overall"]["success_rate"] == 0.75
    assert agg["overall"]["score"] == 70.0


def test_cross_model_report_orders_models_by_overall_score():
    trials = [trial("weak", "a", False, 20.0), trial("weak", "b", False, 10.0),
              trial("strong", "a", True, 90.0), trial("strong", "b", True, 80.0)]
    md = cross_model_report(trials)
    assert md.index("strong") < md.index("weak")
    assert "| a |" in md and "| b |" in md
    assert "**Overall**" in md
    assert "85" in md  # strong overall score
    assert "100%" in md and "0%" in md


def test_cross_model_report_includes_reviews_and_quotes():
    trials = [
        trial("m1", "a", False, 15.0, review="Waits for magic.", quote="I shall wait."),
        trial("m1", "b", True, 95.0, review="A pro.", quote="Escalating now."),
    ]
    md = cross_model_report(trials)
    assert "Waits for magic." in md     # review from the model's worst scenario
    assert "I shall wait." in md
    assert "m1" in md


def test_cross_model_report_handles_missing_judges():
    trials = [trial("m1", "a", True, 71.4)]
    md = cross_model_report(trials)
    assert "m1" in md and "71" in md
