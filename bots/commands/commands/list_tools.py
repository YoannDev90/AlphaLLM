import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from pathlib import Path
import logging
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

class ListTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="list-tools", description="List all available AI tools and their descriptions")
    async def list_tools(self, interaction: discord.Interaction):
        tools_path = Path("configs/tools")
        if not tools_path.exists():
            await interaction.response.send_message("❌ Tools configuration directory not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🛠️ AI Available Tools",
            description="Here are the tools I can use to help you manage the server and create content.",
            color=discord.Color.blue()
        )

        tools_found = 0
        
        # Load all JSON files in configs/tools/
        for filename in os.listdir(tools_path):
            if filename.endswith(".json"):
                try:
                    with open(tools_path / filename, "r", encoding="utf-8") as f:
                        tool_data = json.load(f)
                    
                    name = tool_data.get("name", filename[:-5])
                    description = tool_data.get("description", "No description provided.")
                    
                    # Formatting parameters if they exist
                    params = tool_data.get("parameters", {}).get("properties", {})
                    if params:
                        param_list = ", ".join([f"`{p}`" for p in params.keys()])
                        value = f"{description}\n**Parameters:** {param_list}"
                    else:
                        value = description

                    embed.add_field(
                        name=f"🔹 {name}",
                        value=value,
                        inline=False
                    )
                    tools_found += 1
                except Exception as e:
                    logger.error(f"Error loading tool file {filename}: {e}")

        if tools_found == 0:
            await interaction.response.send_message("📭 No tools found in the configuration.", ephemeral=True)
            return

        embed.set_footer(text=f"Total: {tools_found} tools | Use @AlphaLLM to trigger them naturally.")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ListTools(bot))