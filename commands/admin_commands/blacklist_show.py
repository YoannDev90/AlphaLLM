import discord
import logging
from supabase import create_client, Client, ClientOptions
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

logger = logging.getLogger('AlphaLLM')
OWNER_ID = int(os.getenv('DEV_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))


async def setup(bot: discord.Client):
    @bot.tree.command(name="blacklist-show", description="Affiche la liste des utilisateurs blacklistés")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def blacklist_show(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /blacklist-show exécutée par {interaction.user.display_name}")

        if interaction.user.id != OWNER_ID:
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

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
            
            response = supabase_client.table("blacklist").select("*").execute()
            blacklisted_users = response.data

            if not blacklisted_users:
                await interaction.followup.send("Aucun utilisateur n'est actuellement blacklisté.", ephemeral=True)
                return

            embed = discord.Embed(
                title="📋 Liste des utilisateurs blacklistés",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Total: {len(blacklisted_users)} utilisateur(s)")

            for user_data in blacklisted_users:
                user_id = user_data["id_discord"]
                reason = user_data["reason"]
                ban_date = user_data["datetime"]
                
                try:
                    date_obj = datetime.fromisoformat(ban_date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime("%d/%m/%Y à %H:%M")
                except:
                    formatted_date = ban_date

                try:
                    user = await bot.fetch_user(user_id)
                    username = user.global_name if user.global_name else user.name
                except:
                    username = f"Utilisateur (ID: {user_id})"

                field_value = f"**Raison:** {reason}\n**Date:** {formatted_date}\n```\n{user_id}\n```"
                embed.add_field(
                    name=f"👤 {username}",
                    value=field_value,
                    inline=False
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la blacklist : {str(e)}")
            await interaction.followup.send("Erreur interne : Impossible de récupérer la liste des utilisateurs blacklistés.", ephemeral=True)
            return