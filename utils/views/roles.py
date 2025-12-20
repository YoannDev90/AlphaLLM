import logging

import discord
from discord import ChannelType, Interaction
from discord.ui import Select, View, Button

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

class RoleSelect(Select):
    def __init__(self, options_part):
        super().__init__(
            placeholder="Sélectionnez des rôles autorisés à interagir avec le bot",
            min_values=0,
            max_values=len(options_part),
            options=options_part
        )

    async def callback(self, interaction: Interaction):
        selected = [interaction.guild.get_role(int(rid)) for rid in self.values]
        self.view.selected_roles.extend(selected)
        await interaction.response.send_message(
            f"Rôles sélectionnés : {', '.join([r.name for r in selected])}",
            ephemeral=True
        )

class DoneButton(Button):
    def __init__(self):
        super().__init__(label="Terminé", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message("Sélection terminée.", ephemeral=True)
        self.view.stop()

class RoleSelectView(View):
    def __init__(self, guild):
        super().__init__(timeout=300)
        self.selected_roles = []
        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in guild.roles if role.name != "@everyone"
        ]
        for i in range(0, len(options), 25):
            part = options[i:i + 25]
            self.add_item(RoleSelect(part))
        self.add_item(DoneButton())
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True