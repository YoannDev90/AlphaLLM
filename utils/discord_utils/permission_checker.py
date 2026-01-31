import logging

from config import LOGGER_NAME
from utils.database.perms_conf import (
    get_allowed_channels,
    get_allowed_roles,
    get_blacklist,
)

logger = logging.getLogger(LOGGER_NAME)


class PermissionChecker:
    async def is_authorized_msg(self, message) -> tuple[bool, str]:
        """
        Vérifie si le bot est autorisé à répondre au message.

        :param message: Objet Message ou Interaction de Discord.
        :return: Tuple (bool, str) - True si autorisé, False sinon, avec une raison.
        """
        # Déterminer l'utilisateur et le canal
        user = message.author if hasattr(message, "author") else message.user
        channel = message.channel
        guild = message.guild

        # Vérification de blacklist
        if user.id in await get_blacklist():
            return False, "Utilisateur blacklisté"

        # Si c'est un message privé (DM)
        if guild is None:
            return True, "Autorisé en MP"

        # Pour les interactions (slash commands), on suppose autorisé si canal autorisé
        if hasattr(message, "author"):  # C'est un Message
            # Vérification si le bot est mentionné
            if guild.me not in message.mentions:
                return False, "Bot non mentionné"

            # Vérification si @everyone ou @here ou rôle mentionné
            if message.mention_everyone or message.role_mentions:
                return False, "Mention @everyone, @here ou rôle"

        # Vérification des canaux autorisés (si configuré)
        # if channel.id not in await get_allowed_channels(guild.id):
        #     return False, "Canal non autorisé"

        # Vérification des rôles autorisés (si configuré)
        # user_roles_ids = [role.id for role in user.roles]
        # if not any(role_id in user_roles_ids for role_id in await get_allowed_roles(guild.id)):
        #     return False, "Rôle non autorisé"

        return True, "Autorisé"

    async def is_authorized_int(self, interaction) -> tuple[bool, str]:
        """
        Vérifie si le bot est autorisé à répondre à l'interaction d'image.

        :param interaction: Objet Interaction de Discord.
        :return: Tuple (bool, str) - True si autorisé, False sinon, avec une raison.
        """
        user = interaction.user
        channel = interaction.channel
        guild = interaction.guild

        # Vérification de blacklist
        if user.id in await get_blacklist():
            return False, "Utilisateur blacklisté"

        # Si c'est un message privé (DM)
        if guild is None:
            return True, "Autorisé en MP"

        # Vérification des canaux autorisés (si configuré)
        # if channel.id not in await get_allowed_channels(guild.id):
        #     return False, "Canal non autorisé"

        # Vérification des rôles autorisés (si configuré)
        # user_roles_ids = [role.id for role in user.roles]
        # if not any(role_id in user_roles_ids for role_id in await get_allowed_roles(guild.id)):
        #     return False, "Rôle non autorisé"

        return True, "Autorisé"
