import discord
import logging
from config import LOGGER_NAME
from utils.handlers.table import detect_and_convert_tables
from utils.unified_text import Origin, unified_text_gen

logger = logging.getLogger(LOGGER_NAME)

class MessageView(discord.ui.View):
    def __init__(self, original_question, model, response_data=None, bot=None):
        super().__init__(timeout=300)
        self.original_question = original_question
        self.model = model
        self.responses = [response_data] if response_data else []
        self.current_index = 0
        self.bot = bot
        self.message = None
        self.regenerated = False

    async def on_timeout(self):
        """Supprime les boutons lorsque la vue expire après 30 secondes"""
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass

    @discord.ui.button(emoji="🔄", label="Regenerate", style=discord.ButtonStyle.gray)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.regenerated:
            await interaction.response.send_message("❌ Regeneration already done.", ephemeral=True)
            return
        logger.info(f"Régénération de réponse demandée par {interaction.user.display_name}")
        await interaction.response.defer()
        button.disabled = True
        self.regenerated = True
        await interaction.message.edit(view=self)
        try:
            results = [result async for result in unified_text_gen(
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
            if not results:
                await interaction.followup.send("❌ No response generated.")
                return
            result = results[0]
            self.responses.append(result)
            self.current_index = 1
            response_text = result.response
            # Enable and set switch button
            for child in self.children:
                if hasattr(child, 'label') and 'Switch' in child.label:
                    child.disabled = False
                    child.label = "View Original"
                    child.emoji = "⬅️"
            await interaction.message.edit(content=response_text, view=self)
            
        except Exception as e:
            logger.error(f"Erreur lors de la régénération de réponse pour {interaction.user.display_name}: {str(e)}")
            await interaction.followup.send("❌ Unexpected error during response regeneration.")

    @discord.ui.button(emoji="📊", label="Details", style=discord.ButtonStyle.gray)
    async def show_details(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.debug(f"Affichage des détails demandé par {interaction.user.display_name}")
        
        response_data = self.responses[self.current_index] if self.responses else None
        if not response_data:
            await interaction.response.send_message("❌ No detailed information available.", ephemeral=True, delete_after=60)
            return
        
        try:
            embed = discord.Embed(title="📊 Response Details")
            embed.add_field(name="🤖 Model", value=f"`{response_data.model}`", inline=False)
            embed.add_field(name="🔢 Tokens Used", value=f"`{response_data.usage}`", inline=False)
            embed.add_field(name="⏱️ Response Time", value=f"`{response_data.elapsed_time}`", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=60)
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'embed de détails pour {interaction.user.display_name}: {str(e)}")

    @discord.ui.button(label="Switch Response", emoji="🔄", style=discord.ButtonStyle.gray, disabled=True)
    async def switch_response(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.responses) < 2:
            await interaction.response.send_message("❌ No alternative response available.", ephemeral=True)
            return
        self.current_index = 1 - self.current_index
        response_text = self.responses[self.current_index].response
        if self.current_index == 0:
            button.label = "View Regenerated"
            button.emoji = "➡️"
        else:
            button.label = "View Original"
            button.emoji = "⬅️"
        await interaction.response.edit_message(content=response_text, view=self)

    @discord.ui.button(emoji="🗑️", label="Delete", style=discord.ButtonStyle.gray)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.debug(f"Suppression de message demandée par {interaction.user.display_name}")
        
        await interaction.message.edit(view=None)
        await interaction.message.delete()
