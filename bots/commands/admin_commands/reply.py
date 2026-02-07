import logging

import discord

from config import DEV_IDS, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(name="reply", description="Reply to a user via DM")
    async def reply(interaction: discord.Interaction, user_id: str, message: str):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message(
                "❌ You are not authorized to use this command.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Command /reply executed by {interaction.user.display_name}")

        try:
            user_id = int(user_id)
            asker = await bot.fetch_user(user_id)
            if not DEV_IDS:
                raise ValueError("Developer IDs are not defined in the configuration.")
            await asker.send(
                f"Developer (<@{interaction.user.id}>): {message}\nUse `/contact-dev` to reply"
            )
        except discord.HTTPException as e:
            logger.error(f"Error sending message: {e}")
            if e.code == 50007:
                await interaction.followup.send("Cannot send message to this user. They may have blocked the bot or disabled DMs from server members.", ephemeral=True)
            else:
                await interaction.followup.send("Error sending message.", ephemeral=True)
            return
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await interaction.followup.send("Unexpected error.", ephemeral=True)
            return

        await interaction.followup.send("Message sent successfully.", ephemeral=True)
