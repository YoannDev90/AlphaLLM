class PermissionChecker:
    """
    Classe pour vérifier si le bot est autorisé à répondre à un message Discord.
    Règles simplifiées : MP toujours autorisé sauf blacklist, serveur seulement si mentionné et conditions remplies.
    """

    def __init__(self, blacklist=None, allowed_channels=None):
        """
        Initialise le vérificateur de permissions.

        :param blacklist: Liste des IDs d'utilisateurs blacklistés.
        :param allowed_channels: Liste des IDs de canaux autorisés (par défaut tous si vide).
        """
        self.blacklist = set(blacklist or [])
        self.allowed_channels = set(allowed_channels or [])

    def is_authorized(self, message):
        """
        Vérifie si le bot est autorisé à répondre au message.

        :param message: Objet Message de Discord.
        :return: Tuple (bool, str) - True si autorisé, False sinon, avec une raison.
        """
        # Vérification de blacklist
        if message.author.id in self.blacklist:
            return False, "Utilisateur blacklisté"

        # Si c'est un message privé (DM)
        if message.guild is None:
            return True, "Autorisé en MP"

        # Dans un serveur : vérifications supplémentaires
        # Vérification si le bot est mentionné
        if message.guild.me not in message.mentions:
            return False, "Bot non mentionné"

        # Vérification si @everyone ou @here ou rôle mentionné
        if message.mention_everyone or message.role_mentions:
            return False, "Mention @everyone, @here ou rôle non autorisée"

        # Vérification des canaux autorisés (si configuré)
        if self.allowed_channels and message.channel.id not in self.allowed_channels:
            return False, "Canal non autorisé"

        return True, "Autorisé"

    def add_to_blacklist(self, user_id):
        """Ajoute un utilisateur à la blacklist."""
        self.blacklist.add(user_id)

    def remove_from_blacklist(self, user_id):
        """Retire un utilisateur de la blacklist."""
        self.blacklist.discard(user_id)

    def add_allowed_channel(self, channel_id):
        """Ajoute un canal autorisé."""
        self.allowed_channels.add(channel_id)

    def remove_allowed_channel(self, channel_id):
        """Retire un canal autorisé."""
        self.allowed_channels.discard(channel_id)