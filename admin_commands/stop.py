import discord
import logging
import sys
import os

logger = logging.getLogger('AlphaLLM')
OWNER_ID = int(os.getenv('DEV_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))

async def setup(bot: discord.Client):
    @bot.tree.command(name="stop", description="Arrête complètement le bot et le programme")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def stop(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /stop exécutée par {interaction.user.display_name}")

        if interaction.user.id != OWNER_ID:
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        await interaction.followup.send("🛑 Arrêt complet du bot...", ephemeral=True)
        logger.info("Demande d'arrêt reçue")

        if bot.is_closed():
            return

        await bot.close()
        sys.exit(0)
