#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# 1. Format code (run only if available)
# ---------------------------------------------------------------------------
echo "Running formatters if available..."
if command -v ruff >/dev/null 2>&1; then
    echo "1️⃣  Running ruff format..."
    ruff format . || true
else
    echo " ⛔ Skipping ruff (not installed)"
fi
if command -v isort >/dev/null 2>&1; then
    echo "2️⃣  Running isort..."
    isort **/*.py || true
else
    echo " ⛔ Skipping isort (not installed)"
fi
if command -v removestar >/dev/null 2>&1; then
    echo "3️⃣  Running removestar..."
    removestar . || true
else
    echo " ⛔ Skipping removestar (not installed)"
fi

# ---------------------------------------------------------------------------
# 2. Project tree → stdout + README (between <!-- TREE-START --> / <!-- TREE-END -->)
# ---------------------------------------------------------------------------
python3 << 'EOF'
import subprocess, sys, re
from pathlib import Path

GITIGNORE = Path(".gitignore")
README    = Path("README.md")

# Build exclusion pattern for `tree -I`
excludes = [".git"]
if GITIGNORE.exists():
    for line in GITIGNORE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("!"):
            excludes.append(line.removeprefix("./").rstrip("/"))
pattern = "|".join(excludes) or ".git"

if subprocess.run(["which", "tree"], capture_output=True).returncode != 0:
    print("'tree' not installed. Install with: apt-get install tree / brew install tree")
    sys.exit(0)

tree_output = subprocess.run(
    ["tree", "-a", "-I", pattern],
    capture_output=True, text=True
).stdout

if not README.exists():
    sys.exit(0)

content = README.read_text()
block = f"\n```\n{tree_output}```\n"
new_content = re.sub(
    r"(<!-- TREE-START -->).*?(<!-- TREE-END -->)",
    lambda m: m.group(1) + block + m.group(2),
    content, flags=re.DOTALL
)
if new_content != content:
    README.write_text(new_content)
EOF

# ---------------------------------------------------------------------------
# 3. PyPI dependencies → README (between <!--DEPS-START--> / <!--DEPS-END-->)
# ---------------------------------------------------------------------------
python3 << 'EOF'
import re, json, sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

README       = Path("README.md")
REQUIREMENTS = Path("requirements.txt")

if not README.exists() or not REQUIREMENTS.exists():
    sys.exit(0)

def fetch_pypi(pkg):
    try:
        with urlopen(f"https://pypi.org/pypi/{pkg.lower()}/json", timeout=5) as r:
            info = json.loads(r.read())["info"]
            return info.get("summary", "").replace("\n", " ").strip(), info.get("version", "")
    except (URLError, KeyError):
        return "", ""

print("♻️ Updating dependencies list (fetching from PyPI)...")
lines = ["```markdown"]
for raw in REQUIREMENTS.read_text().splitlines():
    raw = raw.strip()
    if not raw or raw.startswith("#"):
        continue
    pkg = re.split(r"[\[<>=!~\s]", raw)[0]
    summary, version = fetch_pypi(pkg)
    if summary:
        lines.append(f"- `{raw}` - {summary} (latest: {version})")
    elif version:
        lines.append(f"- `{raw}` - latest: {version}")
    else:
        lines.append(f"- `{raw}`")
lines.append("```")

block = "\n" + "\n".join(lines) + "\n"
content = README.read_text()
new_content = re.sub(
    r"(<!--DEPS-START-->).*?(<!--DEPS-END-->)",
    lambda m: m.group(1) + block + m.group(2),
    content, flags=re.DOTALL
)
if new_content != content:
    README.write_text(new_content)
    print("  Dependencies updated ✓")
EOF

# ---------------------------------------------------------------------------
# 4. Env var names → README (between <!--ENV-START--> / <!--ENV-END-->)
# ---------------------------------------------------------------------------
python3 << 'EOF'
import re, sys
from pathlib import Path

README   = Path("README.md")
ENV_FILE = Path(".env")

if not README.exists() or not ENV_FILE.exists():
    sys.exit(0)

print("✂️ Copying environment variable names to README...")
var_names = []
for line in ENV_FILE.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        var_names.append(line.split("=", 1)[0].strip())

if not var_names:
    sys.exit(0)

block = "\n```env\n" + "".join(f"{v}=\n" for v in var_names) + "```\n"
content = README.read_text()
new_content = re.sub(
    r"(<!--ENV-START-->).*?(<!--ENV-END-->)",
    lambda m: m.group(1) + block + m.group(2),
    content, flags=re.DOTALL
)
if new_content != content:
    README.write_text(new_content)
    print("  Environment variables updated ✓")
EOF

# ---------------------------------------------------------------------------
# 5. Command documentation → README (between <!-- COMMANDS-START --> / <!-- COMMANDS-END -->)
# ---------------------------------------------------------------------------
if [ -f scripts/generate_docs.py ]; then
    echo "🔄 Updating command documentation..."
    python3 scripts/generate_docs.py
fi

echo "✅ All updates completed!"