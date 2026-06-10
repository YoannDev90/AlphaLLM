"""Core answer-generation helpers and LiteLLM orchestration."""

import logging
import time
from typing import List, Optional

import litellm

# Disable LiteLLM logging worker to prevent "Task was destroyed but it is pending" noise
litellm.suppress_logging_worker_warnings = True
# Optional: suppress standard LiteLLM stdout logging if desired
# litellm.set_verbose = False
try:
    # Prefer explicit debug off API if available
    if hasattr(litellm, "_turn_off_debug"):
        litellm._turn_off_debug()
    else:
        # Fallback: set verbose flag if present
        setattr(litellm, "set_verbose", False)
except Exception:
    pass

# Reduce Python logging noise from litellm internals
for _n in ("LiteLLM", "litellm"):
    logging.getLogger(_n).setLevel(logging.CRITICAL)

from core.config import cfg
from core.models_loader import Model, get_models
from core.tools import get_combined_tools, handle_tool_call
from utils.logger import get_logger

logger = get_logger()

DEFAULT_MAX_CONTEXT_CHARS = 128000


def _validate_tools_payload(raw_tools: list) -> list:
    """Validate and normalize tools payload before sending to LLM provider.

    Returns a filtered list containing only provider-compatible function descriptors.
    Logs and drops malformed entries to avoid provider validation crashes.

    Parameters
    ----------
    raw_tools : list
        Raw tool descriptors returned by the tool registry.

    Returns
    -------
    list
        Provider-compatible function tool descriptors.
    """
    valid = []
    for t in raw_tools or []:
        if not isinstance(t, dict):
            logger.warning("Dropping non-dict tool entry: %s", type(t))
            continue

        tt = t.get("type")
        if tt != "function":
            logger.warning(
                "Dropping tool with unsupported type '%s' (expected 'function'): %s",
                tt,
                t,
            )
            continue

        fn = t.get("function")
        if not isinstance(fn, dict):
            logger.warning("Dropping tool with missing/invalid 'function' field: %s", t)
            continue

        name = fn.get("name")
        if not name or not isinstance(name, str):
            logger.warning("Dropping tool with invalid name: %s", fn)
            continue

        # Ensure parameters is present and is a dict (providers expect JSON Schema)
        params = fn.get("parameters") or {}
        if not isinstance(params, dict):
            logger.warning("Normalizing parameters for tool %s", name)
            params = {}
            fn["parameters"] = params

        valid.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": fn.get("description", ""),
                    "parameters": params,
                },
            }
        )

    return valid


def _messages_char_size(msgs: list) -> int:
    """Return the serialized character size of a messages list.

    Parameters
    ----------
    msgs : list
        Chat messages to measure.

    Returns
    -------
    int
        Serialized character count.
    """
    try:
        import json

        return len(json.dumps(msgs, ensure_ascii=False))
    except Exception:
        return sum(len(str(m)) for m in msgs)


def _truncate_messages(msgs: list, max_chars: int = DEFAULT_MAX_CONTEXT_CHARS) -> list:
    """Trim oldest non-system messages until the serialized size is under max_chars.

    Keeps system messages and as many recent messages as will fit.

    Parameters
    ----------
    msgs : list
        Chat messages to trim.
    max_chars : int
        Maximum character budget. Default is DEFAULT_MAX_CONTEXT_CHARS.

    Returns
    -------
    list
        Trimmed list of messages.
    """
    if not isinstance(msgs, list):
        return msgs

    size = _messages_char_size(msgs)
    if size <= max_chars:
        return msgs

    logger.warning(
        "Messages too large (%d chars), truncating to %d chars", size, max_chars
    )

    msgs_copy = list(msgs)
    # Remove oldest non-system messages first
    i = 0
    while _messages_char_size(msgs_copy) > max_chars and any(
        m.get("role") != "system" for m in msgs_copy
    ):
        # find first non-system
        for idx, m in enumerate(msgs_copy):
            if m.get("role") != "system":
                del msgs_copy[idx]
                break
        i += 1

    final_size = _messages_char_size(msgs_copy)
    logger.info(
        "Truncated messages: removed %d messages; final size %d chars", i, final_size
    )
    return msgs_copy


