import discord
from discord.ext import commands
import json
import logging
from typing import Union
import os
from supabase import create_client, Client, ClientOptions

logger = logging.getLogger("AlphaLLM")

# Structure de validation des paramètres
SETTINGS_CONFIG = {
    "lang": {"type": str, "allowed": ["fr", "en", "es", "de"]},
    "def_model": {"type": str},
    "fallback": {"type": bool, "aliases": ["true", "false", "on", "off"]},
    "fallback_model": {"type": str},
    "image_gen": {"type": bool},
    "image_model": {"type": str},
    "image_size": {"type": json.loads, "example": '{"w": 1024, "h": 768}'},
    "image_private": {"type": bool},
    "image_enhance": {"type": bool},
    "audio_gen": {"type": bool},
    "audio_voice": {"type": str},
    "audio_fallback": {"type": str},
    "announce_mp": {"type": bool},
}

async def setup(bot: commands.Bot):

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
    @bot.group(name="settings", aliases=["set"])
    async def settings_group(ctx: commands.Context):
        """Gestion des paramètres utilisateur"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help("settings")

    # Génération automatique des sous-commandes
    for param, config in SETTINGS_CONFIG.items():
        @settings_group.command(name=param)
        async def settings_command(ctx: commands.Context, *, value: str):
            param_name = ctx.command.name
            config = SETTINGS_CONFIG[param_name]
            
            # Conversion et validation
            try:
                if config["type"] == bool:
                    converted = value.lower() in ["true", "on", "yes", "1"]
                else:
                    converted = config["type"](value)
            except Exception as e:
                example = config.get("example", "")
                await ctx.send(f"Format invalide pour `{param_name}`. Exemple : `{example}`")
                return

            # Validation des valeurs autorisées
            if "allowed" in config and converted not in config["allowed"]:
                allowed = ", ".join(config["allowed"])
                await ctx.send(f"Valeurs autorisées pour `{param_name}` : {allowed}")
                return

            # Mise à jour Supabase
            try:
                user_id = ctx.author.id
                supabase_client.table("user_settings").upsert(
                    {"id_discord": user_id, param_name: converted}
                ).execute()
                
                await ctx.send(f"Paramètre `{param_name}` mis à jour avec succès!")
                
            except Exception as e:
                logger.error(f"Erreur mise à jour {param_name} : {str(e)}")
                await ctx.send("Erreur lors de la mise à jour du paramètre")

    # Commande pour afficher tous les paramètres
    @settings_group.command(name="show")
    async def show_settings(ctx: commands.Context):
        try:
            user_id = ctx.author.id
            response = supabase_client.table("user_settings").select("*").eq("id_discord", user_id).execute()
            
            if not response.data:
                await ctx.send("Aucun paramètre configuré")
                return
                
            settings = response.data[0]
            embed = discord.Embed(title="🔧 Vos paramètres", color=0x00ff00)
            
            for param in SETTINGS_CONFIG:
                value = settings.get(param, "Non défini")
                embed.add_field(name=param.upper(), value=f"`{value}`", inline=False)
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erreur affichage paramètres : {str(e)}")
            await ctx.send("Erreur lors de la récupération des paramètres")
