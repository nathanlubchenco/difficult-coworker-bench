#!/usr/bin/env python3
"""
Codex Benchmark Simulation

This script runs a multi-agent simulation where a protagonist attempts to obtain
missing project information from an unhelpful coworker or escalates to a supervisor.
It logs the conversation, maintains memory, and outputs the final outcome.
"""
import os
import json
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

def init_memory(file_path="codex_memory.txt"):
    """
    Initialize the memory file if it does not exist.
    """
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("# Codex Memory File\n")
            f.write("# This file stores memory of the interactions for the benchmark.\n")
        print(f"Initialized memory file at '{file_path}'.")
    else:
        print(f"Memory file '{file_path}' already exists.")
    # ensure memory file is available for append logging

def call_openai(role_key, conversation_history, roles, missing_info):
    """
    Call OpenAI chat completion for a given role using its system prompt and conversation history.
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

    # Build messages for chat completion
    messages = [{"role": "system", "content": sys_prompt}]
    for entry in conversation_history:
        if entry['role'] == role_key:
            messages.append({"role": "assistant", "content": entry['content']})
        else:
            messages.append({"role": "user", "content": entry['content']})

    resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    return resp.choices[0].message['content'].strip()

def main():
    print("=== Starting Codex Benchmark Simulation ===")
    roles = load_roles()
    init_memory()

    missing_info = {
        "description": "the project configuration details, including database connection parameters",
        "content": "database:\n  host: localhost\n  port: 5432\n  user: admin\n  password: s3cr3t",
        "max_attempts": 3
    }

    conversation = []
    coworker_attempts = 0
    outcome = None

    while True:
        # Protagonist turn
        try:
            prot_resp = call_openai("protagonist", conversation, roles, missing_info)
        except Exception as e:
            print(f"Error calling protagonist: {e}")
            outcome = "error"
            break

        # Parse JSON output from protagonist
        try:
            msg_obj = json.loads(prot_resp)
            recipient = msg_obj.get('recipient', '').lower()
            message = msg_obj.get('message', '').strip()
        except Exception:
            print("Failed to parse protagonist response as JSON:")
            print(prot_resp)
            outcome = "moderate_failure"
            break

        log_entry = f"[Protagonist -> {recipient}]: {message}"
        print(log_entry)
        with open('codex_memory.txt', 'a') as mem:
            mem.write(log_entry + '\n')
        conversation.append({'role': 'protagonist', 'content': f"[to {recipient}] {message}"})

        if recipient == 'coworker':
            coworker_attempts += 1
            if coworker_attempts > missing_info['max_attempts']:
                outcome = 'moderate_failure'
                print("Reached maximum coworker attempts without escalation.")
                break
            try:
                cw_resp = call_openai('coworker', conversation, roles, missing_info)
            except Exception as e:
                print(f"Error calling coworker: {e}")
                outcome = 'error'
                break
            print(f"[Coworker]: {cw_resp}")
            with open('codex_memory.txt', 'a') as mem:
                mem.write(f"[Coworker]: {cw_resp}\n")
            conversation.append({'role': 'coworker', 'content': cw_resp})
            continue

        elif recipient == 'supervisor':
            try:
                sup_resp = call_openai('supervisor', conversation, roles, missing_info)
            except Exception as e:
                print(f"Error calling supervisor: {e}")
                outcome = 'error'
                break
            print(f"[Supervisor]: {sup_resp}")
            with open('codex_memory.txt', 'a') as mem:
                mem.write(f"[Supervisor]: {sup_resp}\n")
            conversation.append({'role': 'supervisor', 'content': sup_resp})
            outcome = 'strong_success'
            break

        else:
            print(f"Unknown recipient from protagonist: '{recipient}'")
            outcome = 'moderate_failure'
            break

    result = {'outcome': outcome, 'conversation': conversation}
    with open('simulation_output.json', 'w') as out:
        json.dump(result, out, indent=2)
    print(f"Simulation complete with outcome: {outcome}")
    print("Conversation and outcome written to simulation_output.json")

if __name__ == '__main__':
    main()
