import discord
from discord.ext import commands, tasks
import logging
from utils.config import logger_name, GUILD_ID, is_dev_id, LOGGER_NAME
from dotenv import load_dotenv
from utils import get_announce_channel
from utils import TranslationManager, SUPPORTED_LANGUAGES, load_translations
from utils import command_id_manager
from bots.bot import bot as main_bot
from embeds.poll import PollView, ResultsCollectorView, PollConfirmationView, poll_results
import os
import json
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.font_manager as fm

load_dotenv()

logger = logging.getLogger(logger_name)

active_poll_messages: Dict[str, List[Dict]] = {}

async def create_poll_chart(question: str, options: List[str], results: Dict[str, int], total_votes: int) -> BytesIO:
    try:
        plt.style.use('default')

        fig, ax = plt.subplots(figsize=(8, max(3.5, len(options) * 0.8)))
        fig.patch.set_facecolor('#232529')
        ax.set_facecolor('#232529')
        
        labels = []
        counts = []
        for option in options:
            labels.append(option)
            counts.append(results.get(option, 0))
        
        y_pos = np.arange(len(labels))
        bar_color = "#0051ff"
        bg_bar_color = "#2d2f34"
        
        ax.barh(y_pos, [max(counts) if counts else 1]*len(labels),
                color=bg_bar_color, height=0.8, zorder=1, edgecolor='none')
        bars = ax.barh(y_pos, counts, color=bar_color, height=0.8, zorder=2, edgecolor='none')

        ax.set_yticks([])
        ax.set_xticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.axis('off')

        max_count = max(counts) if counts else 1
        pad = max_count * 0.018

        for i, (bar, label, count) in enumerate(zip(bars, labels, counts)):
            bar_width = bar.get_width()
            bar_y = bar.get_y() + bar.get_height() / 2
            percent = (count / total_votes * 100) if total_votes > 0 else 0
            score_text = f"({count}) {percent:.0f}%"

            ax.text(pad, bar_y, label,
                    color='white', fontsize=14, fontweight='bold',
                    va='center', ha='left', zorder=10, clip_on=True)

            ax.set_xlim(0, max_count * 1.2)
            ax.text(max_count * 1.2 - pad, bar_y, score_text,
                    color='white', fontsize=14, fontweight='bold',
                    va='center', ha='right', zorder=10, clip_on=False)

        plt.subplots_adjust(left=0.04, right=0.98, top=0.87, bottom=0.08)
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', facecolor=fig.get_facecolor(), edgecolor='none', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close(fig)
        return buffer
    except Exception as e:
        logger.error(f"Erreur lors de la génération du graphique de sondage: {e}")
        plt.close('all')
        return None

@tasks.loop(minutes=5)
async def update_poll_messages():
    """Mise à jour automatique des messages de sondage toutes les 5 minutes"""
    try:
        for poll_id, messages in active_poll_messages.items():
            if poll_id not in poll_results:
                continue
                
            for message_data in messages:
                try:
                    guild = main_bot.get_guild(message_data['guild_id'])
                    if not guild:
                        continue
                        
                    channel = guild.get_channel(message_data['channel_id'])
                    if not channel:
                        continue
                        
                    message = await channel.fetch_message(message_data['message_id'])
                    if not message:
                        continue
                    
                    guild_results = poll_results[poll_id].get(str(guild.id), {})
                    total_votes = sum(guild_results.values())
                    
                    embed = discord.Embed(
                        title="📊 Sondage",
                        description=message_data['question'],
                        color=discord.Color.blue(),
                        timestamp=datetime.now()
                    )
                    
                    if total_votes > 0:
                        for option, count in guild_results.items():
                            percentage = (count / total_votes * 100) if total_votes > 0 else 0
                            bar_length = int(percentage / 5)
                            bar = "█" * bar_length + "░" * (20 - bar_length)
                            
                            embed.add_field(
                                name=f"{option}",
                                value=f"`{bar}` **{count}** votes (**{percentage:.1f}%**)",
                                inline=False
                            )
                    else:
                        embed.add_field(
                            name="📊 Statistiques",
                            value="Aucun vote pour le moment",
                            inline=False
                        )
                    
                    embed.set_footer(text=f"Total: {total_votes} votes • Mis à jour automatiquement")
                    
                    await message.edit(embed=embed)
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la mise à jour du message de sondage {message_data}: {e}")
                    
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour automatique des sondages: {e}")

