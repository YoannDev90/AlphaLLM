#utils/models_buttons.py

import discord
from utils.roles_utils import save_role_to_db, get_role_from_db, create_role, assign_role_to_bot, remove_role_from_bot, delete_role
import json
from utils.langs import get_translation

with open("config/models.json", "r") as f:
    MODELS = json.load(f)

class ModelButton(discord.ui.Button):
    def __init__(self, bot, model, guild):
        super().__init__(label=model["role_name"])
        self.model = model
        self.bot = bot
        self.guild = guild
        self.update_button_status()

    def update_button_status(self):
        role_id = get_role_from_db(self.guild.id, self.model["name"])
        if role_id:
            role = discord.utils.get(self.guild.roles, id=role_id[0])
            if role and role in self.guild.me.roles:
                self.style = discord.ButtonStyle.danger
            else:
                self.style = discord.ButtonStyle.blurple
        else:
            self.style = discord.ButtonStyle.success

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            role_id = get_role_from_db(self.guild.id, self.model["name"])
            if role_id:
                role = discord.utils.get(self.guild.roles, id=role_id[0])
                if role and role in interaction.guild.me.roles:
                    await remove_role_from_bot(interaction.guild.me, role)
                    await delete_role(role)
                    await interaction.followup.send(f"Le rôle {role.name} a été supprimé avec succès.", ephemeral=True)
                else:
                    await assign_role_to_bot(interaction.guild.me, role)
                    await interaction.followup.send(f"Le rôle {role.name} a été attribué avec succès.", ephemeral=True)
            else:
                role = await create_role(interaction.guild, self.model["role_name"])
                await assign_role_to_bot(interaction.guild.me, role)
                save_role_to_db(interaction.guild.id, self.model["name"], role.id)
                await interaction.followup.send(f"Le rôle {role.name} a été créé et attribué avec succès.", ephemeral=True)
            view = discord.ui.View()
            for index, model in enumerate(MODELS):
                row = index // 5
                view.add_item(ModelButton(self.bot, model, interaction.guild))
            await interaction.edit_original_response(view=view)
        except Exception as e:
            print(f"Erreur lors du traitement du bouton : {e}")
            await interaction.followup.send(f"Erreur lors du traitement du bouton : {e}", ephemeral=True)
