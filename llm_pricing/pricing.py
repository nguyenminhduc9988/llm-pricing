"""Pricing table and estimation logic.

All amounts are USD per 1,000,000 (1M) tokens. Keys are canonical base
model names; callers may pass dated or suffixed variants (e.g.
``"gpt-4o-2024-08-06"``) and ``resolve_model`` will map them back.
"""

from __future__ import annotations

import re
from typing import Dict

# {model: {"input": x, "output": y, ["cache_read": r], ["cache_write": w]}}
# All values: USD per 1,000,000 tokens.
PRICING: Dict[str, Dict[str, float]] = {
    # --- OpenAI ---
    "gpt-4o":            {"input": 2.50,  "output": 10.00, "cache_read": 1.25},
    "gpt-4o-mini":       {"input": 0.15,  "output": 0.60,  "cache_read": 0.075},
    "gpt-4-turbo":       {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo":     {"input": 0.50,  "output": 1.50},
    "o1":                {"input": 15.00, "output": 60.00},
    "o1-mini":           {"input": 3.00,  "output": 12.00},
    "o3-mini":           {"input": 1.10,  "output": 4.40,  "cache_read": 0.55},
    # --- Anthropic ---
    "claude-3-5-sonnet": {"input": 3.00,  "output": 15.00, "cache_read": 0.30,  "cache_write": 3.75},
    "claude-3-5-haiku":  {"input": 0.80,  "output": 4.00,  "cache_read": 0.08,  "cache_write": 1.00},
    "claude-3-opus":     {"input": 15.00, "output": 75.00},
    "claude-3-sonnet":   {"input": 3.00,  "output": 15.00},
    "claude-3-haiku":    {"input": 0.25,  "output": 1.25},
    # --- Google ---
    "gemini-1.5-pro":    {"input": 1.25,  "output": 5.00,  "cache_read": 0.3125},
    "gemini-1.5-flash":  {"input": 0.075, "output": 0.30,  "cache_read": 0.01875},
    "gemini-2.0-flash":  {"input": 0.10,  "output": 0.40},
    # --- Meta (hosted, e.g. Together/Groq) ---
    "llama-3.1-405b":    {"input": 2.70,  "output": 2.70},
    "llama-3.1-70b":     {"input": 0.59,  "output": 0.79},
    "llama-3.1-8b":      {"input": 0.05,  "output": 0.08},
    # --- DeepSeek ---
    "deepseek-chat":     {"input": 0.14,  "output": 0.28,  "cache_read": 0.014},
    "deepseek-reasoner": {"input": 0.55,  "output": 2.19},
    # --- Mistral ---
    "mistral-large":     {"input": 2.00,  "output": 6.00},
    "mistral-small":     {"input": 0.20,  "output": 0.60},
}

# One or more trailing date/qualifier suffixes, stripped in a single pass.
_DATE_SUFFIX = re.compile(r"(?:-\d{4}-\d{2}-\d{2}|-\d{8}|-latest|-preview)+$")


class UnknownModelError(KeyError):
    """Raised when a model name cannot be resolved to a known entry."""


def list_models() -> list:
    """Return the canonical model names, sorted alphabetically."""
    return sorted(PRICING.keys())


def _normalize(name: str) -> str:
    """Lowercase and strip common dated/qualifier suffixes (one pass)."""
    return _DATE_SUFFIX.sub("", name.strip().lower())


def resolve_model(name: str) -> str:
    """Return the canonical model key for a (possibly suffixed) ``name``.

    Resolution order:
      1. Exact key match.
      2. Normalized match (date/qualifier suffixes stripped, lowercased).
      3. Prefix match — but ONLY when a single canonical key extends the
         prefix. Ambiguous family prefixes such as ``"claude"`` or
         ``"deepseek"`` match several keys and deliberately raise rather
         than silently pick an arbitrary model.
    """
    if name in PRICING:
        return name
    norm = _normalize(name)
    if norm in PRICING:
        return norm
    candidates = [k for k in PRICING if k.startswith(norm + "-")]
    if len(candidates) == 1:
        return candidates[0]
    raise UnknownModelError(
        f"Unknown model: {name!r}. Known: {', '.join(list_models()[:6])} ..."
    )


def get_model(name: str) -> Dict[str, float]:
    """Return the price dict (USD per 1M tokens) for ``name``."""
    return PRICING[resolve_model(name)]


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """Estimate the USD cost of a request.

    ``input_tokens`` are charged at the (non-cached) input price;
    ``cache_read_tokens`` and ``cache_write_tokens`` are charged at the
    provider's cache rates when published. Fallbacks for providers that do
    not publish a given rate:

      * ``cache_read``  -> input price  (reads are never costlier than input)
      * ``cache_write`` -> input price * 1.25  (Anthropic-style write premium;
        conservative over-estimate when a provider charges for writes but
        omits the rate)
    """
    if min(input_tokens, output_tokens, cache_read_tokens, cache_write_tokens) < 0:
        raise ValueError("token counts must be non-negative")
    p = get_model(model)
    per_m = 1_000_000.0

    cache_read_rate = p.get("cache_read", p["input"])
    cache_write_rate = p.get("cache_write", p["input"] * 1.25)

    cost = (
        input_tokens * p["input"]
        + output_tokens * p["output"]
        + cache_read_tokens * cache_read_rate
        + cache_write_tokens * cache_write_rate
    ) / per_m
    return cost


def format_cost(usd: float) -> str:
    """Format a USD amount compactly. Small costs keep 4-6 decimals."""
    if usd >= 1.0:
        return f"${usd:,.2f}"
    if usd >= 0.001:
        return f"${usd:.4f}"
    return f"${usd:.6f}"