async def send_poll_to_guilds(bot, question: str, options: List[str], poll_id: str, results_channel_id: int):
    """Envoie un sondage à tous les serveurs"""
    sent_count = 0
    failed_count = 0
    
    for guild in bot.guilds:
        try:
            announce_channel_id = await get_announce_channel(guild.id)
            if not announce_channel_id:
                failed_count += 1
                continue
                
            channel = guild.get_channel(announce_channel_id)
            if not channel:
                failed_count += 1
                continue
                
            embed = discord.Embed(
                title="📊 Nouveau sondage",
                description=question,
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
            embed.add_field(
                name="Options disponibles",
                value=options_text,
                inline=False
            )
            
            embed.add_field(
                name="📊 Statistiques",
                value="Aucun vote pour le moment",
                inline=False
            )
            
            embed.set_footer(text=f"ID: {poll_id} • Cliquez sur les boutons pour voter")
            
            view = PollView(poll_id, question, options, results_channel_id)
            message = await channel.send(embed=embed, view=view)
            
            # Stocker les informations du message pour les mises à jour
            if poll_id not in active_poll_messages:
                active_poll_messages[poll_id] = []
                
            active_poll_messages[poll_id].append({
                'guild_id': guild.id,
                'channel_id': channel.id,
                'message_id': message.id,
                'question': question
            })
            
            sent_count += 1
            logger.info(f"Sondage {poll_id} envoyé sur {guild.name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du sondage sur {guild.name}: {e}")
            failed_count += 1
    
    return sent_count, failed_count

class PollModal(discord.ui.Modal, title="Créer un sondage"):
    
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
        self.question = discord.ui.TextInput(
            label="Question du sondage",
            style=discord.TextStyle.short,
            placeholder="Posez votre question ici...",
            required=True,
            max_length=200
        )
        self.add_item(self.question)
        
        self.options = discord.ui.TextInput(
            label="Options (une par ligne, 2-10 options)",
            style=discord.TextStyle.paragraph,
            placeholder="Option 1\nOption 2\nOption 3\n...",
            required=True,
            max_length=1000
        )
        self.add_item(self.options)
    
    async def on_submit(self, interaction: discord.Interaction):
        question = self.question.value.strip()
        options_text = self.options.value.strip()
        
        options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
        
        if len(options) < 2:
            await interaction.response.send_message(
                "❌ Vous devez fournir au moins 2 options pour le sondage.",
                ephemeral=True
            )
            return
        
        if len(options) > 10:
            await interaction.response.send_message(
                "❌ Vous ne pouvez pas avoir plus de 10 options dans un sondage.",
                ephemeral=True
            )
            return
        
        poll_id = f"poll_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            embed = discord.Embed(
                title="🔍 Aperçu du sondage à envoyer",
                description=f"**Question :** {question}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
            embed.add_field(
                name="Options proposées",
                value=options_text,
                inline=False
            )
            
            embed.add_field(
                name="📊 Informations",
                value=f"• **Serveurs cibles :** {len(self.bot.guilds)}\n"
                      f"• **ID du sondage :** `{poll_id}`\n"
                      f"• **Boutons :** {len(options)} options + résultats",
                inline=False
            )
            
            embed.set_footer(text="⚠️ Une fois envoyé, le sondage ne peut plus être modifié")
            
            view = PollConfirmationView(question, options, poll_id, len(self.bot.guilds))
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du sondage: {e}")
            await interaction.response.send_message(
                f"❌ Erreur lors de la création du sondage: {str(e)}",
                ephemeral=True
            )

async def setup_persistent_poll_views(bot):
    """Restaure les vues de sondage au démarrage du bot"""
    polls_dir = "polls"
    if not os.path.exists(polls_dir):
        return
    
    for filename in os.listdir(polls_dir):
        if not filename.endswith('.json') or filename.endswith('_results.json') or filename.endswith('_export.json'):
            continue
            
        try:
            file_path = os.path.join(polls_dir, filename)
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
            
            poll_id = data.get('poll_id')
            question = data.get('question')
            options = data.get('options', [])
            results_channel_id = data.get('results_channel_id', 0)
            
            if poll_id and question and options:
                view = PollView(poll_id, question, options, results_channel_id)
                bot.add_view(view)
                logger.info(f"Vue de sondage restaurée pour {poll_id}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la restauration de la vue de sondage pour {filename}: {e}")

@update_poll_messages.before_loop
async def before_update_poll_messages():
    await main_bot.wait_until_ready()

async def on_close():
    """Nettoyage avant fermeture"""
    if update_poll_messages.is_running():
        update_poll_messages.cancel()

async def setup(bot: discord.Client):
    """Configuration initiale du module de sondages"""
    await setup_persistent_poll_views(bot)
    
    # Démarrer la tâche de mise à jour automatique
    if not update_poll_messages.is_running():
        update_poll_messages.start()
    
    @bot.tree.command(name="poll", description="Crée et envoie un sondage sur tous les serveurs")
    async def poll_command(interaction: discord.Interaction):
        if not is_dev_id(interaction.user.id):
            logger.warning(f"Refus d'accès pour {interaction.user} (ID: {interaction.user.id})")
            await interaction.response.send_message(
                "Vous n'avez pas la permission d'utiliser cette commande.", 
                ephemeral=True
            )
            return
        
        logger.info(f"Commande /poll exécutée par {interaction.user.display_name}")
        
        modal = PollModal(bot)
        await interaction.response.send_modal(modal)
