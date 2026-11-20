"""Optional CadQuery smoke test for the fixture translator.

The deterministic pipeline is covered by ``tests/``. This script only checks
the optional CAD adapter and exits cleanly with a readable message when
CadQuery is not installed.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="aicad CadQuery translator smoke test")
    parser.add_argument("--instance", type=Path, default=Path("tests/shelf_instance.json"))
    parser.add_argument("--output-step", type=Path, default=Path("output/test_result.step"))
    args = parser.parse_args()

    if importlib.util.find_spec("cadquery") is None:
        print("CadQuery is not installed; skipping optional STEP smoke test.")
        return 0

    from cadquery import exporters
    from core.translator import run_translation

    if not args.instance.exists():
        print(f"Instance not found: {args.instance}")
        return 2

    try:
        assembly = run_translation(str(args.instance))
        args.output_step.parent.mkdir(parents=True, exist_ok=True)
        exporters.export(assembly.toCompound(), str(args.output_step))
    except Exception as exc:
        print(f"STEP smoke test failed: {exc}")
        return 1

    print(f"STEP smoke test passed: {args.output_step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
