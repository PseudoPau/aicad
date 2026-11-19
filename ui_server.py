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
    if importlib.util.find_spec("cadquery") is None:
        return {"ok": False, "stage": "environment", "errors": [{"path": "", "message": "缺少 CadQuery。参数草稿已保留；安装项目依赖后可生成真实几何和 STEP。"}]}
    from cadquery import exporters
    from core.translator import run_translation
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    revision = hashlib.sha256(canonical.encode()).hexdigest()[:20]
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
    return {"ok": True, "revision": revision, "mesh": mesh, "solids": solids,
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

