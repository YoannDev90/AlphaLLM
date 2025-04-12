import discord
from discord.ext import commands
from supabase import create_client, Client, ClientOptions
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

logger = logging.getLogger('AlphaLLM')

async def setup(bot: commands.Bot):
    @bot.command(name="bl", aliases=["blacklist"])
    @commands.is_owner()
    async def blacklist(ctx: commands.Context, user_id: int, *, reason: str = "Aucune raison fournie"):
        """
        Ajoute un utilisateur à la liste noire.
        """
        logger.info(f"Commande blacklist exécutée par {ctx.author.display_name} avec l'ID utilisateur : {user_id}")

        if not isinstance(user_id, int) or user_id <= 0:
            await ctx.send("L'ID utilisateur fourni est invalide.")
            return

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            logger.warning("Impossible de supprimer le message de commande. Vérifiez les permissions.")

        try:
            data = {
                "id_discord": user_id,
                "reason": reason,
                "datetime": datetime.now().isoformat()
            }

            url: str = os.environ.get("DB_URL")
            key: str = os.environ.get("DB_KEY")
            jwt: str = os.environ.get("JWT_KEY")
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
            await ctx.send("Erreur interne : Impossible d'ajouter l'utilisateur à la liste noire.")
            return

        await ctx.send(f"L'utilisateur avec l'ID `{user_id}` a été ajouté à la liste noire pour la raison : `{reason}`.")