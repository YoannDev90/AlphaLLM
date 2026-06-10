"""Command registry for AlphaLLM.

This module provides a centralized place to track all application commands,
making it easier to generate documentation and manage command loading.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class CommandInfo:
    """Metadata about a Discord application command."""

    name: str
    description: str
    module_name: str
    file_path: Path


def get_all_commands() -> List[CommandInfo]:
    """Discover all commands in the cmds/ directory using static analysis.

    Returns
    -------
    List[CommandInfo]
        A sorted list of discovered commands.
    """
    commands = []
    cmds_dir = Path(__file__).parent

    for file in cmds_dir.glob("*.py"):
        if file.name.startswith("_") or file.name == "loader.py":
            continue

        try:
            with open(file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            func = decorator.func
                            is_command = False

                            # Matches @tree.command or @app_commands.command
                            if (
                                isinstance(func, ast.Attribute)
                                and func.attr == "command"
                            ):
                                is_command = True
                            elif isinstance(func, ast.Name) and func.id == "command":
                                is_command = True

                            if is_command:
                                name = "unknown"
                                description = "No description provided"
                                for keyword in decorator.keywords:
                                    if keyword.arg == "name" and isinstance(
                                        keyword.value, ast.Constant
                                    ):
                                        name = keyword.value.value
                                    elif keyword.arg == "description" and isinstance(
                                        keyword.value, ast.Constant
                                    ):
                                        description = keyword.value.value

                                if name == "unknown":
                                    name = node.name

                                commands.append(
                                    CommandInfo(
                                        name=name,
                                        description=description,
                                        module_name=file.stem,
                                        file_path=file,
                                    )
                                )
        except Exception:
            # Skip files that can't be parsed
            continue

    return sorted(commands, key=lambda x: x.name)
