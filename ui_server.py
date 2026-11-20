"""Local aicad workbench. Run: python ui_server.py --port 8765."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import mimetypes
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
BUILD_LOCK = threading.Lock()
ARTIFACTS: dict[str, Path] = {}
STORAGE = tempfile.TemporaryDirectory(prefix="aicad-ui-")


def _add_box(vertices, faces, origin, size):
    ox, oy, oz = origin
    sx, sy, sz = size
    base = len(vertices)
    vertices.extend([
        [ox, oy, oz], [ox + sx, oy, oz], [ox + sx, oy + sy, oz], [ox, oy + sy, oz],
        [ox, oy, oz + sz], [ox + sx, oy, oz + sz],
        [ox + sx, oy + sy, oz + sz], [ox, oy + sy, oz + sz],
    ])
    faces.extend([
        [base + 0, base + 1, base + 2], [base + 0, base + 2, base + 3],
        [base + 4, base + 6, base + 5], [base + 4, base + 7, base + 6],
        [base + 0, base + 4, base + 5], [base + 0, base + 5, base + 1],
        [base + 1, base + 5, base + 6], [base + 1, base + 6, base + 2],
        [base + 2, base + 6, base + 7], [base + 2, base + 7, base + 3],
        [base + 3, base + 7, base + 4], [base + 3, base + 4, base + 0],
    ])


def _unit(vector):
    length = sum(value * value for value in vector) ** 0.5
    if length <= 1e-9:
        return (1.0, 0.0, 0.0)
    return tuple(value / length for value in vector)


def _cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _add_segment(vertices, faces, start, end, width, thickness):
    start = tuple(start)
    end = tuple(end)
    axis = _unit(tuple(end[index] - start[index] for index in range(3)))
    reference = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (0.0, 1.0, 0.0)
    side = _unit(_cross(axis, reference))
    normal = _unit(_cross(axis, side))
    half_side, half_normal = width / 2, thickness / 2
    corners = []
    for point in (start, end):
        for side_sign, normal_sign in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            corners.append([
                point[index]
                + side[index] * half_side * side_sign
                + normal[index] * half_normal * normal_sign
                for index in range(3)
            ])
    base = len(vertices)
    vertices.extend(corners)
    faces.extend([
        [base + 0, base + 1, base + 2], [base + 0, base + 2, base + 3],
        [base + 4, base + 6, base + 5], [base + 4, base + 7, base + 6],
        [base + 0, base + 4, base + 5], [base + 0, base + 5, base + 1],
        [base + 1, base + 5, base + 6], [base + 1, base + 6, base + 2],
        [base + 2, base + 6, base + 7], [base + 2, base + 7, base + 3],
        [base + 3, base + 7, base + 4], [base + 3, base + 4, base + 0],
    ])


def _mesh_from_preview(preview):
    """Turn the deterministic manifest into a review-only browser mesh.

    This keeps browser verification available without claiming that a CAD solid
    or STEP file was produced. CadQuery remains the only STEP path.
    """
    vertices, faces = [], []
    box_kinds = {"base_plate", "column", "beam", "panel"}
    for item in preview.get("items", []):
        if item.get("kind") in box_kinds:
            _add_box(vertices, faces, item["origin"], item["size"])
        elif item.get("kind") == "bracing":
            _add_segment(
                vertices,
                faces,
                item["start"],
                item["end"],
                item.get("width", 30.0),
                item.get("thickness", 2.0),
            )
    return {"vertices": vertices, "faces": faces}


def check_document(data):
    from jsonschema import Draft7Validator
    schema = json.loads((BASE / "schema/assembly_schema.json").read_text(encoding="utf-8-sig"))
    errors = [{"path": ".".join(map(str, e.absolute_path)), "message": e.message}
              for e in Draft7Validator(schema).iter_errors(data)]
    # UI and CLI share the domain contract; never maintain a second set of rules.
    try:
        from core.pipeline import validate_instance
    except ImportError:
        return errors + [{"path": "", "message": "缺少领域校验模块 core.pipeline，需先完成运行基线"}]
    if not errors:
        result = validate_instance(data)
        errors.extend(result.get("errors", []))
    return errors


def build_document(data):
    errors = check_document(data)
    if errors:
        return {"ok": False, "stage": "validation", "errors": errors}
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    revision = hashlib.sha256(canonical.encode()).hexdigest()[:20]
    if importlib.util.find_spec("cadquery") is None:
        from core.pipeline import build_preview

        preview = build_preview(data)
        if not preview["ok"]:
            return {"ok": False, "stage": "validation", "errors": preview["validation"]["errors"]}
        mesh = _mesh_from_preview(preview)
        return {
            "ok": True,
            "preview_mode": "manifest",
            "cadquery": False,
            "step_available": False,
            "revision": revision,
            "mesh": mesh,
            "solids": len(preview["items"]),
            "checks": ["参数校验通过", "Layout manifest 构造预览已生成"],
            "limits": ["CadQuery 未安装：当前为布局复核预览，STEP 仍不可用"],
        }
    from cadquery import exporters
    from core.translator import run_translation
    folder = Path(STORAGE.name) / revision
    folder.mkdir(exist_ok=True)
    source = folder / "parameters.json"
    source.write_text(canonical, encoding="utf-8")
    with BUILD_LOCK:
        assembly = run_translation(str(source))
        shape = assembly.toCompound()
        valid = shape.isValid()
        if not valid:
            return {"ok": False, "stage": "geometry", "errors": [{"path": "", "message": "生成的几何未通过 OpenCASCADE 有效性检查"}]}
        verts, faces = shape.tessellate(2.0, 0.2)
        mesh = {"vertices": [[v.x, v.y, v.z] for v in verts], "faces": [list(f) for f in faces]}
        step = folder / "assembly.step"
        exporters.export(shape, str(step))
        # Export only becomes available after the exact previewed shape is saved.
        ARTIFACTS[revision] = step
        solids = len(shape.Solids())
    return {"ok": True, "preview_mode": "cadquery", "cadquery": True,
            "step_available": True, "revision": revision, "mesh": mesh, "solids": solids,
            "checks": ["参数校验通过", "几何有效性检查通过", "STEP 已由同版预览几何生成"],
            "limits": ["未做承载验算或供应商连接规格认证"]}


class Handler(BaseHTTPRequestHandler):
    def json_response(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/status":
            return self.json_response({"cadquery": importlib.util.find_spec("cadquery") is not None})
        if self.path == "/api/example":
            return self.json_response(json.loads((BASE / "tests/shelf_instance.json").read_text(encoding="utf-8-sig")))
        if self.path.startswith("/api/step/"):
            revision = self.path.removeprefix("/api/step/")
            path = ARTIFACTS.get(revision)
            if path is None:
                return self.json_response({"error": "版本不存在，请重新生成"}, 404)
            return self.send_file(path, "application/step", f"aicad-{revision}.step")
        files = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css", "/workflow.js": "workflow.js", "/workflow.css": "workflow.css"}
        name = files.get(self.path)
        if name is None:
            return self.json_response({"error": "Not found"}, 404)
        return self.send_file(BASE / "web" / name, mimetypes.guess_type(name)[0] or "text/plain")

    def send_file(self, path, content_type, filename=None):
        raw = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        if self.headers.get("Origin") not in (None, f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
            return self.json_response({"error": "Origin rejected"}, 403)
        if self.path not in ("/api/check", "/api/build"):
            return self.json_response({"error": "Not found"}, 404)
        try:
            size = int(self.headers.get("Content-Length", 0))
            if size <= 0 or size > 1_000_000:
                return self.json_response({"error": "参数文件须小于 1 MB"}, 413)
            data = json.loads(self.rfile.read(size))
            if self.path == "/api/check":
                errors = check_document(data)
                return self.json_response({"ok": not errors, "errors": errors})
            return self.json_response(build_document(data))
        except Exception as exc:
            return self.json_response({"ok": False, "stage": "build", "errors": [{"path": "", "message": str(exc)}]}, 422)


def main():
    parser = argparse.ArgumentParser(description="aicad 本地货架工作台")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"aicad workbench: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        STORAGE.cleanup()


if __name__ == "__main__":
    main()

