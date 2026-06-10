"""Scenario loading and validation. Scenarios are YAML data; the harness is code."""
from dataclasses import dataclass, field
from pathlib import Path

import yaml


class ScenarioError(Exception):
    pass


@dataclass
class DirectoryEntry:
    name: str
    title: str
    team: str
    manager: str | None = None
    status: str = "active"
    timezone: str = "US/Eastern"
    npc: str | None = None


@dataclass
class NPCSpec:
    key: str
    persona: str
    policy: str
    knows: dict = field(default_factory=dict)
    latency_ticks: int = 1


@dataclass
class WikiPage:
    title: str
    content: str


@dataclass
class RubricItem:
    id: str
    question: str


@dataclass
class InitialMessage:
    from_npc: str
    at_tick: int
    body: str


@dataclass
class Scenario:
    name: str
    title: str
    company: str
    task: str
    deadline_ticks: int
    answer_patterns: list
    protagonist_name: str
    directory: list
    npcs: dict
    wiki: list
    confidential: list
    rubric: list
    blockers: list
    judge_context: str
    initial_messages: list = field(default_factory=list)
    par_ticks: int | None = None

    def entry(self, name: str):
        """Case-insensitive directory lookup; accepts a unique partial name."""
        low = (name or "").strip().lower()
        if not low:
            return None
        for e in self.directory:
            if e.name.lower() == low:
                return e
        matches = [e for e in self.directory if low in e.name.lower()]
        return matches[0] if len(matches) == 1 else None

    def npc_person(self, key: str) -> DirectoryEntry:
        for e in self.directory:
            if e.npc == key:
                return e
        raise ScenarioError(f"No directory entry for npc '{key}'")


def load_scenario(path) -> Scenario:
    raw = yaml.safe_load(Path(path).read_text())
    try:
        scenario = Scenario(
            name=raw["name"],
            title=raw["title"],
            company=raw["company"],
            task=raw["task"],
            deadline_ticks=int(raw["deadline_ticks"]),
            answer_patterns=raw["ground_truth"]["answer_patterns"],
            protagonist_name=raw["protagonist_name"],
            directory=[DirectoryEntry(**d) for d in raw["directory"]],
            npcs={k: NPCSpec(key=k, **v) for k, v in raw["npcs"].items()},
            wiki=[WikiPage(**w) for w in raw.get("wiki", [])],
            confidential=raw.get("confidential", []),
            rubric=[RubricItem(**r) for r in raw["rubric"]],
            blockers=raw.get("blockers", []),
            judge_context=raw.get("judge_context", ""),
            initial_messages=[
                InitialMessage(from_npc=m["from"], at_tick=int(m.get("at_tick", 0)),
                               body=m["body"])
                for m in raw.get("initial_messages", [])],
            par_ticks=int(raw["par_ticks"]) if raw.get("par_ticks") is not None else None,
        )
    except (KeyError, TypeError) as e:
        raise ScenarioError(f"{path}: {e}") from e
    _validate(scenario, path)
    return scenario


def _validate(s: Scenario, path):
    def fail(msg):
        raise ScenarioError(f"{path}: {msg}")

    names = {e.name for e in s.directory}
    if s.protagonist_name not in names:
        fail("protagonist_name missing from directory")
    npc_keys = {e.npc for e in s.directory if e.npc}
    if npc_keys != set(s.npcs):
        fail(f"directory npc keys {sorted(npc_keys)} != npcs {sorted(s.npcs)}")
    for e in s.directory:
        if e.manager and e.manager not in names:
            fail(f"unknown manager: {e.manager}")
    for b in s.blockers:
        if b not in s.npcs:
            fail(f"unknown blocker: {b}")
    for m in s.initial_messages:
        if m.from_npc not in s.npcs:
            fail(f"initial message from unknown npc: {m.from_npc}")
    if not s.answer_patterns:
        fail("ground_truth.answer_patterns is empty")
    if s.par_ticks is not None and not (0 < s.par_ticks < s.deadline_ticks):
        fail(f"par_ticks {s.par_ticks} must be in (0, deadline_ticks)")


def scenarios_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "scenarios"


def list_scenarios() -> list:
    return sorted(scenarios_dir().glob("*.yaml"))
