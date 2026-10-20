"""Opt-in isolated authoring tools. No credentials, GUI, ports or GPU required.

python tools/art/setup.py [--home /absolute/cache/path] [--check]
Requires uv, Node/npm and git. Never installs into the game's Python/runtime.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BB_REPO = "https://github.com/jasonjgardner/blockbench-mcp-plugin.git"
BB_COMMIT = "141ef78fa59eb697895ab73d4757d874ab8a2711"


def run(args, **kw):
    return subprocess.run([str(a) for a in args], check=True, **kw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path(os.environ.get("RUINA_ART_HOME", ROOT / ".art-tools")))
    parser.add_argument("--check", action="store_true", help="Read-only, no downloads")
    args = parser.parse_args()
    home = args.home.resolve()
    bb, venv = home / "ruina-blockbench-mcp", home / "ruina-blender-venv"
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    report = {"home": str(home), "blender": False, "blockbench_mcp": False,
              "gpu_fps_tested": False, "desktop_apps_connected": False}
    if not args.check:
        for cmd in ("uv", "node", "npm", "git"):
            if not shutil.which(cmd):
                raise SystemExit(f"Missing {cmd}; install it before authoring setup")
        home.mkdir(parents=True, exist_ok=True)
        if not py.exists():
            run(["uv", "venv", "--python", "3.11", venv])
        run(["uv", "pip", "sync", "--python", py, ROOT / "tools/art/requirements-blender.txt"])
        if not bb.exists():
            run(["git", "clone", BB_REPO, bb])
        got = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=bb, text=True).strip()
        if got != BB_COMMIT:
            # Do not reset an existing user's checkout behind their back.
            if subprocess.check_output(["git", "status", "--porcelain"], cwd=bb, text=True).strip():
                raise SystemExit("External checkout has changes; choose a clean --home")
            run(["git", "fetch", "origin", BB_COMMIT], cwd=bb)
            run(["git", "checkout", "--detach", BB_COMMIT], cwd=bb)
        run(["npm", "install", "--omit=dev", "--ignore-scripts", "--package-lock=false"], cwd=bb)
        # Explicitly initialize the inspected Bun launcher. Other package lifecycle
        # scripts stay disabled. Then use the upstream committed dependency lock.
        bun = bb / "node_modules/.bin" / ("bun.exe" if os.name == "nt" else "bun")
        if not bun.exists() or subprocess.run([str(bun), "--version"], capture_output=True).returncode:
            run(["node", "install.js"], cwd=bb / "node_modules/bun")
        bun = bb / "node_modules/.bin" / ("bun.exe" if os.name == "nt" else "bun")
        run([bun, "install", "--production", "--frozen-lockfile", "--ignore-scripts"], cwd=bb)
        if subprocess.run([str(bun), "--version"], capture_output=True).returncode:
            run(["node", "install.js"], cwd=bb / "node_modules/bun")
    if py.exists():
        probe = run([py, "-c", "import bpy; print(bpy.app.version_string)"], capture_output=True, text=True)
        report["blender"] = probe.stdout.strip()
        if not probe.stdout.startswith("4.5.3"):
            raise SystemExit("Blender version mismatch")
    if bb.exists():
        got = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=bb, text=True).strip()
        if got != BB_COMMIT:
            raise SystemExit("Blockbench MCP source version mismatch")
        env = dict(os.environ, PATH=str(bb / "node_modules/.bin") + os.pathsep + os.environ.get("PATH", ""))
        bun = bb / "node_modules/.bin" / ("bun.exe" if os.name == "nt" else "bun")
        run([bun, "run", bb / "headless/call.ts", "--root", ROOT / "design",
             "bbmodel_info", json.dumps({"file": "models/tiphereth_table.bbmodel"})], env=env,
            capture_output=True, text=True)
        report["blockbench_mcp"] = BB_COMMIT
    print(json.dumps(report, indent=2))
    if not report["blender"] or not report["blockbench_mcp"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
