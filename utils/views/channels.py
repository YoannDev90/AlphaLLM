import logging

import discord
from discord import ChannelType, Interaction
from discord.ui import Select, View, Button

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

class ChannelSelect(Select):
    def __init__(self, options_part):
        super().__init__(
            placeholder="Sélectionnez des salons où le bot peut interagir",
            min_values=0,
            max_values=len(options_part),
            options=options_part
        )

    async def callback(self, interaction: Interaction):
        selected = [interaction.guild.get_channel(int(cid)) for cid in self.values]
        self.view.selected_channels.extend(selected)
        await interaction.response.send_message(
            f"Salons sélectionnés : {', '.join([c.name for c in selected])}",
            ephemeral=True
        )

class DoneButton(Button):
    def __init__(self):
        super().__init__(label="Terminé", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message("Sélection terminée.", ephemeral=True)
        self.view.stop()

class ChannelSelectView(View):
    def __init__(self, guild):
        super().__init__(timeout=300)
        self.selected_channels = []
        options = [
            discord.SelectOption(label=channel.name, value=str(channel.id))
            for channel in guild.channels if channel.type == ChannelType.text
        ]
        for i in range(0, len(options), 25):
            part = options[i:i + 25]
            self.add_item(ChannelSelect(part))
        self.add_item(DoneButton())
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True