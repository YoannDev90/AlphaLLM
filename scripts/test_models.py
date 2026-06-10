import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import asyncio
import time
import traceback

import litellm

from core.config import cfg
from core.models_loader import Model, get_model_catalog, get_models


def classify_exception(model, exc):
    msg = str(exc).lower()

    if not model.api_key:
        return "missing_api_key", "No API key set for provider"

    if any(k in msg for k in ("401", "403", "unauthor", "invalid", "api key")):
        return "invalid_api_key", msg

    if any(k in msg for k in ("404", "not found", "model not found")):
        return "model_not_found", msg

    if any(
        k in msg
        for k in (
            "502",
            "503",
            "504",
            "timeout",
            "timed out",
            "connection",
            "failed to establish",
            "name or service not known",
        )
    ):
        return "provider_down", msg

    return "unknown_error", msg


async def test_model(model: Model, msg, retries=1):
    last_exc = None
    for attempt in range(1, retries + 2):
        try:
            resp = await litellm.acompletion(
                model=model.litellm_id,
                base_url=model.api_base,
                api_key=model.api_key,
                messages=msg,
                timeout=30,
            )
            message = (
                resp.choices[0].message if getattr(resp, "choices", None) else None
            )
            return {"status": "ok", "message": message, "resp": resp}
        except Exception as e:
            last_exc = e
            # small backoff before retry
            if attempt <= retries:
                time.sleep(1)
                continue
            return {"status": "error", "exception": e, "trace": traceback.format_exc()}


def summarize_results(model, result):
    if result["status"] == "ok":
        return ("ok", "Got response", None)
    exc = result.get("exception")
    kind, detail = (
        classify_exception(model, exc)
        if exc is not None
        else ("unknown_error", "no exception info")
    )
    return (kind, detail, result.get("trace"))


def pretty_model_info(model):
    return f"model={model.litellm_id} provider={model.provider} api_base={model.api_base} api_key_set={bool(model.api_key)}"


async def main():
    msg = [
        {
            "role": "system",
            "content": "Please answer as concisely as possible; this is just a test",
        },
        {"role": "user", "content": "OK ?"},
    ]

    models = get_models()
    if not models:
        print(
            "No usable models found by get_models(). Catalog below shows providers and which keys are missing:"
        )
        catalog = get_model_catalog()
        for entry in catalog:
            print(
                f"- provider={entry['provider']} model={entry['model']} litellm_id={entry['litellm_id']} api_base={entry['api_base']} api_key_set={entry['api_key_set']}"
            )
        return

    for model in models:
        print("\n" + "=" * 60)
        print(pretty_model_info(model))
        result = await test_model(model, msg, retries=1)
        kind, detail, trace = summarize_results(model, result)
        print(f"Result: {kind}")
        print(detail)
        if trace:
            print("--- traceback ---")
            print(trace)


if __name__ == "__main__":
    asyncio.run(main())
