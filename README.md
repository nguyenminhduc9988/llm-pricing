# llm-pricing

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-green.svg)](#)

> Zero-dependency LLM API pricing data and a tiny cost estimator for Python.

Every LLM app needs to answer *"how much will this request cost?"* — but pricing
is scattered across provider docs, changes often, and nobody wants to hardcode a
spreadsheet. `llm-pricing` ships a single in-memory pricing table for the major
models (OpenAI, Anthropic, Google, Meta, DeepSeek, Mistral) and a one-liner that
turns token counts into USD.

- **No dependencies** — pure Python stdlib. No `requests`, no network calls.
- **Fuzzy model resolution** — pass `"gpt-4o-2024-08-06"` or `"claude-3-5-sonnet-20241022"`, it finds the base model.
- **Cache-aware** — supports prompt-caching read/write pricing where providers offer it.
- **CLI included** — `llm-pricing gpt-4o --input 1200 --output 300`.
- **127 lines of logic, fully tested.**

## Install

```bash
pip install llm-pricing
# or, no install needed:
pipx run llm-pricing gpt-4o --input 1000 --output 500
```

## Quick start

```python
from llm_pricing import estimate_cost, format_cost

cost = estimate_cost("gpt-4o", input_tokens=1200, output_tokens=300)
print(format_cost(cost))   # "$0.0060"

# With Anthropic prompt caching:
cost = estimate_cost(
    "claude-3-5-sonnet",
    input_tokens=500,
    output_tokens=200,
    cache_read_tokens=8000,
    cache_write_tokens=0,
)
print(format_cost(cost))   # "$0.0069"
```

## API

```python
from llm_pricing import list_models, get_model, estimate_cost, format_cost

list_models()             # -> ["claude-3-5-sonnet", "gpt-4o", ...]  (sorted)
get_model("gpt-4o")       # -> {"input": 2.5, "output": 10.0, "cache_read": 1.25}
get_model("gpt-4o-2024-08-06")  # alias-resolved -> same as above
estimate_cost(model, input_tokens, output_tokens, cache_read_tokens=0, cache_write_tokens=0)
                          # -> float, USD
format_cost(0.006)        # -> "$0.0060"
```

All prices are **USD per 1,000,000 tokens**. `estimate_cost` converts internally,
so you pass *raw token counts*.

## CLI

```bash
# List every known model and its per-1M-token prices
llm-pricing --list

# Estimate a single request
llm-pricing gpt-4o --input 1200 --output 300
# gpt-4o: $0.006000  (in=$3.00/1M, out=$12.00/1M)

# With caching
llm-pricing claude-3-5-sonnet --input 500 --output 200 --cache-read 8000
```

## Supported models (v0.1.0)

| Provider   | Models |
|------------|--------|
| OpenAI     | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, o1, o1-mini, o3-mini |
| Anthropic  | claude-3-5-sonnet, claude-3-5-haiku, claude-3-opus, claude-3-sonnet, claude-3-haiku |
| Google     | gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash |
| Meta       | llama-3.1-405b, llama-3.1-70b, llama-3.1-8b |
| DeepSeek   | deepseek-chat, deepseek-reasoner |
| Mistral    | mistral-large, mistral-small |

> **Disclaimer:** Prices are sourced from public provider pages and are
> approximate. Providers change pricing frequently — always verify against the
> official source before relying on these numbers for billing.

## Why?

Token cost is the #1 operational metric for any LLM app, yet it's the thing most
dashboards get wrong because nobody centralizes the price list. This library is
that price list, with a five-function API and zero things to configure.

## License

MIT © [Duc Nguyen](https://github.com/nguyenminhduc9988)
