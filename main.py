"""Command line entry point for the aicad prototype.

The fixture path is model-free and is the first reproducible health check.
Vision and STEP export are opt-in operations.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from core.pipeline import (
    DEFAULT_INSTANCE_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SCHEMA_PATH,
    run_fixture,
)

BASE_DIR = Path(__file__).resolve().parent
INPUT_IMAGE = BASE_DIR / "tests" / "rack_photo.jpg"
FEW_SHOT_PATH = DEFAULT_INSTANCE_PATH


def run_ai_cad_pipeline(
    image_path: str | Path = INPUT_IMAGE,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict:
    """Run the optional GLM vision step, then the deterministic pipeline."""
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        return {"ok": False, "error": "ZHIPU_API_KEY is required for vision mode"}
    try:
        from core.vision_agent import VisionAgent
    except ImportError as exc:
        return {"ok": False, "error": f"vision dependencies are unavailable: {exc}"}

    schema_text = DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8")
    few_shot_text = FEW_SHOT_PATH.read_text(encoding="utf-8")
    try:
        extracted = VisionAgent(api_key).extract_params(
            str(image_path), schema_text, few_shot_text
        )
    except Exception as exc:
        return {"ok": False, "error": f"vision extraction failed: {exc}"}

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    extracted_path = output / "extracted_instance.json"
    extracted_path.write_text(
        json.dumps(extracted, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    result = run_fixture(
        extracted_path,
        DEFAULT_SCHEMA_PATH,
        output,
        export_step_file=True,
    )
    result["extracted_instance_path"] = str(extracted_path)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="aicad deterministic fixture and vision pipeline")
    parser.add_argument(
        "--fixture",
        nargs="?",
        const=str(DEFAULT_INSTANCE_PATH),
        help="run model-free validation and preview for a JSON fixture",
    )
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH))
    parser.add_argument("--image", default=str(INPUT_IMAGE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--export-step",
        action="store_true",
        help="attempt STEP export after fixture validation; requires CadQuery",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv(BASE_DIR / ".env")
    args = _parser().parse_args(argv)
    if args.fixture:
        result = run_fixture(
            args.fixture,
            args.schema,
            args.output_dir,
            export_step_file=args.export_step,
        )
    else:
        result = run_ai_cad_pipeline(args.image, args.output_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
