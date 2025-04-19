import discord
from discord import app_commands
import logging
from dotenv import load_dotenv
from utils.langs import get_language, get_translation as tlt
import os

load_dotenv()
logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="guild-info", description="Affiche les infos complètes du serveur")
    async def guild_info(interaction: discord.Interaction, guild: str = ""):
        try:
            target_guild = await get_guild(bot, interaction, guild)

            if not target_guild:
                user_lang = get_language(interaction.user.id)
                await interaction.response.send_message(tlt(language=user_lang, key="guild_not_found"), ephemeral=True)
                return

            created_at = int(target_guild.created_at.timestamp())

            logger.info(f"Commande guild-info exécutée par {interaction.user.display_name}")
            await interaction.response.defer()

            user_lang = get_language(interaction.user.id)

            embed = discord.Embed(
                title=tlt(language=user_lang, key="guild_info_title", guild_name=target_guild.name),
                color = discord.Color.default(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=tlt(language=user_lang, key="embed_footer", user=interaction.user.display_name), icon_url=interaction.user.display_avatar.url)

            info_general = ""
            info_general += tlt(language=user_lang, key="id", id=target_guild.id) + "\n"
            info_general += tlt(language=user_lang, key="owner", owner=target_guild.owner_id) + "\n"
            info_general += tlt(language=user_lang, key="joined_at", joined_at=f"<t:{int(target_guild.me.joined_at.timestamp())}:F>\n")
            info_general += tlt(language=user_lang, key="created_at", created_at=f"<t:{created_at}:F>\n")
            info_general += tlt(language=user_lang, key="verification", verification=str(target_guild.verification_level).capitalize())

            embed.add_field(name=tlt(language=user_lang, key="general_info_field"), value=info_general, inline=False)

            if target_guild.icon:
                icon_url = target_guild.icon.url
                icon_128 = icon_url.replace("?size=1024", "?size=128") if "?size=" in icon_url else f"{icon_url}?size=128"
                icon_256 = icon_url.replace("?size=1024", "?size=256") if "?size=" in icon_url else f"{icon_url}?size=256"
                icon_512 = icon_url.replace("?size=1024", "?size=512") if "?size=" in icon_url else f"{icon_url}?size=512"
                icon_1024 = icon_url if "?size=" in icon_url else f"{icon_url}?size=1024"
                embed.add_field(
                    name=tlt(language=user_lang, key="icon"),
                    value=f"[128px]({icon_128}) | [256px]({icon_256}) | [512px]({icon_512}) | [1024px]({icon_1024})",
                    inline=True
                )
                embed.set_thumbnail(url=icon_1024)
            else:
                embed.add_field(name=tlt(language=user_lang, key="icon"), value=tlt(language=user_lang, key="none"), inline=False)

            bots_count = 0
            humans_count = 0
            async for member in target_guild.fetch_members(limit=None):
                if member.bot:
                    bots_count += 1
                else:
                    humans_count += 1

            members_info = ""
            members_info += tlt(language=user_lang, key="members", members=str(target_guild.member_count)) + "\n"
            members_info += tlt(language=user_lang, key="humans", humans=str(humans_count))  + "\n"
            members_info += tlt(language=user_lang, key="bots", bots=str(bots_count))
            embed.add_field(name=tlt(language=user_lang, key="members_field"), value=members_info, inline=False)

            channels_info = ""
            channels_info += tlt(language=user_lang, key="channels_count", channels_count=str(len(target_guild.channels))) + "\n"
            channels_info += tlt(language=user_lang, key="text_channels", text_channels=str(len(target_guild.text_channels))) + "\n"
            channels_info += tlt(language=user_lang, key="voice_channels", voice_channels=str(len(target_guild.voice_channels))) + "\n"
            channels_info += tlt(language=user_lang, key="forums_channels", forums_channels=str(len(target_guild.forums))) + "\n"
            channels_info += tlt(language=user_lang, key="stage_channels", stage_channels=str(len(target_guild.stage_channels)))
            embed.add_field(name=tlt(language=user_lang, key="channels_field"), value=channels_info, inline=False)

            roles_info = ""
            roles_info += tlt(language=user_lang, key="roles_count", roles_count=str(len(target_guild.roles)))
            embed.add_field(name=tlt(language=user_lang, key="roles_field"), value=roles_info, inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            user_lang = get_language(interaction.user.id)
            logger.error(f"Erreur lors de l'exécution de guild-info : {str(e)}")
            await interaction.followup.send(tlt(language=user_lang, key="other_exception", e=str(e)))

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
