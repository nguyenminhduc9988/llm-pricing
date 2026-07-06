"""Tests for llm_pricing — pure stdlib, run with ``python -m pytest`` or unittest."""

import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from llm_pricing import (
    PRICING,
    list_models,
    get_model,
    resolve_model,
    estimate_cost,
    format_cost,
    UnknownModelError,
)


class TestPricing(unittest.TestCase):

    def test_list_models_sorted_and_nonempty(self):
        models = list_models()
        self.assertGreater(len(models), 15)
        self.assertEqual(models, sorted(models))

    def test_get_model_exact(self):
        self.assertEqual(get_model("gpt-4o")["input"], 2.50)

    def test_resolve_dated_suffix(self):
        self.assertEqual(resolve_model("gpt-4o-2024-08-06"), "gpt-4o")
        self.assertEqual(resolve_model("claude-3-5-sonnet-20241022"), "claude-3-5-sonnet")
        self.assertEqual(resolve_model("GPT-4O-MINI-LATEST"), "gpt-4o-mini")

    def test_resolve_prefix(self):
        # "deepseek" should resolve to the longest deepseek-* key present.
        self.assertIn(resolve_model("deepseek"), ("deepseek-chat", "deepseek-reasoner"))

    def test_resolve_unknown_raises(self):
        with self.assertRaises(UnknownModelError):
            resolve_model("totally-made-up-model-xyz")

    def test_estimate_cost_gpt4o(self):
        # 1.2K input @ $2.5/1M + 300 output @ $10/1M
        # = (1200*2.5 + 300*10)/1e6 = (3000 + 3000)/1e6 = 0.006
        cost = estimate_cost("gpt-4o", input_tokens=1200, output_tokens=300)
        self.assertAlmostEqual(cost, 0.006, places=8)

    def test_estimate_cost_full_1m(self):
        # 1M input + 1M output should equal input+output per-1M prices.
        cost = estimate_cost("gpt-4o-mini", input_tokens=1_000_000, output_tokens=1_000_000)
        p = PRICING["gpt-4o-mini"]
        self.assertAlmostEqual(cost, p["input"] + p["output"], places=6)

    def test_estimate_cost_caching(self):
        # claude-3-5-sonnet: in=3, out=15, cache_read=0.30 per 1M
        # 500*3 + 200*15 + 8000*0.30 = 1500 + 3000 + 2400 = 6900 -> /1e6
        cost = estimate_cost(
            "claude-3-5-sonnet",
            input_tokens=500,
            output_tokens=200,
            cache_read_tokens=8000,
        )
        self.assertAlmostEqual(cost, 6900 / 1_000_000, places=8)

    def test_cache_falls_back_to_input_when_absent(self):
        # gpt-4-turbo has no cache_read -> falls back to input price.
        p = PRICING["gpt-4-turbo"]
        self.assertNotIn("cache_read", p)
        cost = estimate_cost("gpt-4-turbo", input_tokens=0, output_tokens=0, cache_read_tokens=1_000_000)
        self.assertAlmostEqual(cost, p["input"], places=6)

    def test_negative_tokens_rejected(self):
        with self.assertRaises(ValueError):
            estimate_cost("gpt-4o", input_tokens=-1, output_tokens=0)

    def test_zero_cost(self):
        self.assertEqual(estimate_cost("gpt-4o", input_tokens=0, output_tokens=0), 0.0)

    def test_format_cost(self):
        self.assertEqual(format_cost(12.5), "$12.50")
        self.assertEqual(format_cost(0.006), "$0.0060")
        self.assertEqual(format_cost(0.000012), "$0.000012")


class TestCLI(unittest.TestCase):

    def test_cli_estimate(self):
        from llm_pricing.cli import main
        rc = main(["gpt-4o", "--input", "1200", "--output", "300"])
        self.assertEqual(rc, 0)

    def test_cli_list(self):
        from llm_pricing.cli import main
        from io import StringIO
        import contextlib
        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["--list"])
        self.assertEqual(rc, 0)
        self.assertIn("gpt-4o", buf.getvalue())

    def test_cli_unknown_model(self):
        from llm_pricing.cli import main
        rc = main(["nope-xyz", "--input", "1"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
