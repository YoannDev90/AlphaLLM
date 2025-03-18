import discord
from discord import app_commands
import logging
from dotenv import load_dotenv
from utils.langs import get_translation
import os

load_dotenv()
lang = "fr" #à corriger, doit récupérer la langue de l'utilisateur
logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="guild-info", description="Affiche les infos complètes du serveur")
    async def guild_info(interaction: discord.Interaction, guild: str = ""):
        if not str(interaction.user.id) == os.getenv("DEV_ID"):
            await interaction.response.send_message(get_translation(language=lang, key="admin_command_not_authorized"), ephemeral=True)
            return
        try:
            target_guild = await get_guild(bot, interaction, guild)

            if not target_guild:
                await interaction.response.send_message(get_translation(language=lang, key="guild_not_found"), ephemeral=True)
                return

            created_at = int(target_guild.created_at.timestamp())

            logger.info(f"Commande guild-info exécutée par {interaction.user.display_name}")
            await interaction.response.defer()

            embed = discord.Embed(
                title=get_translation(language=lang, key="guild_info_title", guild_name=target_guild.name),
                color = discord.Color.default(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=get_translation(language=lang, key="embed_footer", user=interaction.user.display_name), icon_url=interaction.user.display_avatar.url)

            info_general = ""
            info_general += get_translation(language=lang, key="id", guild_id=target_guild.id)
            info_general += get_translation(language=lang, key="owner", owner=target_guild.owner_id)
            info_general += get_translation(language=lang, key="joined_at", joined_at=target_guild.me.joined_at.timestamp()) if target_guild.me else get_translation(language=lang, key="joined_at", joined_at=get_translation(language=lang, key="unknown"))
            info_general += get_translation(language=lang, key="created_at", created_at=created_at)
            info_general += get_translation(language=lang, key="verification", verification=str(target_guild.verification_level).capitalize())

            embed.add_field(name=get_translation(language=lang, key="general_info"), value=info_general, inline=False)

            if target_guild.icon:
                icon_url = target_guild.icon.url
                icon_128 = icon_url.replace("?size=1024", "?size=128") if "?size=" in icon_url else f"{icon_url}?size=128"
                icon_256 = icon_url.replace("?size=1024", "?size=256") if "?size=" in icon_url else f"{icon_url}?size=256"
                icon_512 = icon_url.replace("?size=1024", "?size=512") if "?size=" in icon_url else f"{icon_url}?size=512"
                icon_1024 = icon_url if "?size=" in icon_url else f"{icon_url}?size=1024"
                embed.add_field(
                    name=get_translation(language=lang, key="icon"),
                    value=f"[128px]({icon_128}) | [256px]({icon_256}) | [512px]({icon_512}) | [1024px]({icon_1024})",
                    inline=True
                )
                embed.set_thumbnail(url=icon_1024)
            else:
                embed.add_field(name=get_translation(language=lang, key="icon"), value=get_translation(language=lang, key="none"), inline=False)

            bots_count = 0
            humans_count = 0
            async for member in target_guild.fetch_members(limit=None):
                if member.bot:
                    bots_count += 1
                else:
                    humans_count += 1

            members_info = ""
            members_info += f"Membres : {str(target_guild.member_count)}"
            members_info += f"\nHumains : {str(humans_count)}"
            members_info += f"\nBots : {str(bots_count)}"
            embed.add_field(name="Membres", value=members_info, inline=False)

            channels_info = ""
            channels_info += f"Salons : {str(len(target_guild.channels))}"
            channels_info += f"\nSalons textuels : {str(len(target_guild.text_channels))}"
            channels_info += f"\nSalons vocaux : {str(len(target_guild.voice_channels))}"
            channels_info += f"\nSalons de forums : {str(len(target_guild.forums))}"
            channels_info += f"\nSalons de conférence : {str(len(target_guild.stage_channels))}"
            embed.add_field(name="Salons", value=channels_info, inline=False)

            roles_info = ""
            roles_info += f"Rôles : {str(len(target_guild.roles))}"
            embed.add_field(name="Rôles", value=roles_info, inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de guild-info : {str(e)}")
            await interaction.followup.send("Une erreur s'est produite lors de la récupération des informations du serveur.")

async def get_guild(bot, interaction: discord.Interaction, guild_param: str):
    if not guild_param:
        return interaction.guild

    try:
        guild_id = int(guild_param)
        guild = bot.get_guild(guild_id)
        if guild:
            return guild
        else:
            try:
                guild = await bot.fetch_guild(guild_id)
                return guild
            except discord.HTTPException as e:
                logger.error(f"Erreur lors de la récupération du serveur {guild_id} : {str(e)}")
                return None
    except ValueError:
        pass

    for guild in bot.guilds:
        if guild.name.lower() == guild_param.lower():
            return guild

    logger.warning(f"Serveur {guild_param} non trouvé.")
    return None

