import asyncio
import hashlib
import json
import os
import signal
import time
from pathlib import Path

import discord
from discord import app_commands

from cmds import loader as cmds_loader
from core.config import cfg, logging_cfg, read_mood_prompt
from core.model import Answer, generate_answer
from managers.context import format_context_for_prompt, get_server_context
from managers.mcp import mcp_manager
from managers.memory import MemoryManager
from utils.handlers.messages import MessageSender
from utils.logger import get_logger, setup_logging

logger = get_logger()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True


class EvilBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory = MemoryManager(max_history=15)
        self._processing = set()
        self.tree = app_commands.CommandTree(self)
        self._commands_sync_state_path = (
            Path(cfg.BASE_DIR) / "data" / "command_sync_state.json"
        )

    @staticmethod
    def _compute_commands_fingerprint(cmds_path: Path) -> str:
        """Fingerprint command sources to avoid unnecessary global sync at startup."""
        hasher = hashlib.sha256()
        for py_file in sorted(cmds_path.glob("*.py")):
            if py_file.name.startswith("__"):
                continue
            st = py_file.stat()
            rel = py_file.name
            hasher.update(f"{rel}:{st.st_size}:{st.st_mtime_ns}".encode("utf-8"))
        return hasher.hexdigest()

    def _read_last_commands_fingerprint(self) -> str | None:
        try:
            if not self._commands_sync_state_path.exists():
                return None
            with open(self._commands_sync_state_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return payload.get("fingerprint")
        except Exception:
            logger.warning("Failed to read command sync state", exc_info=True)
            return None

    def _write_last_commands_fingerprint(self, fingerprint: str) -> None:
        try:
            self._commands_sync_state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._commands_sync_state_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "fingerprint": fingerprint,
                        "updatedAt": int(time.time()),
                    },
                    f,
                    ensure_ascii=True,
                    indent=2,
                )
        except Exception:
            logger.warning("Failed to write command sync state", exc_info=True)

    async def _sync_commands_if_needed(self, cmds_path: Path) -> None:
        force_sync = os.getenv("FORCE_COMMAND_SYNC", "0") == "1"
        skip_sync = os.getenv("SKIP_COMMAND_SYNC", "0") == "1"

        if skip_sync:
            logger.info("Skipping slash command sync (SKIP_COMMAND_SYNC=1)")
            return

        current_fingerprint = self._compute_commands_fingerprint(cmds_path)
        previous_fingerprint = self._read_last_commands_fingerprint()

        if not force_sync and previous_fingerprint == current_fingerprint:
            logger.info("Skipping slash command sync (no command changes detected)")
            return

        sync_start = time.perf_counter()
        await self.tree.sync()
        sync_elapsed = time.perf_counter() - sync_start
        self._write_last_commands_fingerprint(current_fingerprint)
        logger.info("Slash command sync completed in %.2fs", sync_elapsed)

    async def setup_hook(self):
        # Bootstrap memory and MCP concurrently to speed startup
        try:
            await asyncio.gather(self.memory.bootstrap(), mcp_manager.initialize())
        except Exception as e:
            logger.error("Error during bootstrap/init: %s", e, exc_info=True)
            # continue to attempt loading commands even if one fails

        # load commands from cmds/ directory (loggers inside loader will report details)
        cmds_path = Path(__file__).parent / "cmds"
        await cmds_loader.load_commands(self, self.tree, cmds_path)
        await self._sync_commands_if_needed(cmds_path)

    async def on_ready(self):
        logger.info(
            "AlphaLLM est en ligne ! Connecté en tant que %s (ID: %s)",
            self.user,
            self.user.id,
        )

    async def on_message(self, message):
        if (
            message.guild.me not in message.mentions
            or message.author.bot
            or message is None
        ):
            return

        uid = message.author.id
        if uid in self._processing:
            return

        self._processing.add(uid)
        try:
            # Gather context
            server_ctx = await get_server_context(message.guild)
            ctx_str = format_context_for_prompt(server_ctx)

            # Prepare prompt from mood file (with safe fallback)
            SYSTEM_BASE = read_mood_prompt("basic")
            system_payload = (
                f"{SYSTEM_BASE}\n"
                f"{'=' * 50}\n\n"
                f"TOOL INSTRUCTIONS:\n"
                f"You have access to web search & Python sandbox.\n"
                f"Use them if needed for accurate responses.\n\n"
                f"{'=' * 50}\n\n"
                f"CURRENT CONTEXT:\n"
                f"{ctx_str}\n\n"
                f"{'=' * 50}\n\n"
                f"👤 User: {message.author.display_name}"
            )

            # Handle history
            history = self.memory.get_history(uid, limit=self.memory.max_history)
            logger.debug(
                f"Handling message from {message.author.display_name} (ID: {uid}). History depth: {len(history)}"
            )

            messages = [{"role": "system", "content": system_payload}]
            for h in history:
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": message.content})

            # Activation de l'indicateur "typing" de Discord
            async with message.channel.typing():
                # Start streaming
                logger.debug(f"Sending request to LLM with {len(messages)} messages...")
                stream = await generate_answer(messages, True)

                full_content = ""
                current_buffer = ""
                sender = MessageSender(message.channel, self)

                if isinstance(stream, Answer):
                    await sender.process_and_send(stream.content)
                    return

                async for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        full_content += delta
                        current_buffer += delta

                        # On cherche un bloc complet (Code block ou LaTeX) avant d'envoyer
                        # Pour faire simple : si on a un double saut de ligne ou que c'est très long
                        if "\n\n" in current_buffer or len(current_buffer) > 1500:
                            # Si on est au milieu d'un bloc de code, on attend la fin
                            if current_buffer.count("```") % 2 == 0:
                                # Tentative d'extraction de ce qui est prêt
                                # On envoie uniquement ce qui précède le dernier bloc potentiellement incomplet
                                parts = current_buffer.rsplit("\n", 1)
                                if len(parts) > 1:
                                    to_send = parts[0]
                                    current_buffer = parts[1]
                                    if to_send.strip():
                                        await sender.process_and_send(to_send)

                # Envoi du reliquat final
                if current_buffer.strip():
                    await sender.process_and_send(current_buffer)

            if full_content:
                await self.memory.record_and_sync(
                    user_id=uid,
                    user_name=message.author.display_name,
                    user_content=message.content,
                    assistant_content=full_content,
                    guild_id=message.guild.id if message.guild else None,
                    channel_id=message.channel.id
                    if hasattr(message.channel, "id")
                    else None,
                )
                logger.info("Réponse streamée (par blocs) envoyée à %s", message.author)

        except Exception as e:
            logger.error(
                "Erreur lors du traitement du message streamé: %s", e, exc_info=True
            )
            await message.channel.send("Une erreur interne m'empêche de répondre.")
        finally:
            self._processing.discard(uid)


def run_bot():
    if not cfg.BOT_TOKEN:
        logger.error("BOT_TOKEN est manquant dans l'environnement !")
        return

    async def _main():
        client = EvilBot(intents=intents)

        loop = asyncio.get_running_loop()

        def _on_signal():
            logger.info("Shutdown signal received, closing client...")
            # schedule close on the client; client.start will return after close
            loop.create_task(client.close())

        for s in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(s, _on_signal)
            except NotImplementedError:
                # Windows or environments where add_signal_handler isn't supported
                pass

        try:
            await client.start(cfg.BOT_TOKEN)
        finally:
            # Ensure memory is persisted and client closed
            try:
                if not client.is_closed():
                    await client.close()
            except Exception:
                logger.exception("Error closing client during shutdown")

            try:
                await client.memory.sync()
            except Exception:
                logger.exception("Error syncing memory during shutdown")

    try:
        asyncio.run(_main())
    except Exception:
        logger.exception("Bot terminated with an exception")
