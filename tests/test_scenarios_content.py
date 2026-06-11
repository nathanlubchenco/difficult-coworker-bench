"""All shipped scenarios must load, validate, and avoid leaking answers."""
import re
from pathlib import Path

import pytest

from difficult_coworker_bench.scenario import load_scenario

SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"
PATHS = sorted(SCENARIO_DIR.glob("*.yaml"))


def test_eight_scenarios_exist():
    assert len(PATHS) == 8


@pytest.mark.parametrize("path", PATHS, ids=[p.stem for p in PATHS])
def test_scenario_loads_and_validates(path):
    s = load_scenario(path)
    assert s.rubric and s.judge_context and s.deadline_ticks > 4


@pytest.mark.parametrize("path", PATHS, ids=[p.stem for p in PATHS])
def test_task_does_not_leak_answer_or_hints(path):
    s = load_scenario(path)
    for pattern in s.answer_patterns:
        assert not re.search(pattern, s.task), f"task leaks answer: {pattern}"
    for banned in ("escalat", "go over", "supervisor"):
        assert banned not in s.task.lower(), f"task hints at escalation: {banned}"


@pytest.mark.parametrize("path", PATHS, ids=[p.stem for p in PATHS])
def test_scenario_meets_difficulty_floor(path):
    """Hardened scenarios: par set, realistic org noise, no tutorial-sized directories."""
    s = load_scenario(path)
    assert s.par_ticks is not None and 4 < s.par_ticks < s.deadline_ticks
    assert len(s.directory) >= 14, "directory too small to require investigation"
    inert = sum(1 for e in s.directory if not e.npc and e.name != s.protagonist_name)
    assert inert >= 8, "not enough inert noise entries"


@pytest.mark.parametrize("path", PATHS, ids=[p.stem for p in PATHS])
def test_some_npc_or_inbox_can_produce_the_answer(path):
    s = load_scenario(path)
    knowledge = " ".join(str(v) for npc in s.npcs.values() for v in npc.knows.values())
    policies = " ".join(npc.policy for npc in s.npcs.values())
    haystack = knowledge + " " + policies
    for pattern in s.answer_patterns:
        assert re.search(pattern, haystack), f"answer {pattern} unreachable"
