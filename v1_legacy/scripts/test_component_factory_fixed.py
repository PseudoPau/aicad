"""Headless test for `backend.M3.component_factory`.

Creates three components with fixed sizes, writes bounding-box info
and exports each part to STEP in `output/test_components/`.

Run with the same Python environment used for the app, e.g.:
  D:/miniconda3/envs/aicad_hackathon/python.exe scripts/test_component_factory_fixed.py
"""
import json
import traceback
from pathlib import Path

from backend.M3.component_factory import UpRightBuilder, BeamBuilder, DeckingBuilder
from utils.file_manager import ensure_dir
from utils.logger import get_logger

logger = get_logger("test_component_factory_fixed")


def try_bbox(part):
    try:
        bb = part.BoundingBox()
        return {"xlen": float(bb.xlen), "ylen": float(bb.ylen), "zlen": float(bb.zlen)}
    except Exception:
        try:
            bb = part.val().BoundingBox()
            return {"xlen": float(bb.xlen), "ylen": float(bb.ylen), "zlen": float(bb.zlen)}
        except Exception:
            return None


def try_export(part, path: Path):
    try:
        # Some CadQuery objects expose exportStep directly
        if hasattr(part, "exportStep"):
            part.exportStep(str(path))
        else:
            # wrap in Workplane and export
            import cadquery as cq
            wrapped = cq.Workplane("XY").add(part).val()
            if hasattr(wrapped, "exportStep"):
                wrapped.exportStep(str(path))
            else:
                raise RuntimeError("exportStep not available on wrapped part")
        return True
    except Exception as e:
        logger.error(f"Failed to export {path}: {e}")
        logger.debug(traceback.format_exc())
        return False


def main():
    out_dir = Path("output") / "test_components"
    ensure_dir(out_dir)

    log_path = out_dir / "generation.log"
    info_path = out_dir / "components_info.json"

    results = {}

    try:
        # Hardcoded sizes
        upright_h = 6000.0
        upright_section = "80x60"

        beam_len = 1000.0
        beam_section = "50x100"

        decking_w = 2400.0
        decking_d = 1000.0
        decking_th = 10.0

        # Build parts
        logger.info("Building upright...")
        upright = UpRightBuilder.build(upright_h, upright_section)
        upright_bb = try_bbox(upright)
        results["upright"] = {"bbox": upright_bb}
        upright_step = out_dir / "upright.step"
        results["upright"]["exported"] = try_export(upright, upright_step)

        logger.info("Building beam...")
        beam = BeamBuilder.build(beam_len, beam_section)
        beam_bb = try_bbox(beam)
        results["beam"] = {"bbox": beam_bb}
        beam_step = out_dir / "beam.step"
        results["beam"]["exported"] = try_export(beam, beam_step)

        logger.info("Building decking...")
        decking = DeckingBuilder.build(decking_w, decking_d, decking_th)
        decking_bb = try_bbox(decking)
        results["decking"] = {"bbox": decking_bb}
        decking_step = out_dir / "decking.step"
        results["decking"]["exported"] = try_export(decking, decking_step)

        # Write components info
        with open(info_path, "w", encoding="utf-8") as jf:
            json.dump(results, jf, indent=2, ensure_ascii=False)

        with open(log_path, "w", encoding="utf-8") as gl:
            gl.write("SUCCESS: Components built and export attempted\n")
            gl.write(json.dumps(results, indent=2, ensure_ascii=False))

        print("Test completed. See:")
        print(f"  - {log_path}")
        print(f"  - {info_path}")
        print(f"  - STEP files in {out_dir}")

    except Exception as e:
        tb = traceback.format_exc()
        with open(log_path, "w", encoding="utf-8") as gl:
            gl.write(f"EXCEPTION: {e}\n")
            gl.write(tb)
        print("Test failed. See generation.log for traceback.")
        raise


if __name__ == '__main__':
    main()
