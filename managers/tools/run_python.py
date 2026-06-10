"""Run Python snippets inside an ephemeral microsandbox."""

import asyncio
import json
import time
from typing import Any, Dict, Optional

import microsandbox

from utils.logger import get_logger

logger = get_logger()

# Default OCI image to use for ephemeral Python sandboxes when none provided
DEFAULT_PYTHON_IMAGE = "python:3.12-slim"


async def run_python(code: str, timeout: int = 10, image: Optional[str] = None) -> str:
    """Execute Python code in an ephemeral sandbox.

    Parameters
    ----------
    code : str
        Python source code to execute.
    timeout : int
        Maximum execution time in seconds (default: 10).
    image : Optional[str]
        Optional container image to use (default: None uses built-in image).

    Returns
    -------
    str
        JSON string containing stdout, stderr, exit code and success.

    Raises
    ------
    RuntimeError
        If the sandbox does not expose a supported execution API.
    asyncio.TimeoutError
        If execution exceeds the configured timeout.
    Exception
        If sandbox creation, execution or cleanup fails.
    """
    name = f"run-python-{int(time.time() * 1000)}"
    sandbox = None
    try:
        kwargs: Dict[str, Any] = {"memory_mib": 256, "cpus": 1}
        # Ensure an image or snapshot is provided for microsandbox
        kwargs["image"] = image or DEFAULT_PYTHON_IMAGE

        try:
            # Create in the current event-loop/thread; some SDK builds require a running loop
            sandbox = microsandbox.Sandbox.create(name, **kwargs)
        except Exception:
            cfg = {
                "name": name,
                "memoryMib": 256,
                "cpus": 1,
                "image": image or DEFAULT_PYTHON_IMAGE,
            }
            sandbox = microsandbox.Sandbox.create(cfg)

        # Some SDK builds return a coroutine/Future from create(); await if so
        if asyncio.iscoroutine(sandbox) or isinstance(sandbox, asyncio.Future):
            sandbox = await sandbox

        # Try multiple SDK variants: prefer sandbox.run, then sandbox.exec, then shell fallback
        def _extract_exec_result(result: Any) -> Dict[str, Any]:
            """Normalize a sandbox execution result into a JSON-friendly dict.

            Parameters
            ----------
            result : Any
                Raw execution result returned by microsandbox.

            Returns
            -------
            Dict[str, Any]
                Dictionary with stdout, stderr, exit code and success.
            """
            stdout = None
            stderr = None
            codev = None
            success = None

            # Common field names
            for attr in ("stdout_text", "stdout", "stdout_bytes"):
                if hasattr(result, attr):
                    stdout = getattr(result, attr)
                    break
            for attr in ("stderr_text", "stderr", "stderr_bytes"):
                if hasattr(result, attr):
                    stderr = getattr(result, attr)
                    break
            for attr in ("exit_code", "code"):
                if hasattr(result, attr):
                    codev = getattr(result, attr)
                    break
            if hasattr(result, "success"):
                success = getattr(result, "success")

            if callable(stdout):
                stdout = stdout()
            if callable(stderr):
                stderr = stderr()
            if callable(success):
                success = success()

            # If bytes provided, try to decode
            if isinstance(stdout, (bytes, bytearray)):
                try:
                    stdout = stdout.decode("utf-8", errors="replace")
                except Exception:
                    pass
            if isinstance(stderr, (bytes, bytearray)):
                try:
                    stderr = stderr.decode("utf-8", errors="replace")
                except Exception:
                    pass

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exitCode": codev,
                "success": success,
            }

        result = None

        # Prefer using `exec` which returns either an ExecOutput or an ExecHandle
        if hasattr(sandbox, "exec"):
            try:
                maybe = sandbox.exec("python", ["-c", code])

                # If exec returned a coroutine/awaitable, await it; otherwise run in thread
                if asyncio.iscoroutine(maybe) or isinstance(maybe, asyncio.Future):
                    raw = await asyncio.wait_for(maybe, timeout=timeout)
                else:
                    raw = await asyncio.wait_for(
                        asyncio.to_thread(sandbox.exec, "python", ["-c", code]),
                        timeout=timeout,
                    )

                # If raw is an ExecHandle (streaming), try to collect its output
                collect = getattr(raw, "collect", None)
                if collect is not None:
                    if asyncio.iscoroutinefunction(collect):
                        out = await asyncio.wait_for(raw.collect(), timeout=timeout)
                    else:
                        out = await asyncio.wait_for(
                            asyncio.to_thread(raw.collect), timeout=timeout
                        )
                    result = _extract_exec_result(out)
                else:
                    result = _extract_exec_result(raw)
            except Exception:
                raise

        # Fallback: shell invocation (blocking), run in thread and extract
        elif hasattr(sandbox, "shell"):
            heredoc = "python - <<'PY'\n" + code + "\nPY"
            raw = await asyncio.wait_for(
                asyncio.to_thread(sandbox.shell, heredoc), timeout=timeout
            )
            result = _extract_exec_result(raw)

        # Older or alternative SDKs exposing .run
        elif hasattr(sandbox, "run"):
            maybe = sandbox.run(code, "python")
            if asyncio.iscoroutine(maybe) or isinstance(maybe, asyncio.Future):
                result = await asyncio.wait_for(maybe, timeout=timeout)
            elif callable(maybe):
                result = await asyncio.wait_for(
                    asyncio.to_thread(maybe), timeout=timeout
                )
            else:
                result = maybe

        # Normalize and return
        try:
            return json.dumps(result, ensure_ascii=True)
        except Exception:
            return str(result)
    except asyncio.TimeoutError:
        logger.error("Python execution timeout after %ss", timeout)
        return f"Error: Execution timeout after {timeout} seconds"
    except Exception as e:
        logger.error("Python execution error: %s", e, exc_info=True)
        return f"Error: {str(e)}"
    finally:
        if sandbox is not None:
            try:
                await asyncio.to_thread(sandbox.stop)
            except Exception:
                pass
            try:
                await asyncio.to_thread(microsandbox.Sandbox.remove, name)
            except Exception:
                pass
