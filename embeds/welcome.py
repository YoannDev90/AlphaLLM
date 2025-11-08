import discord
import datetime
import logging
from utils.config import logger_name
from langs.language_manager import language_manager, SUPPORTED_LANGUAGES
from utils import command_id_manager

logger = logging.getLogger(logger_name)

class WelcomeLanguageView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.setup_language_buttons()
    
    def setup_language_buttons(self):        
        for lang_code, lang_info in SUPPORTED_LANGUAGES.items():
            button = discord.ui.Button(
                style=discord.ButtonStyle.gray,
                emoji=lang_info['emoji'],
                custom_id=f"welcome_lang_{lang_code}"
            )
            button.callback = self.create_language_callback(lang_code, lang_info)
            self.add_item(button)
    
    def create_language_callback(self, lang_code: str, lang_info: dict):
        async def language_callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            
            try:
                # Utiliser les traductions du fichier toml
                welcome_section = language_manager.get_section(lang_code, 'welcome')
                
                embed = discord.Embed(
                    title=welcome_section.get('title', '🤖 Welcome to AlphaLLM!'),
                    description=welcome_section.get('description', 'Thank you for adding AlphaLLM to your server!'),
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                
                embed.add_field(
                    name=command_id_manager.get_command_mention("ask"), 
                    value=welcome_section.get('ask_command', 'Ask questions to various AI models'), 
                    inline=False
                )
                embed.add_field(
                    name=command_id_manager.get_command_mention("image"), 
                    value=welcome_section.get('image_command', 'Generate images from text prompts'), 
                    inline=False
                )
                embed.add_field(
                    name=command_id_manager.get_command_mention("ping"), 
                    value=welcome_section.get('ping_command', 'Check the bot\'s latency'), 
                    inline=False
                )
                embed.add_field(
                    name=command_id_manager.get_command_mention("user-config"), 
                    value=welcome_section.get('user_config_command', 'Configure your personal settings'), 
                    inline=False
                )
                embed.add_field(
                    name=command_id_manager.get_command_mention("guild-config"), 
                    value=welcome_section.get('guild_config_command', 'Configure server settings'), 
                    inline=False
                )
                embed.add_field(
                    name=f"🌍 {welcome_section.get('languages_field', 'Multiple Languages')}", 
                    value=welcome_section.get('languages_description', 'Available in multiple languages!'), 
                    inline=False
                )
                
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)
                embed.set_footer(
                    text=welcome_section.get('footer', 'Added to {guild_name}').format(guild_name=interaction.guild.name),
                    icon_url=interaction.guild.icon.url if interaction.guild.icon else None
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f"Erreur dans le callback de langue {lang_code}: {e}")
                await interaction.followup.send("❌ An error occurred while translating the message.", ephemeral=True)
        
        return language_callback

def create_welcome_embed(bot, guild, lang_code: str = 'en') -> discord.Embed:
    """Crée l'embed de bienvenue pour une langue donnée"""
    welcome_section = language_manager.get_section(lang_code, 'welcome')
    
    embed = discord.Embed(
        title=welcome_section.get('title', '🤖 Welcome to AlphaLLM!'),
        description=welcome_section.get('description', 'Thank you for adding AlphaLLM to your server! Here are the main commands you can use:'),
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )
    
    embed.add_field(
        name=command_id_manager.get_command_mention("ask"),
        value=welcome_section.get('ask_command', 'Ask questions to various AI models (GPT, Llama, Gemini, etc.)'),
        inline=False
    )
    embed.add_field(
        name=command_id_manager.get_command_mention("image"),
        value=welcome_section.get('image_command', 'Generate images from text prompts using AI models'),
        inline=False
    )
    embed.add_field(
        name=command_id_manager.get_command_mention("ping"),
        value=welcome_section.get('ping_command', 'Check the bot\'s latency and connection status'),
        inline=False
    )
    embed.add_field(
        name=command_id_manager.get_command_mention("user-config"),
        value=welcome_section.get('user_config_command', 'Configure your personal settings (language, image preferences, etc.)'),
        inline=False
    )
    embed.add_field(
        name=command_id_manager.get_command_mention("guild-config"),
        value=welcome_section.get('guild_config_command', 'Configure server settings (language, announcement channel) - Admin only'),
        inline=False
    )
    
    embed.add_field(
        name=f"🌍 {welcome_section.get('languages_field', 'Multiple Languages')}",
        value=welcome_section.get('languages_description', 'Click a language button below to see this message in your preferred language!'),
        inline=False
    )
    
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(
        text=welcome_section.get('footer', 'Added to {guild_name}').format(guild_name=guild.name),
        icon_url=guild.icon.url if guild.icon else None
    )
    
    return embed
