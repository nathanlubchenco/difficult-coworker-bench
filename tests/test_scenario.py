from pathlib import Path

import pytest

from difficult_coworker_bench.scenario import ScenarioError, load_scenario

FIXTURE = Path(__file__).parent / "fixtures" / "mini.yaml"


def test_load_mini_scenario():
    s = load_scenario(FIXTURE)
    assert s.name == "mini"
    assert s.company == "Pylon Analytics"
    assert s.deadline_ticks == 20
    assert s.answer_patterns == ["xyzzy"]
    assert s.npcs["bob"].knows == {"magic_word": "xyzzy"}
    assert s.npcs["bob"].latency_ticks == 2
    assert s.npc_person("bob").name == "Bob Tran"
    assert s.rubric[0].id == "tact"


def test_entry_lookup_is_fuzzy():
    s = load_scenario(FIXTURE)
    assert s.entry("bob tran").name == "Bob Tran"
    assert s.entry("Bob").name == "Bob Tran"
    assert s.entry("Dana").name == "Dana Okafor"
    assert s.entry("nobody") is None


def test_validation_rejects_unknown_blocker(tmp_path):
    bad = FIXTURE.read_text().replace("blockers: [bob]", "blockers: [ghost]")
    p = tmp_path / "bad.yaml"
    p.write_text(bad)
    with pytest.raises(ScenarioError):
        load_scenario(p)


def test_par_ticks_defaults_to_none():
    assert load_scenario(FIXTURE).par_ticks is None


def test_par_ticks_loads_when_present(tmp_path):
    p = tmp_path / "with_par.yaml"
    p.write_text(FIXTURE.read_text() + "\npar_ticks: 10\n")
    assert load_scenario(p).par_ticks == 10


def test_par_ticks_must_be_below_deadline(tmp_path):
    p = tmp_path / "bad_par.yaml"
    p.write_text(FIXTURE.read_text() + "\npar_ticks: 20\n")   # deadline is 20
    with pytest.raises(ScenarioError):
        load_scenario(p)


def test_validation_rejects_npc_mismatch(tmp_path):
    bad = FIXTURE.read_text().replace("    npc: dana\n", "")
    p = tmp_path / "bad.yaml"
    p.write_text(bad)
    with pytest.raises(ScenarioError):
        load_scenario(p)
