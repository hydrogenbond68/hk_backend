"""apply_cors.py — Remove ALL manual CORS() calls, insert one canonical block,
and register socket.io stub routes that work on both /socket.io/ and /socket.io/<path>."""

import re
import sys
import ast
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

INIT_PATH = Path("app/__init__.py")
MARKER    = "# === BULLETPROOF CORS (auto-generated) ==="
END_MARK  = "# === END BULLETPROOF CORS ==="

CORS_BLOCK = r'''# === BULLETPROOF CORS (auto-generated) ===
import re as _cors_re
from flask import request as _cors_request
from flask_cors import CORS as _CORS

_CORS_LOCAL_REGEX = r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(:\d+)?"
_CORS_PROD_LIST = [
    # Add production origins here, e.g. "https://hk.example.com",
]

# Single canonical CORS registration — no other CORS() call should exist.
_CORS(
    app,
    resources={r"/*": {"origins": [_CORS_LOCAL_REGEX] + _CORS_PROD_LIST}},
    supports_credentials=True,
    allow_headers="*",
    expose_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    max_age=600,
    send_wildcard=False,
)

_CORS_LOCAL_RE = _cors_re.compile(
    r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(:\d+)?$"
)
_CORS_PROD_SET = set(_CORS_PROD_LIST)

def _cors_allow(origin):
    if not origin:
        return False
    if _CORS_LOCAL_RE.match(origin):
        return True
    return origin in _CORS_PROD_SET

@app.after_request
def _force_cors_headers(resp):
    origin = _cors_request.headers.get("Origin")
    if origin and _cors_allow(origin):
        if "Access-Control-Allow-Origin" not in resp.headers:
            resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Vary"] = "Origin"
        resp.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, ngrok-skip-browser-warning, "
            "X-Requested-With, Cache-Control, Pragma, Expires, Idempotency-Key"
        )
        resp.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        )
    return resp

# Socket.IO stubs — BOTH variants so GET /socket.io/ never hits the OPTIONS catch-all.
@app.route("/socket.io/", methods=["GET", "POST", "OPTIONS"])
@app.route("/socket.io/<path:_siopath>", methods=["GET", "POST", "OPTIONS"])
def _socketio_stub(_siopath=""):
    return ({"status": "socket.io not enabled on this backend"}, 501)

# Catch-all OPTIONS so preflight on unknown paths still returns 204.
@app.route("/<path:_any>", methods=["OPTIONS"])
def _cors_preflight_safety(_any=""):
    return ("", 204)
# === END BULLETPROOF CORS ===
'''


def indent_block(block, indent):
    if not indent:
        return block
    return "\n".join(
        (indent + line) if line.strip() else line
        for line in block.rstrip("\n").split("\n")
    ) + "\n"


def find_flask_call(src):
    m = re.search(r"^([ \t]*)(app\s*=\s*Flask\s*\()", src, flags=re.MULTILINE)
    if not m:
        return None
    indent = m.group(1)
    i = m.end() - 1
    depth = 0
    while i < len(src):
        c = src[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return indent, m.start(), i + 1
        i += 1
    return None


def strip_manual_cors(src):
    """Remove every standalone `CORS(app, ...)` call (but not our marker block)."""
    lines = src.split("\n")
    out = []
    i = 0
    removed = []
    while i < len(lines):
        line = lines[i]
        # Skip import lines and our block
        if re.match(r"^\s*from\s+flask_cors\s+import", line):
            removed.append(("import", line.strip()))
            i += 1
            continue
        if re.match(r"^\s*CORS\s*\(", line):
            # Consume the full call (balanced parentheses)
            depth = 0
            j = i
            while j < len(lines):
                depth += lines[j].count("(") - lines[j].count(")")
                if depth <= 0 and j >= i:
                    break
                j += 1
            removed.append(("call", "\n".join(lines[i:j+1]).strip()[:120] + "..."))
            i = j + 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out), removed


def main():
    if not INIT_PATH.exists():
        print(f"FAIL: {INIT_PATH} not found. Run from project root.")
        sys.exit(1)

    src = INIT_PATH.read_text()

    # Remove previous auto-generated block
    if MARKER in src:
        src = re.sub(
            re.escape(MARKER) + r".*?" + re.escape(END_MARK) + r"\n?",
            "", src, flags=re.DOTALL,
        )
        print("• removed previous auto-generated CORS block")

    # Remove ALL manual CORS calls (they conflict with the canonical one)
    src, removed = strip_manual_cors(src)
    if removed:
        print("• removed manual CORS entries:")
        for kind, line in removed:
            print(f"    [{kind}] {line}")

    located = find_flask_call(src)
    if not located:
        print("FAIL: could not find `app = Flask(`")
        sys.exit(2)
    indent, _start, end = located
    print(f"• found app = Flask(...) at char {end}")

    block = indent_block(CORS_BLOCK, indent)
    src = src[:end] + "\n" + block + src[end:]

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"FAIL: syntax error after patch: {e}")
        sys.exit(3)

    backup = INIT_PATH.with_suffix(
        INIT_PATH.suffix + ".bak." + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    shutil.copy2(INIT_PATH, backup)
    INIT_PATH.write_text(src)
    print(f"✅ wrote {INIT_PATH}  (backup: {backup.name})")

    print("• verifying create_app() ...")
    result = subprocess.run(
        [sys.executable, "-c",
         "from app import create_app; "
         "a = create_app(); "
         "print('routes:', len(list(a.url_map.iter_rules())))"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("FAIL: create_app() raised:")
        print(result.stderr)
        shutil.copy2(backup, INIT_PATH)
        print(f"⚠️  restored backup {backup.name}")
        sys.exit(4)
    print("✅ " + result.stdout.strip())

    print()
    print("Done. Restart server: Ctrl+C, then python run.py")


if __name__ == "__main__":
    main()