class Answer:
    """Container for a generated model answer.

    Attributes
    ----------
    content : str
        Generated answer text.
    model : Optional[str]
        Selected model identifier.
    response_time : Optional[float]
        Wall-clock response time in seconds.
    """

    def __init__(self, content: str = ""):
        """Create an answer container.

        Parameters
        ----------
        content : str
            Initial answer content. Default is ''.
        """
        self.content = content
        self.model = None
        self.response_time = None


def _select_model(models: List[Model]) -> Optional[Model]:
    """Select the primary model from the available list.

    Parameters
    ----------
    models : List[Model]
        Available model configurations.

    Returns
    -------
    Optional[Model]
        Selected model or None when the list is empty.
    """
    if not models:
        return None
    # Favor generic selection for now, or use first available
    return models[0]


async def generate_answer(messages: list, stream: bool = False):
    """Generate an answer from chat messages, optionally streaming.

    Parameters
    ----------
    messages : list
        Chat history to send to the model.
    stream : bool
        Whether to return a streaming response. Default is False.

    Returns
    -------
    Answer | Any
        Answer object or streaming response from LiteLLM.
    """
    models = get_models()
    if not models:
        return Answer("Désolé, aucune configuration d'IA disponible.")

    # Sort models or pick one that isn't known to be down
    chosen = _select_model(models)
    logger.debug(f"Selected model: {chosen.id} (base: {chosen.api_base})")

    # Prépare les fallbacks sans inclure le modèle principal
    fallbacks_configs = []
    for m in models:
        if m.id == chosen.id:
            continue
        model_name = f"openai/{m.id}"
        fallbacks_configs.append(
            {"model": model_name, "base_url": m.api_base, "api_key": m.api_key}
        )

    start_time = time.time()

    try:
        # Forcer le préfixe 'openai/' pour chaque endpoint OpenAI-compatible.
        model_name = f"openai/{chosen.id}"

        # Premier appel pour voir si l'IA veut appeler un outil
        # Truncate messages if they're too large for provider context
        messages = _truncate_messages(messages, DEFAULT_MAX_CONTEXT_CHARS)

        resp = await litellm.acompletion(
            model=model_name,
            base_url=chosen.api_base,
            api_key=chosen.api_key,
            messages=messages,
            tools=_validate_tools_payload(get_combined_tools()),
            tool_choice="auto",
            fallbacks=fallbacks_configs,
            timeout=25,
        )

        message = resp.choices[0].message

        # Si tool_calls est présent, on les exécute
        if hasattr(message, "tool_calls") and message.tool_calls:
            logger.info(
                f"LLM wants to use {len(message.tool_calls)} tools: {[tc.function.name for tc in message.tool_calls]}"
            )
            assistant_message = {
                "role": "assistant",
                "content": message.content or "",
            }
            if message.tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": getattr(tool_call, "type", "function"),
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ]

            messages.append(assistant_message)

            for tool_call in message.tool_calls:
                import json

                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                result = await handle_tool_call(function_name, arguments)

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": result,
                    }
                )

            # Deuxième appel après avoir ajouté les résultats des outils
            # Pour la réponse finale au tool calling, on peut streamer si demandé
            # Truncate messages again before the final LLM call
            messages = _truncate_messages(messages, DEFAULT_MAX_CONTEXT_CHARS)

            resp = await litellm.acompletion(
                model=model_name,
                base_url=chosen.api_base,
                api_key=chosen.api_key,
                messages=messages,
                fallbacks=fallbacks_configs,
                timeout=25,
                stream=stream,
            )

            if stream:
                return resp
        else:
            # Si on voulait du stream dès le début et qu'aucun outil n'est appelé,
            # il faut relancer avec stream=True (LiteLLM ne permet pas de streamer le tool calling facilement en un coup)
            if stream:
                return await litellm.acompletion(
                    model=model_name,
                    base_url=chosen.api_base,
                    api_key=chosen.api_key,
                    messages=messages,
                    fallbacks=fallbacks_configs,
                    timeout=25,
                    stream=True,
                )

        content = ""
        if hasattr(resp, "choices") and resp.choices:
            content = resp.choices[0].message.content

        ans = Answer(content)
        ans.model = chosen.id
        ans.response_time = time.time() - start_time
        return ans
    except Exception as e:
        logger.error("Error generating answer: %s", e)
        return Answer(
            "Toutes mes sources de haine sont saturées (ou une erreur d'outil est survenue)."
        )
