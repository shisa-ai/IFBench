#!/usr/bin/env python3
# coding=utf-8
# Generation script for IFBench using OpenAI-compatible API.

import os
import sys
import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def get_response_single(client, model_name, prompt, temperature=0.0, max_tokens=2048):
    """Get a single response from the OpenAI-compatible API."""
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"[generate] Error for prompt: {str(e)[:100]}", file=sys.stderr)
        return ""

def generate_responses(
    input_data_path: str,
    output_path: str,
    model_name: str,
    base_url: str = "http://localhost:8000/v1",
    api_key: str = "EMPTY",
    temperature: float = 0.0,
    max_tokens: int = 2048,
    workers: int = 50,
):
    """Generate responses for all prompts in the input data."""
    from openai import OpenAI

    # Setup client
    client = OpenAI(base_url=base_url, api_key=api_key)

    # Load input data
    print(f"[generate] Loading data from {input_data_path}")
    prompts = []
    with open(input_data_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            prompts.append(data["prompt"])

    print(f"[generate] Found {len(prompts)} prompts to process")
    print(f"[generate] Model: {model_name}")
    print(f"[generate] Base URL: {base_url}")
    print(f"[generate] Workers: {workers}")
    print(f"[generate] Temperature: {temperature}")
    print(f"[generate] Max tokens: {max_tokens}")

    # Generate responses in parallel
    results = [None] * len(prompts)

    def process_prompt(idx, prompt):
        response = get_response_single(client, model_name, prompt, temperature, max_tokens)
        return idx, prompt, response

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_prompt, i, p): i for i, p in enumerate(prompts)
        }

        with tqdm(total=len(prompts), desc="Generating responses") as pbar:
            for future in as_completed(futures):
                idx, prompt, response = future.result()
                results[idx] = {"prompt": prompt, "response": response}
                pbar.update(1)

    # Save results
    print(f"[generate] Saving responses to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"[generate] ✅ Generated {len(results)} responses")

def main():
    parser = argparse.ArgumentParser(description="Generate responses for IFBench")
    parser.add_argument("--input_data", required=True, help="Path to IFBench_test.jsonl")
    parser.add_argument("--output_path", required=True, help="Path to save responses")
    parser.add_argument("--model_name", required=True, help="Model name/identifier")
    parser.add_argument("--base_url", default="http://localhost:8000/v1", help="API base URL")
    parser.add_argument("--api_key", default=None, help="API key (or set via env)")
    parser.add_argument("--api_key_env", default="OPENAI_COMPATIBLE_API_KEY", help="Env var for API key")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature")
    parser.add_argument("--max_tokens", type=int, default=2048, help="Max tokens to generate")
    parser.add_argument("--workers", type=int, default=50, help="Number of parallel workers")

    args = parser.parse_args()

    # Resolve API key
    api_key = args.api_key
    if not api_key:
        api_key = os.environ.get(args.api_key_env, "EMPTY")

    generate_responses(
        input_data_path=args.input_data,
        output_path=args.output_path,
        model_name=args.model_name,
        base_url=args.base_url,
        api_key=api_key,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        workers=args.workers,
    )

if __name__ == "__main__":
    main()
