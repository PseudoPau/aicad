import json
import traceback
from pathlib import Path
from datetime import datetime
import sys

try:
    from backend.M3.assembly_manager import AssemblyBuilder
except Exception as e:
    print(f"Failed to import AssemblyBuilder: {e}")
    print(traceback.format_exc())
    sys.exit(2)


def main():
    base = Path("output") / "analysis"
    param_file = base / "input_img_02_parameters.json"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = base / f"headless_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    gen_log = out_dir / "generation.log"

    if not param_file.exists():
        with open(gen_log, "w", encoding="utf-8") as gl:
            gl.write(f"Param file not found: {param_file}\n")
        print(f"Param file not found: {param_file}")
        sys.exit(1)

    try:
        with open(param_file, "r", encoding="utf-8") as f:
            params = json.load(f)

        builder = AssemblyBuilder(params)
        step_path = str(out_dir / "warehouse_assembly.step")
        success = builder.export_step(step_path)

        with open(gen_log, "w", encoding="utf-8") as gl:
            if success:
                gl.write(f"SUCCESS: STEP exported to {step_path}\n")
            else:
                gl.write(f"FAIL: STEP export failed for path {step_path}\n")

        print(f"Headless export finished. success={success}. See {gen_log}")
        if not success:
            sys.exit(3)
    except Exception as e:
        tb = traceback.format_exc()
        with open(gen_log, "w", encoding="utf-8") as gl:
            gl.write(f"EXCEPTION: {e}\n")
            gl.write(tb)
        print(f"Exception during headless export: {e}")
        print(tb)
        sys.exit(4)


if __name__ == '__main__':
    main()
