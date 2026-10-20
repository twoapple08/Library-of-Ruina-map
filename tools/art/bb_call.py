"""One real MCP call via the pinned local server; root restricted to design/.

RUINA_ART_HOME=/tmp python tools/art/bb_call.py bbmodel_info '{"file":"models/tiphereth_table.bbmodel"}'
"""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
home = Path(os.environ.get("RUINA_ART_HOME", ROOT / ".art-tools")).resolve()
bb = home / "ruina-blockbench-mcp"
env = dict(os.environ, PATH=str(bb / "node_modules/.bin") + os.pathsep + os.environ.get("PATH", ""))
bun = bb / "node_modules/.bin" / ("bun.exe" if os.name == "nt" else "bun")
if __name__ == "__main__":
    sys.exit(subprocess.call([str(bun), "run", str(bb / "headless/call.ts"),
                             "--root", str(ROOT / "design"), *sys.argv[1:]], env=env))
