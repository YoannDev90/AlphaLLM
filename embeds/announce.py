import discord
import datetime
import logging
from utils.config import logger_name
import os
from langs.language_manager import language_manager, SUPPORTED_LANGUAGES

logger = logging.getLogger(logger_name)

class AnnouncementTranslationView(discord.ui.View):
    def __init__(self, original_message: str, file_path: str):
        super().__init__(timeout=None)
        self.original_message = original_message
        self.file_path = file_path
        self.setup_language_buttons()
    
    def setup_language_buttons(self):
        for lang_code, lang_info in SUPPORTED_LANGUAGES.items():
            button = discord.ui.Button(
                style=discord.ButtonStyle.gray,
                emoji=lang_info['emoji'],
                custom_id=f"announce_lang_{lang_code}"
            )
            button.callback = self.create_language_callback(lang_code, lang_info)
            self.add_item(button)
    
    def create_language_callback(self, lang_code: str, lang_info: dict):
        async def language_callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            
            try:
                # Pour les annonces, nous utilisons le système de traduction automatique existant
                # ou affichons le message original si pas de traduction disponible
                from utils.translator import TranslationManager
                
                translation_manager = TranslationManager(self.original_message, self.file_path)
                await translation_manager.load_translations()
                
                translated_text = await translation_manager.get_translation(lang_code)
                
                embed = discord.Embed(
                    title=language_manager.get_translation(lang_code, 'announce', 'news_title'),
                    description=translated_text,
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f"Erreur dans le callback de traduction d'annonce {lang_code}: {e}")
                # Fallback: afficher le message original
                embed = discord.Embed(
                    title="📢 News",
                    description=self.original_message,
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
        
        return language_callback

def create_announcement_embed(message: str, lang_code: str = 'en') -> discord.Embed:
    """Crée l'embed d'annonce pour une langue donnée"""
    embed = discord.Embed(
        title=language_manager.get_translation(lang_code, 'announce', 'news_title'),
        description=message,
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(text=language_manager.get_translation(lang_code, 'announce', 'translation_footer'))
    
    return embed
