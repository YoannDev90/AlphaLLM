from discord.ui import View, Select
from discord import Interaction, ChannelType
import discord
import logging
from utils.config import logger_name, TIMEOUT_CONFIG_VIEW

logger = logging.getLogger(logger_name)

class ChannelSelect(Select):
    def __init__(self, guild):
        options = [
            discord.SelectOption(label=channel.name, value=str(channel.id))
            for channel in guild.channels if channel.type == ChannelType.text
        ]
        super().__init__(
            placeholder="Select channels where the bot could interact",
            min_values=1,
            max_values=min(25, len(options)),
            options=options
        )

    async def callback(self, interaction: Interaction):
        selected_channels = [interaction.guild.get_channel(int(cid)) for cid in self.values]
        self.view.selected_channels = selected_channels
        await interaction.response.send_message(
            f"✅ Salons sélectionnés : {', '.join([c.name for c in selected_channels])}",
            ephemeral=True
        )
        self.view.stop()

class ChannelSelectView(View):
    def __init__(self, guild):
        super().__init__(timeout=TIMEOUT_CONFIG_VIEW)
        self.selected_channels = []
        self.add_item(ChannelSelect(guild))
        logger.info("ChannelSelectView initialized")
    
    async def on_timeout(self):
        logger.warning("ChannelSelectView timed out")
        for item in self.children:
            item.disabled = True


class RoleSelect(Select):
    def __init__(self, guild):
        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in guild.roles if role.name != "@everyone"
        ]
        super().__init__(
            placeholder="Select roles allowed to interact with the bot",
            min_values=1,
            max_values=min(25, len(options)),
            options=options
        )

    async def callback(self, interaction: Interaction):
        selected_roles = [interaction.guild.get_role(int(rid)) for rid in self.values]
        self.view.selected_roles = selected_roles
        await interaction.response.send_message(
            f"✅ Rôles sélectionnés : {', '.join([r.name for r in selected_roles])}",
            ephemeral=True
        )
        self.view.stop()

class RoleSelectView(View):
    def __init__(self, guild):
        super().__init__(timeout=TIMEOUT_CONFIG_VIEW)
        self.selected_roles = []
        self.add_item(RoleSelect(guild))
        logger.info("RoleSelectView initialized")
    
    async def on_timeout(self):
        logger.warning("RoleSelectView timed out")
        for item in self.children:
            item.disabled = True
