import logging

import discord

from config import LOGGER_NAME
from utils.discord_utils.commands_ids import command_id_manager

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(
        name="commands", description="Show all available commands with their mentions"
    )
    async def commands(interaction: discord.Interaction):
        logger.info(f"Commande /commands exécutée par {interaction.user.display_name}")

        try:
            # Créer l'embed principal
            embed = discord.Embed(
                title="🤖 AlphaLLM - Available Commands",
                description="Here are all the available commands you can use:",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow(),
            )

            # Commands principales pour tous les utilisateurs
            embed.add_field(
                name="💬 Main Commands",
                value=(
                    f"{command_id_manager.get_command_mention('ask')} - Ask questions to various AI models\n"
                    f"{command_id_manager.get_command_mention('image-gen')} - Generate images from text prompts\n"
                    f"{command_id_manager.get_command_mention('image-edit')} - Edit images based on text prompts\n"
                    f"{command_id_manager.get_command_mention('ping')} - Check the bot's latency and status"
                ),
                inline=False,
            )

            # Commands de configuration
            embed.add_field(
                name="⚙️ Configuration Commands",
                value=(
                    f"{command_id_manager.get_command_mention('guild-config')} - Configure server settings (Admin only)\n"
                    f"{command_id_manager.get_command_mention('clear-history')} - Delete chat history\n"
                    f"{command_id_manager.get_command_mention('resources')} - Show resources metrics"
                ),
                inline=False,
            )

            # Commands d'aide et support
            embed.add_field(
                name="🆘 Help & Support Commands",
                value=(
                    f"{command_id_manager.get_command_mention('help-bot')} - Show detailed help information\n"
                    f"{command_id_manager.get_command_mention('status')} - Show details ping informations\n"
                    f"{command_id_manager.get_command_mention('support')} - Get support server link\n"
                    f"{command_id_manager.get_command_mention('contact-dev')} - Contact the developer directly"
                ),
                inline=False,
            )

            # Information sur la mention du bot
            embed.add_field(
                name="💡 Chat with AlphaLLM",
                value=(
                    f"You can also chat directly with me by mentioning <@{bot.user.id}> "
                    f"in your messages anywhere in the server!"
                ),
                inline=False,
            )

            # Footer avec informations utiles
            embed.set_footer(
                text=f"Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url,
            )

            # Thumbnail avec l'avatar du bot
            embed.set_thumbnail(url=bot.user.display_avatar.url)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des commandes: {e}")

            # Embed de fallback en cas d'erreur
            fallback_embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while loading the commands list. Please try again later.",
                color=discord.Color.red(),
            )

            try:
                await interaction.response.send_message(
                    embed=fallback_embed, ephemeral=True
                )
            except:
                await interaction.followup.send(embed=fallback_embed, ephemeral=True)
