import discord
from discord import ui
import json
import logging
from typing import Dict, Any

logger = logging.getLogger('AlphaLLM')

class Configurator(ui.View):
    def __init__(self, config_schema: Dict[str, Any], interaction: discord.Interaction):
        super().__init__(timeout=300)
        self.config_schema = config_schema
        self.current_step = 0
        self.param_keys = list(config_schema.keys())
        self.config_data = self.load_current_config()
        self.interaction = interaction
        self.message = None

    def load_current_config(self) -> Dict[str, Any]:
        try:
            with open('config/config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    async def start(self):
        await self.show_step()
        self.message = await self.interaction.followup.send(view=self)

    async def show_step(self):
        current_param = self.param_keys[self.current_step]
        param_config = self.config_schema[current_param]
        self.clear_items()

        # Création des boutons selon le type de paramètre
        if 'available' in param_config:
            for value, label in param_config['available'].items():
                self.add_item(ConfigButton(label, value, current_param))
        
        elif 'filename' in param_config:
            with open(f"config/{param_config['filename']}") as f:
                models = json.load(f)
            for model_id, model_name in models.items():
                self.add_item(ConfigButton(model_name, model_id, current_param))
        
        elif param_config.get('type') == 'boolean':
            self.add_item(ConfigButton("✅ Activer", True, current_param))
            self.add_item(ConfigButton("❌ Désactiver", False, current_param))
        
        elif 'min' in param_config and 'max' in param_config:
            step = param_config.get('step', 5)
            for value in range(param_config['min'], param_config['max'] + 1, step):
                self.add_item(ConfigButton(str(value), value, current_param))

        # Mise à jour de l'embed
        embed = self.create_embed(current_param, param_config)
        if self.message:
            await self.message.edit(embed=embed, view=self)
        else:
            await self.interaction.followup.send(embed=embed, view=self)

    def create_embed(self, current_param: str, param_config: Dict[str, Any]) -> discord.Embed:
        embed = discord.Embed(
            title=f"Configuration du Bot ({self.current_step + 1}/{len(self.param_keys)})",
            color=0x00ff00
        )
        
        # Description étape actuelle
        embed.add_field(
            name=f"Paramètre actuel: {current_param}",
            value=param_config['description'],
            inline=False
        )
        
        # Valeur actuelle
        current_value = self.config_data.get(current_param, {}).get('default')
        if current_value:
            embed.add_field(
                name="Valeur actuelle",
                value=str(current_value),
                inline=False
            )
        
        # Aide à la configuration
        help_text = []
        if 'available' in param_config:
            help_text.append("**Options disponibles:**")
            help_text.extend([f"- {k}: {v}" for k, v in param_config['available'].items()])
        
        if 'min' in param_config and 'max' in param_config:
            help_text.append(f"\n**Plage valide:** {param_config['min']} à {param_config['max']}")
        
        if help_text:
            embed.add_field(name="Aide", value="\n".join(help_text), inline=False)

        return embed

    async def next_step(self):
        self.current_step += 1
        if self.current_step < len(self.param_keys):
            await self.show_step()
        else:
            await self.finalize()

    async def finalize(self):
        # Sauvegarde de la configuration
        with open('config/config.json', 'w') as f:
            json.dump(self.config_data, f, indent=4)
        
        # Embed final
        embed = discord.Embed(
            title="✅ Configuration terminée !",
            description="Tous les paramètres ont été configurés avec succès.",
            color=0x00ff00
        )
        
        # Liste des paramètres configurés
        for param, config in self.config_data.items():
            embed.add_field(
                name=param,
                value=f"`{config.get('default', 'Non défini')}`",
                inline=True
            )
        
        await self.message.edit(embed=embed, view=None)

class ConfigButton(ui.Button):
    def __init__(self, label: str, value: Any, param: str):
        super().__init__(label=label)
        self.value = value
        self.param = param

    async def callback(self, interaction: discord.Interaction):
        # Mise à jour de la configuration
        param_config = self.view.config_schema[self.param]
        
        # Validation des entrées
        if 'available' in param_config and self.value not in param_config['available']:
            return await interaction.response.send_message("Valeur invalide !", ephemeral=True)
        
        if 'min' in param_config and 'max' in param_config:
            if not (param_config['min'] <= self.value <= param_config['max']):
                return await interaction.response.send_message("Hors plage valide !", ephemeral=True)
        
        # Enregistrement de la valeur
        if self.param not in self.view.config_data:
            self.view.config_data[self.param] = {}
        
        self.view.config_data[self.param]['default'] = self.value
        await interaction.response.defer()
        await self.view.next_step()

async def setup(bot: discord.Client):
    @bot.tree.command(name="config", description="Configuration guidée complète du bot")
    async def config(interaction: discord.Interaction):
        print(f"Commande de configuration exécutée par {interaction.user.display_name}")
        
        # Chargement du schéma de configuration
        with open('config/config.json') as f:
            config_schema = json.load(f)
        print(config_schema)
        # Démarrage du configurateur
        await interaction.response.send_message("Chargement du configurateur...", ephemeral=True)
        view = Configurator(config_schema, interaction)
        await view.start()
