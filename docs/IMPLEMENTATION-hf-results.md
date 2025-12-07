# IFBench Results Management

This document describes how we manage IFBench evaluation results using HuggingFace Datasets.

## Overview

We store evaluation results in a dedicated HuggingFace dataset repository:
- **Repository**: [shisa-ai/results-IFBench](https://huggingface.co/datasets/shisa-ai/results-IFBench)
- **License**: ODC-BY-1.0 (consistent with original IFBench)

### Why HuggingFace?

- **Size**: Results are ~2GB+ and growing; too large for regular git
- **Accessibility**: Easy programmatic access via `datasets` library
- **Community**: Others can contribute results via Pull Requests
- **Viewer**: Built-in dataset viewer for browsing results in browser
- **Independence**: Not limited by fork LFS quotas

## Directory Structure

```
results-IFBench/
├── README.md                           # Dataset card
├── {org}--{model-name}/               # One folder per model
│   ├── responses_{model-name}.jsonl   # Raw model responses
│   ├── eval_results_strict.jsonl      # Strict evaluation
│   └── eval_results_loose.jsonl       # Loose evaluation
└── ...
```

### Naming Convention

Model folders use HuggingFace model ID format with `/` replaced by `--`:
- `meta-llama--Llama-3.3-70B-Instruct`
- `shisa-ai--shisa-v2-llama3.3-70b`
- `gpt-4o-2024-08-06` (for API models without org)

## Running Evaluations

### 1. Generate Responses

Using our custom script for OpenAI-compatible APIs:

```bash
python shisa_generate_responses.py \
    --input_data data/IFBench_test.jsonl \
    --output_path {model-name}/responses_{model-name}.jsonl \
    --model_name {model-name} \
    --base_url http://localhost:8000/v1 \
    --workers 50
```

### 2. Run Evaluation

```bash
python -m run_eval \
    --input_data=data/IFBench_test.jsonl \
    --input_response_data={model-name}/responses_{model-name}.jsonl \
    --output_dir={model-name}
```

This produces:
- `eval_results_strict.jsonl`
- `eval_results_loose.jsonl`

### 3. Upload to HuggingFace

```bash
# Clone the results repo
git clone https://huggingface.co/datasets/shisa-ai/results-IFBench
cd results-IFBench

# Copy results
cp -r /path/to/{model-name} .

# Commit and push
git add {model-name}/
git commit -m "Add results for {model-name}"
git push
```

Or use the HuggingFace Hub API:

```python
from huggingface_hub import HfApi

api = HfApi()
api.upload_folder(
    folder_path="./{model-name}",
    path_in_repo="{model-name}",
    repo_id="shisa-ai/results-IFBench",
    repo_type="dataset",
)
```

## Evaluation Status

### Completed Evaluations

| Model | Strict | Loose | Date | Notes |
|-------|--------|-------|------|-------|
| meta-llama--Llama-3.3-70B-Instruct | | | 2024-11 | |
| meta-llama--Llama-3.1-8B-Instruct | | | 2024-11 | |
| shisa-ai--shisa-v2-llama3.3-70b | | | 2024-11 | |
| gpt-4o-2024-08-06 | | | 2024-11 | |
| *... ~90+ models evaluated* | | | | |

### Pending Upload

All results in the local `IFBench/` directory need to be uploaded to HuggingFace.

**To upload all existing results:**

```bash
cd /tmp/results-IFBench

# Copy all model result directories (exclude non-result folders)
for dir in /data/multieval/evals/IFBench/*/; do
    name=$(basename "$dir")
    # Skip non-result directories
    [[ "$name" =~ ^(data|eval|eval2|docs|__pycache__)$ ]] && continue
    # Skip if no eval results
    [[ -f "$dir/eval_results_loose.jsonl" ]] || continue
    cp -r "$dir" .
done

git add .
git commit -m "Add evaluation results for ~90 models"
git push
```

## Community Contributions

### Accepting Results

1. Contributors fork the HF repo
2. They add their `{model-name}/` folder with required files
3. They open a Pull Request via the Community tab
4. We review:
   - Folder naming follows convention
   - All 3 required files present
   - JSONL format is valid
   - Results appear reasonable (spot check)
5. Merge if approved

### Review Checklist

- [ ] Folder name matches HF model ID format
- [ ] `responses_{model-name}.jsonl` exists and valid
- [ ] `eval_results_strict.jsonl` exists and valid
- [ ] `eval_results_loose.jsonl` exists and valid
- [ ] No extraneous files
- [ ] Results are plausible (not all 0% or 100%)

## Related Repositories

- **Code**: [shisa-ai/IFBench](https://github.com/shisa-ai/IFBench) - Evaluation code (fork of allenai/IFBench)
- **Results**: [shisa-ai/results-IFBench](https://huggingface.co/datasets/shisa-ai/results-IFBench) - This results dataset
- **Original**: [allenai/IFBench](https://github.com/allenai/IFBench) - Upstream benchmark

## Future Work

- [ ] Add leaderboard generation script from results
- [ ] Automate result upload in evaluation pipeline
- [ ] Add CI validation for PR submissions
- [ ] Create similar repos for other benchmarks (shisa-jp-tl-bench, etc.)
