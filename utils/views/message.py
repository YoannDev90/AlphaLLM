import csv
import io
import logging
from typing import List, Optional
from urllib.parse import urlparse

import discord
import pandas as pd

from config import LOGGER_NAME
from utils.unified_text import unified_text_gen

logger = logging.getLogger(LOGGER_NAME)


class TableActionView(discord.ui.View):
    def __init__(self, table_data: dict = None):
        super().__init__(timeout=None)  # Permanent view
        self.table_data = table_data or {}
        
        # Add dynamic link buttons if data is provided
        if self.table_data:
            seen_links = set()
            for link in self.table_data.get("links", []):
                # Ensure link is a valid absolute URL for Button URL
                try:
                    parsed = urlparse(link)
                    if not (parsed.scheme and parsed.netloc):
                        continue
                except Exception:
                    continue

                if link not in seen_links:
                    domain = parsed.netloc
                    if domain.startswith("www."): domain = domain[4:]
                    label = f"[{len(seen_links)+1}] {domain}"
                    # Maximum 5 items in a first row if we want to be safe, 
                    # but Discord allows up to 25 items in a View total (5 per ActionRow)
                    if len(seen_links) < 24: # Keep room for Download
                        self.add_item(discord.ui.Button(label=label, url=link, style=discord.ButtonStyle.link))
                        seen_links.add(link)

    @discord.ui.button(label="Download", emoji="📥", custom_id="table_download_btn", style=discord.ButtonStyle.success)
    async def download(self, interaction: discord.Interaction, button: discord.ui.Button):
        # On persistent views after reboot, self.table_data might be empty if we didn't save it.
        # But for the Download button to work, we need the raw data.
        if not self.table_data:
            return await interaction.response.send_message("❌ This table data is no longer available in memory. Please regenerate the response.", ephemeral=True)
        await interaction.response.send_modal(TableDownloadModal(self.table_data))


class TableDownloadModal(discord.ui.Modal):
    def __init__(self, table_data: dict):
        super().__init__(title="Download Table")
        self.table_data = table_data
        
        # Label with TextInput for Filename
        self.filename_label = discord.ui.Label(
            text="File Name",
            description="Enter the name for your export (without extension)",
            component=discord.ui.TextInput(
                placeholder="table",
                default="table",
                required=True
            )
        )
        self.add_item(self.filename_label)

        # Checkbox Group for Formats
        self.format_label = discord.ui.Label(
            text="Select Formats",
            description="Choose one or more formats to export",
            component=discord.ui.CheckboxGroup(
                options=[
                    discord.CheckboxGroupOption(label="CSV", value="csv", default=True),
                    discord.CheckboxGroupOption(label="Excel (XLSX)", value="xlsx"),
                    discord.CheckboxGroupOption(label="OpenDocument (ODS)", value="ods"),
                    discord.CheckboxGroupOption(label="JSON", value="json"),
                    discord.CheckboxGroupOption(label="HTML", value="html"),
                ],
                min_values=1,
                max_values=5
            )
        )
        self.add_item(self.format_label)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            import pandas as pd
            import io
            
            # Defer and confirm as ephemeral
            await interaction.response.defer(ephemeral=True)
            
            df = pd.DataFrame(self.table_data["rows"], columns=self.table_data["headers"])
            name = self.filename_label.component.value.strip()
            selected_formats = self.format_label.component.values
            
            files = []
            
            for fmt in selected_formats:
                output = io.BytesIO()
                
                if fmt == "csv":
                    df.to_csv(output, index=False)
                    ext = "csv"
                elif fmt == "ods":
                    df.to_excel(output, index=False, engine='odf')
                    ext = "ods"
                elif fmt == "xlsx":
                    df.to_excel(output, index=False, engine='xlsxwriter')
                    ext = "xlsx"
                elif fmt == "json":
                    json_str = df.to_json(orient="records", indent=4)
                    output.write(json_str.encode("utf-8"))
                    ext = "json"
                elif fmt == "html":
                    html_str = df.to_html(index=False)
                    output.write(html_str.encode("utf-8"))
                    ext = "html"
                else:
                    continue
                
                output.seek(0)
                files.append(discord.File(fp=output, filename=f"{name}.{ext}"))
            
            if files:
                await interaction.followup.send(f"✅ Here are your exports for table '{name}':", files=files, ephemeral=True)
            else:
                await interaction.followup.send("❌ No files generated.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error generating table files: {e}")
            await interaction.followup.send(f"❌ Error generating files: {e}", ephemeral=True)


