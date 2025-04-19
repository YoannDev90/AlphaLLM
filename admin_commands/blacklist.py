import discord
import logging
from supabase import create_client, Client, ClientOptions
import os
from datetime import datetime

logger = logging.getLogger('AlphaLLM')
OWNER_ID = int(os.getenv('DEV_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))


async def setup(bot: discord.Client):
    @bot.tree.command(name="blacklist", description="Ajoute un utilisateur à la blacklist")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def blacklist(interaction: discord.Interaction, user_id: str, reason: str = "Aucune raison fournie"):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /blacklist exécutée par {interaction.user.display_name}")

        if interaction.user.id != OWNER_ID:
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        if not user_id.isdigit() or int(user_id) <= 0:
            await interaction.followup.send("L'ID utilisateur fourni est invalide.", ephemeral=True)
            return

        try:
            data = {
                "id_discord": int(user_id),
                "reason": reason,
                "datetime": datetime.now().isoformat()
            }

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
            supabase_client.table("blacklist").insert(data).execute()
        except Exception as e:
            logger.error(f"Erreur lors de l'interaction avec Supabase : {str(e)}")
            await interaction.followup.send("Erreur interne : Impossible d'ajouter l'utilisateur à la liste noire.", ephemeral=True)
            return

        await interaction.followup.send(f"L'utilisateur avec l'ID `{user_id}` a été ajouté à la liste noire pour la raison : `{reason}`.", ephemeral=True)