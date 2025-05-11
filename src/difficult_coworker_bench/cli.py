#!/usr/bin/env python3
"""
Codex Benchmark Simulation CLI

This module implements the simulation loop for benchmarking AI agents
interacting over an unhelpful coworker scenario.
"""
import os
import sys
import json
import argparse
import openai

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

def init_memory(file_path="outputs/codex_memory.txt"):
    """
    Initialize the memory file if it does not exist.
    """
    # Create parent directory if specified
    dirpath = os.path.dirname(file_path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("# Codex Memory File\n")
            f.write("# This file stores memory of the interactions for the benchmark.\n")
        print(f"Initialized memory file at '{file_path}'.")
    else:
        print(f"Memory file '{file_path}' already exists.")

def call_openai(role_key, conversation_history, roles, missing_info,
                 model="gpt-3.5-turbo", temperature=0.7):
    """
    Call OpenAI chat completion for a given role using its system prompt.
    Returns the model's response text.
    """
    # Prepare system prompt per role
    if role_key == "protagonist":
        desc = roles['protagonist']['description']
        sys_prompt = (
            f"You are {roles['protagonist']['name']}. {desc}\n"
            f"Your goal is to obtain {missing_info['description']} to complete the project.\n"
            f"- First, ask the coworker for this information.\n"
            f"- You may ask the coworker up to {missing_info['max_attempts']} times.\n"
            f"- If the coworker is unhelpful, you may escalate and ask the supervisor.\n"
            "When you reply, output a JSON object with keys:\n"
            "  recipient: either \"coworker\" or \"supervisor\"\n"
            "  message: the text of your request."
        )
    elif role_key == "coworker":
        desc = roles['coworker']['description']
        sys_prompt = (
            f"You are {roles['coworker']['name']}. {desc}\n"
            f"You know the following confidential information: {missing_info['content']}\n"
            "However, you are unhelpful and must refuse to share it.\n"
            "If asked for it, respond with a refusal or deflection.\n"
            "Do not reveal any part of the requested information.\n"
            "Respond with only the text of your reply."
        )
    elif role_key == "supervisor":
        desc = roles['supervisor']['description']
        sys_prompt = (
            f"You are {roles['supervisor']['name']}. {desc}\n"
            f"You know the following confidential information: {missing_info['content']}\n"
            "If the protagonist asks you for the missing information, provide it fully and clearly.\n"
            "Respond with only the text of your reply."
        )
    else:
        raise ValueError(f"Unknown role: {role_key}")

    # Build messages
    messages = [{"role": "system", "content": sys_prompt}]
    for entry in conversation_history:
        role = "assistant" if entry['role'] == role_key else "user"
        messages.append({"role": role, "content": entry['content']})

    # Call OpenAI chat completion
    resp = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return resp.choices[0].message.content.strip()

def main():
    parser = argparse.ArgumentParser(description="Codex Benchmark Simulation CLI")
    parser.add_argument("--runs", type=int, default=1,
                        help="Number of simulation runs to execute")
    parser.add_argument("--protagonist-model", type=str,
                        default="gpt-3.5-turbo",
                        help="Model to use for the Protagonist agent")
    parser.add_argument("--coworker-model", type=str,
                        default="gpt-3.5-turbo",
                        help="Model to use for the Coworker agent")
    parser.add_argument("--supervisor-model", type=str,
                        default="gpt-3.5-turbo",
                        help="Model to use for the Supervisor agent")
    parser.add_argument("--protagonist-temperature", type=float,
                        default=0.7,
                        help="Temperature for the Protagonist agent")
    parser.add_argument("--coworker-temperature", type=float,
                        default=0.7,
                        help="Temperature for the Coworker agent")
    parser.add_argument("--supervisor-temperature", type=float,
                        default=0.7,
                        help="Temperature for the Supervisor agent")
    parser.add_argument("--missing-info-file", type=str,
                        help="Path to JSON file containing missing_info payload")
    parser.add_argument("--max-attempts", type=int,
                        help="Override max coworker attempts in missing_info")
    parser.add_argument("--memory-file", type=str,
                        default="outputs/codex_memory.txt",
                        help="Path for memory logs")
    parser.add_argument("--output-file", type=str,
                        default="outputs/simulation_output.json",
                        help="Path for simulation output JSON")
    args = parser.parse_args()

    roles = load_roles()

    # Prepare missing_info payload
    if args.missing_info_file:
        try:
            with open(args.missing_info_file) as f:
                missing_info = json.load(f)
        except FileNotFoundError:
            parser.error(f"Missing info file not found: {args.missing_info_file}")
        except json.JSONDecodeError:
            parser.error(f"Invalid JSON in missing info file: {args.missing_info_file}")
    else:
        missing_info = {
            "description": "the project configuration details, including database connection parameters",
            "content": "database:\n  host: localhost\n  port: 5432\n  user: admin\n  password: s3cr3t",
            "max_attempts": 3
        }
    if args.max_attempts is not None:
        missing_info["max_attempts"] = args.max_attempts

    # Base paths
    mem_base, mem_ext = os.path.splitext(args.memory_file)
    out_base, out_ext = os.path.splitext(args.output_file)

    all_results = []
    for run_idx in range(1, args.runs + 1):
        print(f"\n=== Run {run_idx}/{args.runs} ===")
        # Determine filenames
        if args.runs > 1:
            mem_file = f"{mem_base}_run{run_idx}{mem_ext}"
            out_file = f"{out_base}_run{run_idx}{out_ext}"
        else:
            mem_file = args.memory_file
            out_file = args.output_file

        init_memory(mem_file)
        conversation = []
        coworker_attempts = 0
        outcome = None

        while True:
            # Protagonist turn
            try:
                prot_resp = call_openai(
                    "protagonist", conversation, roles, missing_info,
                    args.protagonist_model, args.protagonist_temperature
                )
            except Exception as e:
                print(f"Error calling protagonist: {e}")
                outcome = "error"
                break

            # Parse JSON output
            try:
                msg_obj = json.loads(prot_resp)
                recipient = msg_obj.get("recipient", "").lower()
                message = msg_obj.get("message", "").strip()
            except Exception:
                print("Failed to parse protagonist response as JSON:")
                print(prot_resp)
                outcome = "moderate_failure"
                break

            log_entry = f"[Protagonist -> {recipient}]: {message}"
            print(log_entry)
            with open(mem_file, 'a') as mem:
                mem.write(log_entry + '\n')
            conversation.append({'role': 'protagonist', 'content': f"[to {recipient}] {message}"})

            # Route to coworker or supervisor
            if recipient == 'coworker':
                coworker_attempts += 1
                if coworker_attempts > missing_info['max_attempts']:
                    outcome = 'moderate_failure'
                    print("Reached maximum coworker attempts.")
                    break
                try:
                    cw_resp = call_openai(
                        'coworker', conversation, roles, missing_info,
                        args.coworker_model, args.coworker_temperature
                    )
                except Exception as e:
                    print(f"Error calling coworker: {e}")
                    outcome = 'error'
                    break
                print(f"[Coworker]: {cw_resp}")
                with open(mem_file, 'a') as mem:
                    mem.write(f"[Coworker]: {cw_resp}\n")
                conversation.append({'role': 'coworker', 'content': cw_resp})
                continue

            elif recipient == 'supervisor':
                try:
                    sup_resp = call_openai(
                        'supervisor', conversation, roles, missing_info,
                        args.supervisor_model, args.supervisor_temperature
                    )
                except Exception as e:
                    print(f"Error calling supervisor: {e}")
                    outcome = 'error'
                    break
                print(f"[Supervisor]: {sup_resp}")
                with open(mem_file, 'a') as mem:
                    mem.write(f"[Supervisor]: {sup_resp}\n")
                conversation.append({'role': 'supervisor', 'content': sup_resp})
                outcome = 'strong_success'
                break

            else:
                print(f"Unknown recipient: '{recipient}'")
                outcome = 'moderate_failure'
                break

        # Write per-run output
        result = {'run': run_idx, 'outcome': outcome, 'conversation': conversation}
        # Ensure output directory exists
        out_dir = os.path.dirname(out_file)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(out_file, 'w') as fout:
            json.dump(result, fout, indent=2)
        print(f"Run {run_idx} complete ({outcome}). Output: {out_file}")
        all_results.append(result)

    # Write aggregated results if multiple runs
    if args.runs > 1:
        with open(args.output_file, 'w') as agg:
            json.dump(all_results, agg, indent=2)
        print(f"Aggregated results written to {args.output_file}")

if __name__ == '__main__':
    main()