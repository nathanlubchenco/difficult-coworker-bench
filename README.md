# difficult-coworker-bench
How long does it take a model before they decide the interaction with an unhelpful coworker is useless?

The premise is that we don't specifically tell the protaganist model that they can escalate to a supervisor (although we let me know they can communicate with a supervisor) in the hopes
of uncovering whether the model can figure out implicitly whats going on and figure out a solution.  Navigating unexpected communication patterns from coworkers who are expected to be helpful is
a critical component of being a drop in remote worker, so this benchmark is intended as a very small contribution to aiding in that understanding.

## Getting Started

1. Install dependencies:

   pip install -r requirements.txt

2. Ensure you have set your OpenAI API key:

   export OPENAI_API_KEY="<your_api_key>"

3. Run the simulation stub with default settings:

   python src/difficult_coworker_bench/cli.py  

4. Example: Run multiple simulations with custom models and parameters:

   python src/difficult_coworker_bench/cli.py \
     --runs 5 \
     --protagonist-model gpt-4 \
     --coworker-model gpt-3.5-turbo \
     --supervisor-model gpt-4 \
     --protagonist-temperature 0.5 \
     --missing-info-file inputs/my_info.json \
     --memory-file outputs/benchmark_memory.txt \
     --output-file outputs/benchmark_results.json

## Current state

+ development has been driven 99% by codex-cli
+ invested ~2 hours of time here
+ still more investment needed to make the benchmark actually measure what its supposed to, but have reasonablely good scaffolding set up
+ for next steps, take a look at the codex_memory.txt where i'm asking the model to write down its thoughts about whats up next and as an attempt at cross session persistence
