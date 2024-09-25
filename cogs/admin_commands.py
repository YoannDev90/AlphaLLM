import discord
from discord import app_commands
from discord.ext import commands
import datetime
import asyncio

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blacklisted_users = {}
        self.bot_paused = False
        self.pause_end_time = None

    @app_commands.command(name="reset", description="Réinitialise le bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_bot(self, interaction: discord.Interaction):
        await interaction.response.send_message("Réinitialisation du bot en cours...")
        # Ajoutez ici la logique de réinitialisation

    @app_commands.command(name="break", description="Met le bot en pause")
    @app_commands.checks.has_permissions(administrator=True)
    async def pause_bot(self, interaction: discord.Interaction, duration: str):
        try:
            minutes, seconds = map(int, duration.split(':'))
            total_seconds = minutes * 60 + seconds
            if total_seconds > 1800:  # 30 minutes max
                await interaction.response.send_message("La durée maximale de pause est de 30 minutes.")
                return
            self.bot_paused = True
            self.pause_end_time = datetime.datetime.now() + datetime.timedelta(seconds=total_seconds)
            await interaction.response.send_message(f"Le bot est mis en pause pour {duration}.")
            await asyncio.sleep(total_seconds)
            self.bot_paused = False
            self.pause_end_time = None
            await interaction.followup.send("La pause est terminée. Le bot est de nouveau actif.")
        except ValueError:
            await interaction.response.send_message("Format de durée invalide. Utilisez mm:ss.")

    @app_commands.command(name="blacklist", description="Blackliste un utilisateur")
    @app_commands.checks.has_permissions(administrator=True)
    async def blacklist_user(self, interaction: discord.Interaction, user: discord.User, duration: str = None):
        if duration:
            try:
                days, hours, minutes, seconds = map(int, duration.split(':'))
                end_time = datetime.datetime.now() + datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            except ValueError:
                await interaction.response.send_message("Format de durée invalide. Utilisez jj:hh:mm:ss.")
                return
        else:
            end_time = None

        self.blacklisted_users[str(user.id)] = end_time
        await interaction.response.send_message(f"Utilisateur {user.mention} blacklisté" + (f" pour {duration}" if duration else " indéfiniment") + ".")

    @app_commands.command(name="whitelist", description="Retire un utilisateur de la blacklist")
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist_user(self, interaction: discord.Interaction, user: discord.User):
        user_id = str(user.id)
        if user_id in self.blacklisted_users:
            del self.blacklisted_users[user_id]
            await interaction.response.send_message(f"Utilisateur {user.mention} retiré de la blacklist.")
        else:
            await interaction.response.send_message(f"L'utilisateur {user.mention} n'est pas dans la blacklist.")

    @app_commands.command(name="kill", description="Arrête le serveur")
    @app_commands.checks.has_permissions(administrator=True)
    async def kill_server(self, interaction: discord.Interaction):
        await interaction.response.send_message("Arrêt du serveur en cours...")
        await self.bot.close()

    @app_commands.command(name="stop", description="Arrête le bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def stop_bot(self, interaction: discord.Interaction):
        await interaction.response.send_message("Arrêt du bot en cours...")
        await self.bot.close()
