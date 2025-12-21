import discord
import logging
from config import LOGGER_NAME
from utils.handlers.table import detect_and_convert_tables
from utils.unified_text import Origin, unified_text_manager

logger = logging.getLogger(LOGGER_NAME)

class MessageView(discord.ui.View):
    def __init__(self, original_message, model, response_data=None, bot=None):
        super().__init__(timeout=300)
        self.original_message = original_message
        self.model = model
        self.response_data = response_data
        self.bot = bot
        self.message = None

    async def on_timeout(self):
        """Supprime les boutons lorsque la vue expire après 30 secondes"""
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass

    @discord.ui.button(emoji="🔄", label="Regenerate", style=discord.ButtonStyle.gray)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Régénération de réponse demandée par {interaction.user.display_name}")
        await interaction.response.defer()
        from utils.handlers.messages import smart_long_messages_with_view
        try:
            results = [result async for result in unified_text_manager(
                user_id=interaction.user.id,
                conv_id=interaction.channel.id,
                input=self.original_question,
                model=self.model,
                files=None,
                origin=Origin.DISCORD,
                message=interaction,
                bot=self.bot,
                stream=False
            )]
            result = results[0]
            response_text = result.response
            await smart_long_messages_with_view(interaction.channel, response_text, self.original_question, self.model, result, self.bot)
            
        except Exception as e:
            logger.error(f"Erreur lors de la régénération de réponse pour {interaction.user.display_name}: {str(e)}")
            await interaction.followup.send("❌ Unexpected error during response regeneration.")

    @discord.ui.button(emoji="📊", label="Details", style=discord.ButtonStyle.gray)
    async def show_details(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Affichage des détails demandé par {interaction.user.display_name}")
        
        if not self.response_data:
            await interaction.response.send_message("❌ No detailed information available.", ephemeral=True)
            return
        
        # Créer un embed avec les informations détaillées
        embed = discord.Embed(
            title="📊 Response Details",
            color=0x00ff00
        )
        
        # Ajouter les informations disponibles
        if isinstance(self.response_data, dict):
            if "model" in self.response_data:
                embed.add_field(name="🤖 Model", value=f"`{self.response_data['model']}`", inline=True)
            
            if "usage" in self.response_data:
                usage = self.response_data['usage']
                if isinstance(usage, dict):
                    if "total_tokens" in usage:
                        embed.add_field(name="🔢 Total Tokens", value=f"`{usage['total_tokens']}`", inline=True)
                    if "prompt_tokens" in usage:
                        embed.add_field(name="📝 Prompt Tokens", value=f"`{usage['prompt_tokens']}`", inline=True)
                    if "completion_tokens" in usage:
                        embed.add_field(name="💬 Completion Tokens", value=f"`{usage['completion_tokens']}`", inline=True)
                else:
                    embed.add_field(name="🔢 Tokens Used", value=f"`{usage}`", inline=True)
            
            if "elapsed_time" in self.response_data:
                embed.add_field(name="⏱️ Response Time", value=f"`{self.response_data['elapsed_time']}`", inline=True)
            
            if "finish_reason" in self.response_data:
                embed.add_field(name="🏁 Finish Reason", value=f"`{self.response_data['finish_reason']}`", inline=True)
            
            # Ajouter d'autres champs disponibles
            for key, value in self.response_data.items():
                if key not in ["response", "model", "usage", "elapsed_time", "finish_reason"]:
                    if isinstance(value, (str, int, float)):
                        embed.add_field(name=f"🔍 {key.replace('_', ' ').title()}", value=f"`{value}`", inline=True)
        
        embed.add_field(name="❓ Original Question", value=f"```{self.original_message.content[:1000]}{'...' if len(self.original_message.content) > 1000 else ''}```", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(emoji="📌", label="Pin", style=discord.ButtonStyle.gray)
    async def pin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel.permissions_for(interaction.user).manage_messages:
            await interaction.response.send_message("You do not have permission to pin messages.", ephemeral=True)
            return
        logger.info(f"Épinglage de message demandé par {interaction.user.display_name}")
        await interaction.response.defer()
        await interaction.message.pin()
        await interaction.followup.send("Message pinned.", delete_after=2)

    @discord.ui.button(emoji="🗑️", label="Delete", style=discord.ButtonStyle.gray)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Suppression de message demandée par {interaction.user.display_name}")
        
        # Si possible, supprimer aussi le message de la question originale
        if hasattr(self, 'original_message') and self.original_message:
            try:
                await self.original_message.delete()
            except Exception as e:
                logger.debug(f"Impossible de supprimer le message original: {e}")
        
        # Supprimer le message de réponse
        await interaction.message.edit(view=None)
        await interaction.message.delete()
