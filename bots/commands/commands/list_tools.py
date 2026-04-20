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

        embeds = []
        current_embed = discord.Embed(
            title="🛠️ AI Available Tools",
            description="Here are the tools I can use to help you manage the server and create content.",
            color=discord.Color.blue()
        )
        
        tools_found = 0
        field_count = 0
        
        # Sort files to have a consistent order
        filenames = sorted([f for f in os.listdir(tools_path) if f.endswith(".json")])
        
        for filename in filenames:
            try:
                with open(tools_path / filename, "r", encoding="utf-8") as f:
                    tool_data = json.load(f)
                
                name = tool_data.get("name", filename[:-5])
                description = tool_data.get("description", "No description provided.")
                params = tool_data.get("parameters", {}).get("properties", {})
                
                if params:
                    param_list = ", ".join([f"`{p}`" for p in params.keys()])
                    value = f"{description}\n**Parameters:** {param_list}"
                else:
                    value = description

                # Discord limit: 25 fields per embed
                if field_count >= 25:
                    embeds.append(current_embed)
                    current_embed = discord.Embed(
                        title="🛠️ AI Available Tools (continued)",
                        color=discord.Color.blue()
                    )
                    field_count = 0

                current_embed.add_field(
                    name=f"🔹 {name}",
                    value=value,
                    inline=False
                )
                tools_found += 1
                field_count += 1
            except Exception as e:
                logger.error(f"Error loading tool file {filename}: {e}")

        if tools_found == 0:
            await interaction.response.send_message("📭 No tools found in the configuration.", ephemeral=True)
            return

        embeds.append(current_embed)
        
        # Add footer to the last embed
        embeds[-1].set_footer(text=f"Total: {tools_found} tools | Use @AlphaLLM to trigger them naturally.")
        
        # Send the first embed as response, others as follow-up
        await interaction.response.send_message(embed=embeds[0])
        for i in range(1, len(embeds)):
            await interaction.followup.send(embed=embeds[i])

async def setup(bot):
    await bot.add_cog(ListTools(bot))