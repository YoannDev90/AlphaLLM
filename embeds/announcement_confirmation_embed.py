import discord
import logging
from datetime import datetime
from utils.config import logger_name

logger = logging.getLogger(logger_name)

class ConfirmationView(discord.ui.View):
    def __init__(self, original_message: str, file_path: str, translation_manager, total_guilds: int):
        super().__init__(timeout=300)
        self.original_message = original_message
        self.file_path = file_path
        self.translation_manager = translation_manager
        self.total_guilds = total_guilds
        
    @discord.ui.button(label="✅ Confirmer l'envoi", style=discord.ButtonStyle.success, emoji="📢")
    async def confirm_send(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        try:
            for item in self.children:
                item.disabled = True
            
            embed = discord.Embed(
                title="🔄 Envoi de l'annonce en cours...",
                description=f"Envoi sur {self.total_guilds} serveurs...",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            await interaction.edit_original_response(embed=embed, view=self)
            
            # Import des fonctions nécessaires
            try:
                from embeds.announcement_embed import AnnouncementTranslationView
                from commands.admin_commands.announce import send_announcement_to_guilds
                
                translation_view = AnnouncementTranslationView(self.original_message, self.file_path)
                
                announced_guilds, failed_guilds = await send_announcement_to_guilds(
                    interaction.client, self.original_message, translation_view
                )
            except ImportError:
                announced_guilds = 0
                failed_guilds = self.total_guilds
            
            final_embed = discord.Embed(
                title="✅ Annonce envoyée avec succès !",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            final_embed.add_field(
                name="📊 Résultats",
                value=f"• **{announced_guilds} serveurs** : annonce envoyée\n"
                      f"• **{failed_guilds} serveurs** : échecs\n"
                      f"• **{len(self.translation_manager.translations)} langues** traduites",
                inline=False
            )
            final_embed.add_field(
                name="📁 Fichier",
                value=f"`{self.file_path}`",
                inline=False
            )
            
            await interaction.edit_original_response(embed=final_embed, view=None)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi confirmé de l'annonce: {e}")
            error_embed = discord.Embed(
                title="❌ Erreur lors de l'envoi",
                description=f"Une erreur est survenue: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=error_embed, view=None)
    
    @discord.ui.button(label="👀 Aperçu traductions", style=discord.ButtonStyle.secondary, emoji="🌍")
    async def preview_translations(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Import des langues supportées
            try:
                from commands.admin_commands.announce import SUPPORTED_LANGUAGES
            except ImportError:
                SUPPORTED_LANGUAGES = {}
            
            preview_langs = ['fr', 'es', 'de', 'ja', 'ru']
            available_langs = [lang for lang in preview_langs if lang in self.translation_manager.translations]
            
            embed = discord.Embed(
                title="🌍 Aperçu des traductions",
                description=f"**Message original :**\n{self.original_message[:500]}{'...' if len(self.original_message) > 500 else ''}",
                color=discord.Color.blue()
            )
            
            for lang_code in available_langs[:3]:
                lang_info = SUPPORTED_LANGUAGES.get(lang_code, {'name': lang_code, 'emoji': '🌍'})
                translated_text = self.translation_manager.translations[lang_code]
                
                embed.add_field(
                    name=f"{lang_info['emoji']} {lang_info['name']}",
                    value=translated_text[:200] + ("..." if len(translated_text) > 200 else ""),
                    inline=False
                )
            
            embed.add_field(
                name="📊 Statistiques complètes",
                value=f"• **Total :** {len(self.translation_manager.translations)} langues traduites\n"
                      f"• **Fichier :** `{self.file_path}`",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'aperçu des traductions: {e}")
            await interaction.followup.send(
                f"❌ Erreur lors de l'affichage de l'aperçu: {str(e)}", 
                ephemeral=True
            )
    
    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.danger, emoji="🚫")
    async def cancel_send(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🚫 Annonce annulée",
            description="L'envoi de l'annonce a été annulé.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="📁 Fichier temporaire",
            value=f"`{self.file_path}` (non envoyé)",
            inline=False
        )
        
        await interaction.edit_original_response(embed=embed, view=None)

def create_announcement_confirmation_embed(message: str, file_path: str, translation_count: int, total_guilds: int) -> discord.Embed:
    """Créer l'embed de confirmation pour l'envoi d'annonce"""
    embed = discord.Embed(
        title="📢 Confirmation d'envoi d'annonce",
        description=f"**Message à envoyer :**\n{message[:500]}{'...' if len(message) > 500 else ''}",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="📊 Détails de l'envoi",
        value=f"• **Serveurs cibles :** {total_guilds}\n"
              f"• **Langues traduites :** {translation_count}\n"
              f"• **Fichier :** `{file_path}`",
        inline=False
    )
    
    embed.add_field(
        name="⚠️ Attention",
        value="Cette action enverra l'annonce à tous les serveurs où le bot est présent. Confirmez-vous l'envoi ?",
        inline=False
    )
    
    return embed
