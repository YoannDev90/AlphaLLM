import discord
from discord.ext import commands
import logging
import sys

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.command(name="stop", aliases=["exit"])
    @commands.is_owner()
    async def stop(ctx: commands.Context):
        """
        Arrête complètement le bot et le programme.
        """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            logger.warning("Impossible de supprimer le message de commande.")

        await ctx.send("🛑 Arrêt complet du bot...")
        logger.info("Demande d'arrêt reçue")

        if bot.is_closed():
            return

        await bot.close()
        
        sys.exit(0)
