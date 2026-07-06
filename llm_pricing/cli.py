"""Command-line interface: ``llm-pricing [model --input N --output M]``."""

from __future__ import annotations

import argparse
import sys

from .pricing import estimate_cost, format_cost, get_model, list_models


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-pricing",
        description="Estimate the USD cost of an LLM request from token counts.",
    )
    parser.add_argument("model", nargs="?", help="Model name (e.g. gpt-4o).")
    parser.add_argument("--input", type=int, default=0, dest="input_tokens", help="Input (prompt) token count.")
    parser.add_argument("--output", type=int, default=0, dest="output_tokens", help="Output (completion) token count.")
    parser.add_argument("--cache-read", type=int, default=0, dest="cache_read_tokens", help="Cache-read token count.")
    parser.add_argument("--cache-write", type=int, default=0, dest="cache_write_tokens", help="Cache-write token count.")
    parser.add_argument("--list", action="store_true", help="List every known model and its per-1M-token prices.")
    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.list or args.model is None:
        print(f"{'model':<22} {'input/1M':>10} {'output/1M':>10} {'cache_read/1M':>14} {'cache_write/1M':>15}")
        print("-" * 75)
        for m in list_models():
            p = get_model(m)
            print(
                f"{m:<22} {p['input']:>10.4f} {p['output']:>10.4f} "
                f"{p.get('cache_read', '')!s:>14} {p.get('cache_write', '')!s:>15}"
            )
        return 0

    try:
        cost = estimate_cost(
            args.model,
            input_tokens=args.input_tokens,
            output_tokens=args.output_tokens,
            cache_read_tokens=args.cache_read_tokens,
            cache_write_tokens=args.cache_write_tokens,
        )
        p = get_model(args.model)
        resolved = (
            f"{args.model}: {format_cost(cost)}  "
            f"(in=${p['input']:.4f}/1M, out=${p['output']:.4f}/1M)"
        )
        print(resolved)
        return 0
    except Exception as exc:  # noqa: BLE001 - surface to CLI user
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
