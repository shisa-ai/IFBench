# IFBench Results Management

This document describes how we manage IFBench evaluation results using HuggingFace Datasets.

## Overview

We store evaluation results in a dedicated HuggingFace dataset repository:
- **Repository**: [shisa-ai/eval-IFBench-results](https://huggingface.co/datasets/shisa-ai/eval-IFBench-results)
- **License**: ODC-BY-1.0 (consistent with original IFBench)

### Naming Convention

We use the `eval-{EVAL}-{type}` schema for all evaluation datasets:
- `eval-IFBench-results` - Model evaluation outputs
- `eval-IFBench-prompts` - Test prompts/questions (if separated)
- `eval-shisa-jp-tl-bench-results` - Another benchmark's results
- etc.

This ensures all assets for a given benchmark cluster together when sorted alphabetically.

### Why HuggingFace?

- **Size**: Results are ~250MB+ and growing; keeps code repo clean
- **Accessibility**: Easy programmatic access via `datasets` library
- **Community**: Others can contribute results via Pull Requests
- **Viewer**: Built-in dataset viewer for browsing results in browser
- **Independence**: Not limited by fork LFS quotas

## Repository Structure

### Code Repository (GitHub)

```
shisa-ai/IFBench/
├── evaluation_lib.py          # Evaluation logic (with our bug fixes)
├── instructions.py            # Instruction checkers (with our bug fixes)
├── shisa_generate_responses.py # Response generation script
├── run_eval.py                # Evaluation runner
├── data/                      # Test prompts
├── docs/                      # Documentation
│   └── IMPLEMENTATION-hf-results.md
└── results/                   # Git submodule → HuggingFace
```

### Results Repository (HuggingFace, mounted as submodule)

```
eval-IFBench-results/
├── README.md                           # Dataset card
├── {org}--{model-name}/               # One folder per model
│   ├── responses_{model-name}.jsonl   # Raw model responses
│   ├── eval_results_strict.jsonl      # Strict evaluation
│   └── eval_results_loose.jsonl       # Loose evaluation
└── ...
```

### Model Naming Convention

Model folders use HuggingFace model ID format with `/` replaced by `--`:
- `meta-llama--Llama-3.3-70B-Instruct`
- `shisa-ai--shisa-v2-llama3.3-70b`
- `gpt-4o-2024-08-06` (for API models without org)

## Setup

### Clone with Submodule

```bash
# Clone code repo with results submodule
git clone --recurse-submodules https://github.com/shisa-ai/IFBench.git

# Or if already cloned:
git submodule update --init --recursive
```

### Submodule Configuration

The results submodule is configured in `.gitmodules`:
```ini
[submodule "results"]
    path = results
    url = https://huggingface.co/datasets/shisa-ai/eval-IFBench-results
```

## Running Evaluations

### Using multieval (Recommended)

The multieval runner outputs directly to `results/`:

```bash
cd ~/multieval
./run-evals-py --model shisa-ai/my-model --evals ifbench
```

Results are written to `evals/IFBench/results/{model-slug}/`.

### Manual Evaluation

#### 1. Generate Responses

```bash
cd evals/IFBench
python shisa_generate_responses.py \
    --input_data data/IFBench_test.jsonl \
    --output_path results/{model-name}/responses_{model-name}.jsonl \
    --model_name {model-name} \
    --base_url http://localhost:8000/v1 \
    --workers 50
```

#### 2. Run Evaluation

```bash
python -m run_eval \
    --input_data=data/IFBench_test.jsonl \
    --input_response_data=results/{model-name}/responses_{model-name}.jsonl \
    --output_dir=results/{model-name}
```

This produces:
- `results/{model-name}/eval_results_strict.jsonl`
- `results/{model-name}/eval_results_loose.jsonl`

### Publishing Results

After evaluation, commit and push results to HuggingFace:

```bash
cd results/  # The submodule directory
git add {model-name}/
git commit -m "Add results for {model-name}"
git push

# Then update the submodule reference in the parent repo
cd ..
git add results
git commit -m "Update results submodule"
git push
```

Or use the HuggingFace Hub API:

```python
from huggingface_hub import HfApi

api = HfApi()
api.upload_folder(
    folder_path="./results/{model-name}",
    path_in_repo="{model-name}",
    repo_id="shisa-ai/eval-IFBench-results",
    repo_type="dataset",
)
```

## Programmatic Access

```python
from datasets import load_dataset

# Load all results
ds = load_dataset("shisa-ai/eval-IFBench-results")

# Or load specific model results
import json
from huggingface_hub import hf_hub_download

path = hf_hub_download(
    repo_id="shisa-ai/eval-IFBench-results",
    filename="meta-llama--Llama-3.3-70B-Instruct/eval_results_loose.jsonl",
    repo_type="dataset"
)
with open(path) as f:
    results = [json.loads(line) for line in f]
```

## Community Contributions

### Submitting Results

1. **Fork** the HF dataset repo
2. **Run IFBench evaluation** using the [official code](https://github.com/shisa-ai/IFBench)
3. **Add your results** in a folder named `{org}--{model-name}/`
4. **Open a Pull Request** via the Community tab

### Required Files

- `responses_{model-name}.jsonl` - Your model's responses
- `eval_results_strict.jsonl` - Strict evaluation output
- `eval_results_loose.jsonl` - Loose evaluation output

### Review Checklist

- [ ] Folder name matches HF model ID format
- [ ] `responses_{model-name}.jsonl` exists and valid
- [ ] `eval_results_strict.jsonl` exists and valid
- [ ] `eval_results_loose.jsonl` exists and valid
- [ ] No extraneous files
- [ ] Results are plausible (not all 0% or 100%)

## Related Repositories

- **Code**: [shisa-ai/IFBench](https://github.com/shisa-ai/IFBench) - Evaluation code (fork of allenai/IFBench)
- **Results**: [shisa-ai/eval-IFBench-results](https://huggingface.co/datasets/shisa-ai/eval-IFBench-results) - Results dataset
- **Original**: [allenai/IFBench](https://github.com/allenai/IFBench) - Upstream benchmark

## Replicating for Other Benchmarks

To set up the same pattern for another benchmark:

1. **Create HF dataset repo**: `shisa-ai/eval-{BENCHMARK}-results`
2. **Add as submodule**: `git submodule add https://huggingface.co/datasets/shisa-ai/eval-{BENCHMARK}-results results`
3. **Update eval runner** to output to `results/{model-slug}/`
4. **Create documentation** following this template