class MessageView(discord.ui.View):
    def __init__(self, original_question, model, response_data=None, bot=None, table_data: List[dict] = None):
        super().__init__(timeout=300)
        self.original_question = original_question
        self.model = model
        self.responses = [response_data] if response_data else []
        self.current_index = 0
        self.bot = bot
        self.message = None
        self.regenerated = False
        self.table_data = table_data or []

    async def on_timeout(self):
        """Remove buttons when the view expires after 30 seconds"""
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass

    @discord.ui.button(emoji="🔄", label="Regenerate", style=discord.ButtonStyle.gray)
    async def regenerate(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.regenerated:
            await interaction.followup.send(
                "❌ Regeneration already done.", ephemeral=True
            )
            return
        logger.info(
            f"Response regeneration requested by {interaction.user.display_name}"
        )
        await interaction.response.defer()
        button.disabled = True
        self.regenerated = True
        await interaction.message.edit(view=self)
        try:
            results = [
                result
                async for result in unified_text_gen(
                    user_id=interaction.user.id,
                    conv_id=interaction.channel.id,
                    input=self.original_question,
                    model=self.model,
                    files=None,
                    message=interaction,
                    bot=self.bot,
                    use_memory=True,
                )
            ]
            if not results:
                await interaction.followup.send("❌ No response generated.")
                return
            result = results[0]
            self.responses.append(result)
            self.current_index = 1
            response_text = result.response
            # Enable and set switch button
            for child in self.children:
                if hasattr(child, "label") and "Switch" in child.label:
                    child.disabled = False
                    child.label = "View Original"
                    child.emoji = "⬅️"
            await interaction.message.edit(content=response_text, view=self)

        except Exception as e:
            logger.error(
                f"Error during response regeneration for {interaction.user.display_name}: {str(e)}"
            )
            await interaction.followup.send(
                "❌ Unexpected error during response regeneration."
            )

    @discord.ui.button(emoji="📊", label="Details", style=discord.ButtonStyle.gray)
    async def show_details(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        logger.debug(f"Details display requested by {interaction.user.display_name}")
        await interaction.response.defer()

        response_data = self.responses[self.current_index] if self.responses else None
        if not response_data:
            await interaction.followup.send(
                "❌ No detailed information available.", ephemeral=True
            )
            return

        try:
            embed = discord.Embed(title="📊 Response Details")
            embed.add_field(
                name="🤖 Model", value=f"`{response_data.model}`", inline=False
            )
            embed.add_field(
                name="🔢 Tokens Used", value=f"`{response_data.usage}`", inline=False
            )
            embed.add_field(
                name="⏱️ Response Time",
                value=f"`{response_data.elapsed_time}`",
                inline=False,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(
                f"Error creating details embed for {interaction.user.display_name}: {str(e)}"
            )

    @discord.ui.button(
        label="Switch Response",
        emoji="🔄",
        style=discord.ButtonStyle.gray,
        disabled=True,
    )
    async def switch_response(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if len(self.responses) < 2:
            await interaction.followup.send(
                "❌ No alternative response available.", ephemeral=True
            )
            return
        self.current_index = 1 - self.current_index
        response_text = self.responses[self.current_index].response
        if self.current_index == 0:
            button.label = "View Regenerated"
            button.emoji = "➡️"
        else:
            button.label = "View Original"
            button.emoji = "⬅️"
        await interaction.response.edit_message(content=response_text, view=self)

    @discord.ui.button(emoji="🗑️", label="Delete", style=discord.ButtonStyle.gray)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.debug(f"Message deletion requested by {interaction.user.display_name}")

        await interaction.message.edit(view=None)
        await interaction.message.delete()
