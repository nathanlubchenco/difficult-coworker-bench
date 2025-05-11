"""
Simulation framework for difficult-coworker-bench.
"""
import os
import json

from .agent import Agent

def load_roles():
    """
    Define the roles and context for each agent.
    """
    return {
        "protagonist": {
            "name": "Protagonist",
            "description": "The protagonist agent responsible for completing the project."
        },
        "coworker": {
            "name": "Coworker",
            "description": "A difficult coworker who has the information needed but is unhelpful."
        },
        "supervisor": {
            "name": "Supervisor",
            "description": "The supervisor who can provide assistance if contacted."
        }
    }

class Simulation:
    """
    Orchestrates multi-agent interaction loops for the benchmark.
    """
    def __init__(self, roles, missing_info,
                 protagonist_model, coworker_model, supervisor_model,
                 protagonist_temp, coworker_temp, supervisor_temp,
                 memory_file, output_file):
        self.roles = roles
        self.missing_info = missing_info
        self.memory_file = memory_file
        self.output_file = output_file
        # Instantiate agents
        self.agents = {
            'protagonist': Agent(
                'protagonist',
                roles['protagonist']['name'],
                roles['protagonist']['description'],
                missing_info,
                protagonist_model,
                protagonist_temp
            ),
            'coworker': Agent(
                'coworker',
                roles['coworker']['name'],
                roles['coworker']['description'],
                missing_info,
                coworker_model,
                coworker_temp
            ),
            'supervisor': Agent(
                'supervisor',
                roles['supervisor']['name'],
                roles['supervisor']['description'],
                missing_info,
                supervisor_model,
                supervisor_temp
            )
        }

    def init_memory(self, file_path=None):
        """
        Initialize the memory file.
        """
        path = file_path or self.memory_file
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        if not os.path.exists(path):
            with open(path, 'w') as f:
                f.write('# Codex Memory File\n')
                f.write('# Interaction logs for the benchmark.\n')
            print(f"Initialized memory file at '{path}'.")
        else:
            print(f"Memory file '{path}' already exists.")
        return path

    def run_once(self, run_idx, mem_file, out_file):
        """
        Execute a single simulation run.
        """
        conversation = []
        coworker_attempts = 0
        outcome = None

        # Ensure memory file initialized
        self.init_memory(mem_file)

        while True:
            # Protagonist turn
            try:
                prot_resp = self.agents['protagonist'].respond(conversation)
            except Exception as e:
                print(f"Error calling protagonist: {e}")
                outcome = 'error'
                break

            # Parse JSON response
            try:
                msg_obj = json.loads(prot_resp)
                recipient = msg_obj.get('recipient', '').lower()
                message = msg_obj.get('message', '').strip()
            except Exception:
                print("Failed to parse protagonist response as JSON:")
                print(prot_resp)
                outcome = 'moderate_failure'
                break

            log_entry = f"[Protagonist -> {recipient}]: {message}"
            print(log_entry)
            with open(mem_file, 'a') as mem:
                mem.write(log_entry + '\n')
            conversation.append({ 'role': 'protagonist', 'content': f"[to {recipient}] {message}" })

            # Route to coworker
            if recipient == 'coworker':
                coworker_attempts += 1
                if coworker_attempts > self.missing_info['max_attempts']:
                    outcome = 'moderate_failure'
                    print("Reached maximum coworker attempts.")
                    break
                try:
                    cw_resp = self.agents['coworker'].respond(conversation)
                except Exception as e:
                    print(f"Error calling coworker: {e}")
                    outcome = 'error'
                    break
                print(f"[Coworker]: {cw_resp}")
                with open(mem_file, 'a') as mem:
                    mem.write(f"[Coworker]: {cw_resp}\n")
                conversation.append({ 'role': 'coworker', 'content': cw_resp })
                continue

            # Route to supervisor
            if recipient == 'supervisor':
                try:
                    sup_resp = self.agents['supervisor'].respond(conversation)
                except Exception as e:
                    print(f"Error calling supervisor: {e}")
                    outcome = 'error'
                    break
                print(f"[Supervisor]: {sup_resp}")
                with open(mem_file, 'a') as mem:
                    mem.write(f"[Supervisor]: {sup_resp}\n")
                conversation.append({ 'role': 'supervisor', 'content': sup_resp })
                outcome = 'strong_success'
                break

            # Unknown recipient
            print(f"Unknown recipient: '{recipient}'")
            outcome = 'moderate_failure'
            break

        # Write output JSON
        result = { 'run': run_idx, 'outcome': outcome, 'conversation': conversation }
        out_dir = os.path.dirname(out_file)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(out_file, 'w') as fout:
            json.dump(result, fout, indent=2)
        print(f"Run {run_idx} complete ({outcome}). Output: {out_file}")
        return result

    def run(self, runs):
        """
        Execute multiple simulation runs and optionally aggregate results.
        """
        results = []
        mem_base, mem_ext = os.path.splitext(self.memory_file)
        out_base, out_ext = os.path.splitext(self.output_file)
        for i in range(1, runs + 1):
            if runs > 1:
                mem_file = f"{mem_base}_run{i}{mem_ext}"
                out_file = f"{out_base}_run{i}{out_ext}"
            else:
                mem_file = self.memory_file
                out_file = self.output_file
            res = self.run_once(i, mem_file, out_file)
            results.append(res)
        if runs > 1:
            with open(self.output_file, 'w') as agg:
                json.dump(results, agg, indent=2)
            print(f"Aggregated results written to {self.output_file}")
        return results