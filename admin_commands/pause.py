import discord
from discord.ext import commands
import logging

logger = logging.getLogger('AlphaLLM')


async def setup(bot: discord.Client):
    @bot.command(name="ps", aliases=["pause"])
    @commands.is_owner()
    async def pause(ctx: commands.Context, user_id: int):
        logger.info(f"Commande pause exécutée par {ctx.author.display_name}")

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            logger.warning("Impossible de supprimer le message de commande. Vérifiez les permissions.")

        #PAUSE
        await ctx.send(f"L'utilisateur avec l'ID {user_id} a été ajouté à la liste blanche.")
