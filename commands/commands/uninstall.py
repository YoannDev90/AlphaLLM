import discord
from discord import app_commands
import logging
from typing import Literal
from datetime import datetime, timedelta

logger = logging.getLogger('AlphaLLM')

# IDs des bots AlphaLLM
bot_ids = {
    "ChatGPT": 1370683080892747796,
    "DeepSeek": 1370682029460684850,
    "EvilGPT": 1370685660326920252,
    "Gemini": 1370683258274185349,
    "Grok": 1370683169522847827,
    "Llama": 1370685321703854110,
    "Mistral": 1370685184269352962,
    "Phi": 1370685419557224538,
    "Perplexity": 1370681547740418079,
    "Qwen": 1370686144542539846
}

# Descriptions des bots avec emojis
bot_descriptions = {
    "ChatGPT": "🤖 Based on GPT-4, excellent for conversation and general tasks.",
    "DeepSeek": "🧠 Advanced reasoning model specialized in solving complex problems.",
    "EvilGPT": "😈 Alternative version with a more provocative and free personality.",
    "Gemini": "💎 Google's multimodal AI, capable of processing text, images and more.",
    "Grok": "🚀 xAI's AI assistant with a unique and innovative approach.",
    "Llama": "🦙 Meta's open-source model, performant and transparent.",
    "Mistral": "🌪️ Fast and efficient French AI for various tasks.",
    "Phi": "🌍️ Compact but powerful Microsoft model, optimized for performance.",
    "Perplexity": "🔍 Specialist in search and real-time information.",
    "Qwen": "🈳 Alibaba's model with excellent multilingual capabilities."
}

class UninstallConfirmView(discord.ui.View):
    def __init__(self, bot_name: str, bot_id: int, delete_messages: bool):
        super().__init__(timeout=60)
        self.bot_name = bot_name
        self.bot_id = bot_id
        self.delete_messages = delete_messages
        self.confirmed = False

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.danger)
    async def confirm_uninstall(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        
        try:
            # Supprimer les messages si demandé
            if self.delete_messages:
                await interaction.response.defer()
                deleted_count = 0
                
                # Parcourir tous les canaux textuels
                for channel in interaction.guild.text_channels:
                    try:
                        # Vérifier les permissions
                        if not channel.permissions_for(interaction.guild.me).read_message_history:
                            continue
                        if not channel.permissions_for(interaction.guild.me).manage_messages:
                            continue
                            
                        # Supprimer les messages du bot des 14 derniers jours
                        deleted = await channel.purge(
                            limit=None,
                            after=discord.utils.utcnow() - timedelta(days=14),
                            check=lambda m: m.author.id == self.bot_id,
                            bulk=True
                        )
                        deleted_count += len(deleted)
                    except discord.Forbidden:
                        # Ignorer les canaux sans permissions
                        continue
                    except Exception as e:
                        logger.error(f"Erreur lors de la suppression des messages dans {channel.name}: {str(e)}")
                        continue
            
            # Expulser le bot en utilisant ban/unban (équivalent à un kick)
            try:
                bot_user = await interaction.client.fetch_user(self.bot_id)
                await interaction.guild.ban(bot_user, reason=f"Uninstalled by {interaction.user.display_name}")
                await interaction.guild.unban(bot_user, reason="Uninstall completed - bot can be reinstalled")
                bot_removed = True
            except discord.NotFound:
                # Le bot n'est pas sur le serveur
                bot_removed = False
            except discord.Forbidden:
                # Pas les permissions pour ban/unban
                bot_removed = False
            
            # Message de confirmation
            if bot_removed:
                embed = discord.Embed(
                    title="✅ Bot Successfully Uninstalled",
                    description=f"**{self.bot_name}** has been successfully removed from the server.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
            else:
                embed = discord.Embed(
                    title="⚠️ Manual Removal Required",
                    description=f"**{self.bot_name}** must be manually removed from the server." + 
                               (f"\n\n🗑️ All messages from this bot in the last 14 days have been deleted." if self.delete_messages else ""),
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                
                embed.add_field(
                    name="📋 Manual Steps",
                    value="1. Go to **Server Settings** → **Members**\n2. Find and click on the bot\n3. Click **Kick** to remove it from the server",
                    inline=False
                )
            
            if self.delete_messages:
                embed.add_field(
                    name="Messages Deleted",
                    value=f"🗑️ {deleted_count} messages from the last 14 days have been deleted.",
                    inline=False
                )
            
            embed.set_footer(
                text=f"Uninstalled by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            logger.info(f"Bot {self.bot_name} désinstallé du serveur {interaction.guild.name} par {interaction.user.display_name}")
            
            if self.delete_messages:
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            else:
                await interaction.response.edit_message(embed=embed, view=None)
                
        except discord.NotFound:
            embed = discord.Embed(
                title="❌ Bot Not Found",
                description=f"The bot **{self.bot_name}** is not on this server or has already been removed.",
                color=discord.Color.red()
            )
            if self.delete_messages:
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            else:
                await interaction.response.edit_message(embed=embed, view=None)
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="I don't have permission to remove this bot from the server.",
                color=discord.Color.red()
            )
            if self.delete_messages:
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            else:
                await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            logger.error(f"Erreur lors de la désinstallation du bot: {str(e)}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while uninstalling the bot.",
                color=discord.Color.red()
            )
            if self.delete_messages:
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            else:
                await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_uninstall(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🚫 Uninstall Cancelled",
            description="The bot uninstallation has been cancelled.",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot: discord.Client):
    @bot.tree.command(name="uninstall", description="Remove an AlphaLLM bot from the server")
    @app_commands.describe(
        bot_name="The bot to remove from the server",
        delete_messages="Whether to delete the bot's messages from the last 14 days"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def uninstall(
        interaction: discord.Interaction,
        bot_name: Literal["ChatGPT", "DeepSeek", "EvilGPT", "Gemini", "Grok", "Llama", "Mistral", "Phi", "Perplexity", "Qwen"],
        delete_messages: bool = False
    ):
        logger.info(f"Commande /uninstall exécutée par {interaction.user.display_name} pour le bot {bot_name}")
        
        # Vérifier les permissions
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You must have server management permissions to use this command.", ephemeral=True)
            return
        
        bot_id = bot_ids[bot_name]
        
        # Créer l'embed de confirmation
        description = bot_descriptions.get(bot_name)
        if not description:
            description = "No description available."

        embed = discord.Embed(
            title="⚠️ Confirm Bot Uninstall",
            description=f"Are you sure you want to remove **{bot_name}** from this server?\n\n{description}",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        
        if delete_messages:
            embed.add_field(
                name="⚠️ Message Deletion",
                value="🗑️ **All messages from this bot in the last 14 days will be permanently deleted.**",
                inline=False
            )
        
        embed.add_field(
            name="Bot Information",
            value=f"**Bot:** {bot_name}\n**ID:** {bot_id}\n**Action:** This will remove the bot from the server",
            inline=False
        )
        
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        # Créer la vue de confirmation
        view = UninstallConfirmView(bot_name, bot_id, delete_messages)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
