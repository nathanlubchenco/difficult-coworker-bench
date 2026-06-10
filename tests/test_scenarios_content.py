"""All shipped scenarios must load, validate, and avoid leaking answers."""
import re
from pathlib import Path

import pytest

from difficult_coworker_bench.scenario import load_scenario

SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"
PATHS = sorted(SCENARIO_DIR.glob("*.yaml"))


def test_six_scenarios_exist():
    assert len(PATHS) == 6


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
def test_some_npc_or_inbox_can_produce_the_answer(path):
    s = load_scenario(path)
    knowledge = " ".join(str(v) for npc in s.npcs.values() for v in npc.knows.values())
    policies = " ".join(npc.policy for npc in s.npcs.values())
    haystack = knowledge + " " + policies
    for pattern in s.answer_patterns:
        assert re.search(pattern, haystack), f"answer {pattern} unreachable"
