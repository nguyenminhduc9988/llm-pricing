"""Zero-dependency LLM API pricing data and cost estimator.

All public prices are USD per 1,000,000 (1M) tokens, sourced from the
respective provider's public pricing page. Prices are approximate and
subject to change.
"""

from .pricing import (
    PRICING,
    list_models,
    get_model,
    resolve_model,
    estimate_cost,
    format_cost,
    UnknownModelError,
)

__version__ = "0.1.0"
__all__ = [
    "PRICING",
    "list_models",
    "get_model",
    "resolve_model",
    "estimate_cost",
    "format_cost",
    "UnknownModelError",
]
