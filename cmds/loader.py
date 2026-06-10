"""Command loader utilities.

This module discovers command modules under the `cmds` package and calls
their `setup(tree, bot)` function if present to register application
commands.
"""

import importlib
import inspect
import logging
import pkgutil
import time
from pathlib import Path
from typing import Any

from discord import app_commands

from utils.logger import get_logger

logger = get_logger()


def _iter_command_modules(base_path: Path):
    """Yield top-level module names found in `base_path`.

    Parameters
    ----------
    base_path : Path
        Filesystem path to the `cmds` directory to scan.

    Yields
    ------
    str
        Module name (without package prefix) for each discovered module.
    """
    pkg_path = str(base_path)
    for finder, name, ispkg in pkgutil.iter_modules([pkg_path]):
        if name.startswith("__"):
            continue
        yield name


async def load_commands(bot: Any, tree: app_commands.CommandTree, cmds_path: Path):
    """Import and initialize command modules found under `cmds_path`.

    This function walks the package tree under `cmds_path`, imports each
    module, and calls its `setup(tree, bot)` function if present. Failing
    modules are logged and skipped to avoid crashing startup.

    Parameters
    ----------
    bot : Any
        Bot instance passed to command modules' `setup` functions.
    tree : app_commands.CommandTree
        Command tree used to register application commands.
    cmds_path : Path
        Filesystem path to the `cmds` package directory.
    """
    start = time.perf_counter()
    loaded = 0
    failed = 0
    loaded_modules = []
    failed_modules = []
    module_times = []

    # Top-level modules
    for finder, modname, ispkg in pkgutil.walk_packages([str(cmds_path)], prefix=""):
        if modname.split(".")[-1].startswith("__"):
            continue
        rel = modname.replace("/", ".")
        mod_start = time.perf_counter()
        logger.debug("Loading command module: %s", modname)
        # Convert filesystem path style to module-like import path
        # We'll import via importlib by path: convert file path to module spec
        try:
            spec = importlib.util.spec_from_file_location(
                modname, str(cmds_path / (modname + ".py"))
            )
            if spec is None:
                # maybe a package
                # try import by package name relative to project
                module = importlib.import_module(f"cmds.{modname}")
            else:
                module = importlib.util.module_from_spec(spec)
                loader = spec.loader
                assert loader is not None
                loader.exec_module(module)
        except Exception:
            # fallback: try import as package module
            try:
                module = importlib.import_module(f"cmds.{modname}")
            except Exception:
                failed += 1
                failed_modules.append(modname)
                logger.warning(
                    "Failed to import command module %s", modname, exc_info=True
                )
                continue

        # If module defines setup function, call it
        setup_fn = getattr(module, "setup", None)
        if callable(setup_fn):
            try:
                logger.debug("Calling setup() for module %s", modname)
                maybe_coro = setup_fn(tree, bot)
                if inspect.isawaitable(maybe_coro):
                    await maybe_coro
                loaded += 1
                loaded_modules.append(modname)
                module_times.append((modname, time.perf_counter() - mod_start))
            except Exception:
                # ignore failing command modules to avoid crashing startup
                failed += 1
                failed_modules.append(modname)
                logger.exception("setup() failed for module %s", modname)
                continue
        else:
            logger.debug("Module %s has no setup(); skipping", modname)

    total = time.perf_counter() - start
    logger.info("Loaded %d command modules (%d failed) in %.2fs", loaded, failed, total)
    if failed_modules:
        logger.warning("Command modules failed: %s", ", ".join(failed_modules))
    for name, t in module_times:
        logger.debug("Module %s took %.3fs to setup", name, t)
