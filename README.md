# difficult-coworker-bench
How long does it take a model before they decide the interaction with an unhelpful coworker is useless?

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
