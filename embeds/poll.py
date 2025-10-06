import discord
import json
import aiofiles
import logging
from typing import List, Dict
from datetime import datetime, timedelta
from utils.config import logger_name, TIMEOUT_POLL_VIEW

logger = logging.getLogger(logger_name)

# Variables globales pour les résultats (à importer depuis poll.py)
poll_results = {}

class PollView(discord.ui.View):
    
    def __init__(self, poll_id: str, question: str, options: List[str], results_channel_id: int):
        super().__init__(timeout=None)
        self.poll_id = poll_id
        self.question = question
        self.options = options
        self.results_channel_id = results_channel_id
        self.voters: Dict[int, str] = {}
        
        
        for i, option in enumerate(options):
            label = option[:80] if len(option) > 80 else option
            
            
            try:
                button = discord.ui.Button(
                    label=f"{i+1}. {label}",
                    style=discord.ButtonStyle.primary,
                    custom_id=f"poll_{poll_id}_option_{i}"
                )
                button.callback = self._create_vote_callback(i, option)
                self.add_item(button)
            except Exception as e:
                logger.error(f"Erreur lors de la création du bouton {i+1}: {e}")
                logger.error(f"Détails: label='{label}', custom_id='poll_{poll_id}_option_{i}'")
                raise
        
        try:
            results_button = discord.ui.Button(
                label="Voir les résultats",
                style=discord.ButtonStyle.secondary,
                custom_id=f"poll_{poll_id}_results"
            )
            results_button.callback = self._show_results_callback
            self.add_item(results_button)
        except Exception as e:
            logger.error(f"Erreur lors de la création du bouton résultats: {e}")
            raise
        
    
    def _create_vote_callback(self, option_index: int, option_text: str):
        async def vote_callback(interaction: discord.Interaction):
            try:
                await self._handle_vote(interaction, option_index, option_text)
            except Exception as e:
                logger.error(f"Erreur lors du traitement du vote: {e}")
                try:
                    await interaction.response.send_message(
                        f"Erreur lors de l'enregistrement du vote: {str(e)}", 
                        ephemeral=True
                    )
                except:
                    pass
        return vote_callback
    
    async def _handle_vote(self, interaction: discord.Interaction, option_index: int, option_text: str):
        
        try:
            user_id = interaction.user.id
            guild_id = str(interaction.guild.id)
            
            if self.poll_id not in poll_results:
                poll_results[self.poll_id] = {}
                
            if guild_id not in poll_results[self.poll_id]:
                poll_results[self.poll_id][guild_id] = {option: 0 for option in self.options}
            
            if user_id in self.voters:
                old_option = self.voters[user_id]
                poll_results[self.poll_id][guild_id][old_option] -= 1
            
            self.voters[user_id] = option_text
            poll_results[self.poll_id][guild_id][option_text] += 1
            
            await self._save_poll_results()
            
            embed = discord.Embed(
                title="Vote enregistré !",
                description=f"Vous avez voté pour : **{option_text}**",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self._update_poll_embed(interaction)
            
        except Exception as e:
            logger.error(f"Erreur détaillée lors du traitement du vote: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    async def _show_results_callback(self, interaction: discord.Interaction):
        
        try:
            guild_id = str(interaction.guild.id)
            
            if self.poll_id not in poll_results or guild_id not in poll_results[self.poll_id]:
                embed = discord.Embed(
                    title="Résultats du sondage",
                    description=f"**{self.question}**\n\nAucun vote n'a encore été enregistré sur ce serveur.",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            results = poll_results[self.poll_id][guild_id]
            total_votes = sum(results.values())
            
            embed = discord.Embed(
                title="Résultats du sondage",
                description=f"**{self.question}**",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Statistiques",
                value=f"**Total des votes :** {total_votes}",
                inline=False
            )
            
            if total_votes > 0:
                for option, count in results.items():
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
                    name="Information",
                    value="Aucun vote n'a encore été enregistré.",
                    inline=False
                )
            
            embed.set_footer(text=f"Serveur: {interaction.guild.name}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des résultats: {e}")
            await interaction.response.send_message(
                "Erreur lors de l'affichage des résultats.",
                ephemeral=True
            )
    
    async def _save_poll_results(self):
        """Sauvegarde les résultats du sondage dans un fichier JSON"""
        try:
            file_path = f"polls/{self.poll_id}_results.json"
            data = {
                "poll_id": self.poll_id,
                "question": self.question,
                "options": self.options,
                "results": poll_results.get(self.poll_id, {}),
                "last_updated": datetime.now().isoformat()
            }
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des résultats {self.poll_id}: {e}")
    
    async def _update_poll_embed(self, interaction: discord.Interaction):
        """Met à jour l'embed du sondage avec les nouveaux résultats"""
        try:
            pass  # Cette fonction sera implémentée selon les besoins
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'embed: {e}")


class ResultsCollectorView(discord.ui.View):    
    def __init__(self, poll_id: str, question: str, options: List[str], total_guilds: int):
        super().__init__(timeout=TIMEOUT_POLL_VIEW)
        self.poll_id = poll_id
        self.question = question
        self.options = options
        self.total_guilds = total_guilds
    
    @discord.ui.button(label="Actualiser les résultats", style=discord.ButtonStyle.primary)
    async def refresh_results(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        global_results = await self._calculate_global_results()
        total_votes = sum(global_results.values())
        
        # Import de la fonction pour créer le graphique
        try:
            from commands.admin_commands.poll import create_poll_chart
            chart_buffer = await create_poll_chart(self.question, self.options, global_results, total_votes)
        except ImportError:
            chart_buffer = None
        
        embed = await self._create_global_results_embed()
        
        if chart_buffer and total_votes > 0:
            file = discord.File(chart_buffer, filename=f"global_results_{self.poll_id}.png")
            embed.set_image(url=f"attachment://global_results_{self.poll_id}.png")
            await interaction.edit_original_response(embed=embed, view=self, attachments=[file])
        else:
            await interaction.edit_original_response(embed=embed, view=self, attachments=[])
    
    @discord.ui.button(label="Résultats détaillés", style=discord.ButtonStyle.secondary)
    async def detailed_results(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if self.poll_id not in poll_results:
            await interaction.followup.send("Aucun résultat disponible pour ce sondage.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Résultats détaillés par serveur",
            description=f"**{self.question}**",
            color=discord.Color.blue()
        )
        
        for guild_id, results in poll_results[self.poll_id].items():
            try:
                guild = interaction.client.get_guild(int(guild_id))
                guild_name = guild.name if guild else f"Serveur {guild_id}"
                total_votes = sum(results.values())
                
                if total_votes > 0:
                    results_text = "\n".join([
                        f"• {option}: {count} votes" 
                        for option, count in results.items() if count > 0
                    ])
                    embed.add_field(
                        name=f"{guild_name} ({total_votes} votes)",
                        value=results_text or "Aucun vote",
                        inline=True
                    )
            except Exception as e:
                logger.error(f"Erreur lors de l'affichage des résultats pour le serveur {guild_id}: {e}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Exporter résultats", style=discord.ButtonStyle.success)
    async def export_results(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            file_path = f"polls/{self.poll_id}_export.json"
            data = {
                "poll_id": self.poll_id,
                "question": self.question,
                "options": self.options,
                "results_by_guild": poll_results.get(self.poll_id, {}),
                "global_results": await self._calculate_global_results(),
                "export_time": datetime.now().isoformat(),
                "total_guilds": self.total_guilds
            }
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            
            with open(file_path, 'rb') as f:
                file = discord.File(f, filename=f"results.json")
                await interaction.followup.send(
                    f"**Résultats exportés avec succès !**\n"
                    f"Fichier : `{file_path}`",
                    file=file,
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Erreur lors de l'export des résultats: {e}")
            await interaction.followup.send(f"Erreur lors de l'export: {str(e)}", ephemeral=True)
    
    async def _create_global_results_embed(self):
        global_results = await self._calculate_global_results()
        total_votes = sum(global_results.values())
        participating_guilds = len([g for g in poll_results.get(self.poll_id, {}).values() if sum(g.values()) > 0])
        
        embed = discord.Embed(
            title="Résultats globaux du sondage",
            description=f"**{self.question}**",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Statistiques générales",
            value=f"• **Total des votes :** {total_votes}\n"
                  f"• **Serveurs participants :** {participating_guilds}/{self.total_guilds}\n"
                  f"• **Taux de participation :** {(participating_guilds/self.total_guilds*100):.1f}%",
            inline=False
        )

        embed.add_field(
            name="Actualisation",
            value=f"**Dernière mise à jour :** \n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n**Prochaine mise à jour :** \n{(datetime.now() + timedelta(minutes=5)).strftime('%d/%m/%Y %H:%M:%S')}",
            inline=False
        )
        
        if total_votes > 0:
            for option, count in global_results.items():
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
                name="Information",
                value="Aucun vote n'a encore été enregistré.",
                inline=False
            )

        return embed
    
    async def _calculate_global_results(self):
        """Calcule les résultats globaux en combinant tous les serveurs"""
        global_results = {option: 0 for option in self.options}
        
        if self.poll_id in poll_results:
            for guild_results in poll_results[self.poll_id].values():
                for option, count in guild_results.items():
                    if option in global_results:
                        global_results[option] += count
        
        return global_results


class PollConfirmationView(discord.ui.View):
    def __init__(self, question: str, options: List[str], poll_id: str, total_guilds: int):
        super().__init__(timeout=TIMEOUT_POLL_VIEW)
        self.question = question
        self.options = options
        self.poll_id = poll_id
        self.total_guilds = total_guilds

    @discord.ui.button(label="Confirmer l'envoi", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm_send(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        try:
            for item in self.children:
                item.disabled = True
            
            embed = discord.Embed(
                title="Envoi du sondage en cours...",
                description=f"Envoi sur {self.total_guilds} serveurs...",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            await interaction.edit_original_response(embed=embed, view=self)
            
            results_view = ResultsCollectorView(
                self.poll_id, self.question, self.options, self.total_guilds
            )
            
            # Import de la fonction pour envoyer le sondage
            try:
                from commands.admin_commands.poll import send_poll_to_guilds
                poll_guilds, failed_guilds = await send_poll_to_guilds(
                    interaction.client, self.question, self.options, self.poll_id, interaction.channel.id
                )
            except ImportError:
                poll_guilds = 0
                failed_guilds = self.total_guilds
            
            final_embed = await results_view._create_global_results_embed()
            final_embed.title = "Sondage envoyé avec succès !"
            final_embed.add_field(
                name="Statut d'envoi",
                value=f"• **{poll_guilds} serveurs** : sondage envoyé\n"
                      f"• **{failed_guilds} serveurs** : échecs\n"
                      f"• **ID du sondage** : `{self.poll_id}`",
                inline=False
            )
            
            await interaction.edit_original_response(embed=final_embed, view=results_view)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi confirmé du sondage: {e}")
            error_embed = discord.Embed(
                title="Erreur lors de l'envoi",
                description=f"Une erreur est survenue: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=error_embed, view=None)
    
    @discord.ui.button(label="Aperçu du sondage", style=discord.ButtonStyle.secondary)
    async def preview_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            embed = discord.Embed(
                title="Aperçu du sondage",
                description=f"**Question :** {self.question}",
                color=discord.Color.blue()
            )
            
            options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(self.options)])
            embed.add_field(
                name="Options disponibles",
                value=options_text,
                inline=False
            )
            
            embed.add_field(
                name="Informations",
                value=f"• **ID du sondage :** `{self.poll_id}`\n"
                      f"• **Serveurs cibles :** {self.total_guilds}\n"
                      f"• **Boutons :** {len(self.options)} options + résultats",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'aperçu du sondage: {e}")
            await interaction.followup.send(
                f"Erreur lors de l'affichage de l'aperçu: {str(e)}", 
                ephemeral=True
            )
    
    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.danger)
    async def cancel_send(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="Sondage annulé",
            description="L'envoi du sondage a été annulé.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="Informations",
            value=f"**ID du sondage :** `{self.poll_id}`\n"
                  f"**Question :** {self.question}",
            inline=False
        )
        
        await interaction.edit_original_response(embed=embed, view=None)
