import discord
import logging

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="ping", description="Show the bot's latency")
    async def ping(interaction: discord.Interaction):
        logger.info(f"Commande /ping exécutée par {interaction.user.display_name}")
        await interaction.response.defer()

        latency = round(bot.latency * 1000)

        embed = discord.Embed(
            title=f"Current latency: {latency} ms",
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)
