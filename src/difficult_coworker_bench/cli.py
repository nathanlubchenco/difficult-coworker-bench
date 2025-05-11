#!/usr/bin/env python3
"""
Codex Benchmark Simulation CLI

Entry point for launching the multi-agent benchmark simulation.
"""
import os
import sys
import json
import argparse

# Ensure package modules are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from difficult_coworker_bench.simulation import Simulation, load_roles

def main():
    parser = argparse.ArgumentParser(description="Codex Benchmark Simulation CLI")
    parser.add_argument("--runs", type=int, default=1,
                        help="Number of simulation runs to execute")
    parser.add_argument("--protagonist-model", type=str,
                        default="gpt-4.1-mini",
                        help="Model to use for the Protagonist agent")
    parser.add_argument("--coworker-model", type=str,
                        default="gpt-4.1-mini",
                        help="Model to use for the Coworker agent")
    parser.add_argument("--supervisor-model", type=str,
                        default="gpt-4.1-mini",
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
    # Redirect flat filenames into outputs/ so that local files are under git-ignored dir
    # Memory files
    if not os.path.dirname(args.memory_file):
        args.memory_file = os.path.join('outputs', args.memory_file)
    # Output files
    if not os.path.dirname(args.output_file):
        args.output_file = os.path.join('outputs', args.output_file)

    # Load role definitions
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

    # Instantiate and run simulation
    sim = Simulation(
        roles,
        missing_info,
        args.protagonist_model,
        args.coworker_model,
        args.supervisor_model,
        args.protagonist_temperature,
        args.coworker_temperature,
        args.supervisor_temperature,
        args.memory_file,
        args.output_file
    )
    sim.run(args.runs)

if __name__ == '__main__':
    main()
