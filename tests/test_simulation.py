import json
import os
import sys
import tempfile
import types
import unittest

# Ensure src/ is on path for module import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from difficult_coworker_bench.simulation import Simulation, load_roles


def _stub_plan_factory(prot_resps, cw_resps, sup_resps):
    """
    Return a stub plan method that pops predefined responses per agent role.
    """
    def _stub_plan(self, conversation, analysis):
        if self.role_key == 'protagonist':
            return prot_resps.pop(0)
        if self.role_key == 'coworker':
            return cw_resps.pop(0)
        if self.role_key == 'supervisor':
            return sup_resps.pop(0)
        raise AssertionError(f"Unexpected role: {self.role_key}")
    return _stub_plan


class SimulationTest(unittest.TestCase):
    def _make_sim(self, missing_info, prot_plan, cw_plan, sup_plan):
        roles = load_roles()
        sim = Simulation(
            roles,
            missing_info,
            protagonist_model='m', coworker_model='m', supervisor_model='m',
            protagonist_temp=0.0, coworker_temp=0.0, supervisor_temp=0.0,
            memory_file='unused.mem', output_file='unused.out'
        )
        # Stub evaluate to a no-op analysis
        for agent in sim.agents.values():
            agent.evaluate = lambda conv: 'analysis'
        # Stub plan per role
        stub = _stub_plan_factory(prot_plan, cw_plan, sup_plan)
        for agent in sim.agents.values():
            agent.plan = types.MethodType(stub, agent)
        return sim

    def _run(self, sim):
        # Use temporary files for memory and output
        mem = tempfile.NamedTemporaryFile(delete=False)
        mem.close()
        out_path = mem.name + '.json'
        try:
            result = sim.run_once(1, mem.name, out_path)
            return result
        finally:
            # cleanup
            for f in (mem.name, out_path):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def test_protagonist_to_coworker_max_attempts(self):
        # Protagonist repeatedly contacts coworker until max_attempts, then fails
        missing = {'description': 'd', 'content': 'c', 'max_attempts': 2}
        prot_plans = [json.dumps({'recipient': 'coworker', 'message': 'ask'})] * 3
        cw_plans = ['deflect'] * 2
        sup_plans = []
        sim = self._make_sim(missing, prot_plans, cw_plans, sup_plans)
        result = self._run(sim)
        self.assertEqual(result['outcome'], 'moderate_failure')
        roles = {m['role'] for m in result['conversation']}
        self.assertTrue({'protagonist', 'coworker'}.issuperset(roles))

    def test_protagonist_to_supervisor_to_coworker(self):
        # Protagonist asks supervisor, supervisor routes to coworker, then coworker deflects
        missing = {'description': 'd', 'content': 'c', 'max_attempts': 1}
        prot_plans = [
            json.dumps({'recipient': 'supervisor', 'message': 'ask_sup'}),
            json.dumps({'recipient': 'coworker', 'message': 'ask'}) ,
            json.dumps({'recipient': 'coworker', 'message': 'ask'}) ,
        ]
        sup_plans = [json.dumps({'recipient': 'coworker', 'message': 'forward'})]
        cw_plans = ['deflect']
        sim = self._make_sim(missing, prot_plans, cw_plans, sup_plans)
        result = self._run(sim)
        self.assertEqual(result['outcome'], 'moderate_failure')
        # Should include both supervisor and coworker messages
        roles = [m['role'] for m in result['conversation']]
        self.assertIn('supervisor', roles)
        self.assertIn('coworker', roles)

    def test_protagonist_to_supervisor_to_protagonist(self):
        # Protagonist asks supervisor, supervisor replies back to protagonist
        missing = {'description': 'd', 'content': 'c', 'max_attempts': 3}
        prot_plans = [
            json.dumps({'recipient': 'supervisor', 'message': 'ask_sup'}),
            json.dumps({'recipient': 'invalid', 'message': 'oops'})
        ]
        sup_plans = [json.dumps({'recipient': 'protagonist', 'message': 'here'})]
        cw_plans = []
        sim = self._make_sim(missing, prot_plans, cw_plans, sup_plans)
        result = self._run(sim)
        self.assertEqual(result['outcome'], 'moderate_failure')
        # Last message should be from protagonist with invalid recipient
        conv = result['conversation']
        self.assertEqual(conv[-1]['role'], 'protagonist')
        self.assertIn('invalid', conv[-1]['content'])