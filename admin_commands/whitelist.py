import discord
from discord.ext import commands
from supabase import create_client, Client, ClientOptions
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

load_dotenv()

logger = logging.getLogger('AlphaLLM')
OWNER_ID = int(os.getenv('DEV_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))

async def setup(bot: commands.Bot):
    @bot.tree.command(name="whitelist", description="Retire un utilisateur de la blacklist")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def whitelist(interaction: discord.Interaction, user_id: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /whitelist exécutée par {interaction.user.display_name}")

        if interaction.user.id != OWNER_ID:
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        if not user_id.isdigit() or int(user_id) <= 0:
            await interaction.followup.send("L'ID utilisateur fourni est invalide.", ephemeral=True)
            return
        
        user_id = int(user_id)

        try:
            url = os.environ.get("DB_URL")
            key = os.environ.get("DB_KEY")
            jwt = os.environ.get("JWT_KEY")
            supabase_client: Client = create_client(url, key, 
                                options=ClientOptions(
                                    schema="public",
                                    headers={"Authorization": f"Bearer {jwt}"},
                                    auto_refresh_token=True,
                                    persist_session=True
                                ))
            supabase_client.table("blacklist").delete().eq("id_discord", user_id).execute()
        except Exception as e:
            logger.error(f"Erreur lors de l'interaction avec Supabase : {str(e)}")
            await interaction.followup.send("Erreur interne : Impossible de retirer l'utilisateur de la liste noire.", ephemeral=True)
            return

        await interaction.followup.send(f"L'utilisateur avec l'ID `{user_id}` a été retiré de la liste noire.", ephemeral=True)