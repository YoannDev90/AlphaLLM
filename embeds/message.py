import discord
import logging
from utils.config import logger_name, TIMEOUT_IMAGE_VIEW

logger = logging.getLogger(logger_name)

class MessageView(discord.ui.View):
    def __init__(self, original_question, model, response_data=None, bot=None, search_internet=None):
        super().__init__(timeout=TIMEOUT_IMAGE_VIEW)
        self.original_question = original_question
        self.model = model
        self.response_data = response_data
        self.bot = bot
        self.search_internet = search_internet
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
        
        # Import des fonctions nécessaires à l'exécution
        from utils.user_manager import new_interaction
        from utils.ai_utils import generate_response
        from utils.table_converter import detect_and_convert_tables
        from utils.ai_process import smart_long_messages_with_view
        
        new_interaction(interaction.user.id)
        
        try:
            # Créer un message factice pour simuler une mention
            class MockMessage:
                def __init__(self, original_interaction):
                    self.author = original_interaction.user
                    self.channel = original_interaction.channel
                    self.guild = original_interaction.guild
                    self.attachments = []
            
            mock_message = MockMessage(interaction)
            
            # Générer la réponse en utilisant generate_response directement
            parameters = {
                "history": True, 
                "preprompt": True, 
                "tools": False, 
                "internet": self.search_internet if self.search_internet is not None else False, 
                "audio": False,
                "raw": False,
                "model": self.model if hasattr(self, 'model') and self.model else self.bot.user.id if isinstance(self.bot, discord.Client) else self.bot.id
            }
            
            response = await generate_response(
                user_id=int(interaction.user.id),
                server_id=int(interaction.channel.id if not interaction.guild else interaction.guild.id),
                raw_content=self.original_question,
                attachments=[],
                bot=self.bot,
                user=interaction.user.display_name,
                parameters=parameters
            )
            
            # Extract response text properly
            if isinstance(response, dict) and 'response' in response:
                response_text = response['response']
            elif isinstance(response, str):
                response_text = response
            else:
                await interaction.followup.send("❌ Unexpected response format during regeneration.")
                return
            
            response_text = detect_and_convert_tables(response_text)
            await smart_long_messages_with_view(interaction.channel, response_text, self.original_question, self.model, response, self.bot)
            
        except Exception as e:
            logger.error(f"Erreur lors de la régénération de réponse pour {interaction.user.display_name}: {str(e)}")
            await interaction.followup.send("❌ Unexpected error during response regeneration.")

    @discord.ui.button(emoji="✏️", label="Edit", style=discord.ButtonStyle.gray)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Édition de question demandée par {interaction.user.display_name}")
        
        from utils.user_manager import new_interaction
        
        new_interaction(interaction.user.id)

        modal = EditQuestionModal(self.original_question, self.model, self.bot, self.search_internet)
        await interaction.response.send_modal(modal)

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
        
        embed.add_field(name="❓ Original Question", value=f"```{self.original_question[:1000]}{'...' if len(self.original_question) > 1000 else ''}```", inline=False)
        
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


class EditQuestionModal(discord.ui.Modal):
    def __init__(self, original_question, model, bot, search_internet):
        super().__init__(title="Edit Question")
        self.original_question = original_question
        self.model = model
        self.bot = bot
        self.search_internet = search_internet
        
        self.question_input = discord.ui.TextInput(
            label="New question",
            placeholder="Enter your new question...",
            style=discord.TextStyle.paragraph,
            max_length=2000,
            default=original_question,
            required=True
        )
        self.add_item(self.question_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        new_question = self.question_input.value
        
        if not new_question.strip():
            await interaction.followup.send("❌ The question cannot be empty.", ephemeral=True)
            return
        
        try:
            from utils.ai_utils import generate_response
            from utils.table_converter import detect_and_convert_tables
            from utils.ai_process import smart_long_messages_with_view
            
            # Générer la réponse en utilisant generate_response directement
            parameters = {
                "history": True, 
                "preprompt": True, 
                "tools": False, 
                "internet": self.search_internet if self.search_internet is not None else False, 
                "audio": False,
                "raw": False,
                "model": self.model if hasattr(self, 'model') and self.model else self.bot.user.id if isinstance(self.bot, discord.Client) else self.bot.id
            }
            
            response = await generate_response(
                user_id=int(interaction.user.id),
                server_id=int(interaction.channel.id if not interaction.guild else interaction.guild.id),
                raw_content=new_question,
                attachments=[],
                bot=self.bot,
                user=interaction.user.display_name,
                parameters=parameters
            )
            
            # Extract response text properly
            if isinstance(response, dict) and 'response' in response:
                response_text = response['response']
            elif isinstance(response, str):
                response_text = response
            else:
                await interaction.followup.send("❌ Unexpected response format.")
                return
            
            response_text = detect_and_convert_tables(response_text)
            await smart_long_messages_with_view(interaction.channel, response_text, new_question, self.model, response, self.bot)
            
            logger.info(f"Question éditée et nouvelle réponse envoyée à {interaction.user.display_name}")
            
        except Exception as e:
            await interaction.followup.send("❌ Error processing the edited question.")
            logger.error(f"Échec de l'édition de question pour {interaction.user.display_name}: {str(e)}")
