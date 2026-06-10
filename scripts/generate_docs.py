import os
import re
import sys
from pathlib import Path

# Add project root to sys.path to import cmds._registry
sys.path.append(str(Path(__file__).parent.parent))

from cmds._registry import get_all_commands


def update_readme(commands):
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("README.md not found")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    commands_table = "| Command | Description |\n| :--- | :--- |\n"
    for cmd in commands:
        commands_table += f"| `/{cmd.name}` | {cmd.description} |\n"

    new_content = re.sub(
        r"<!-- COMMANDS-START -->.*?<!-- COMMANDS-END -->",
        f"<!-- COMMANDS-START -->\n{commands_table}\n<!-- COMMANDS-END -->",
        content,
        flags=re.DOTALL,
    )

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Updated README.md with {len(commands)} commands.")


if __name__ == "__main__":
    commands = get_all_commands()
    update_readme(commands)
