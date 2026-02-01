import logging

import discord
import requests
from discord import app_commands

from config import (BUG_REPORT_CHANNEL_ID, GITHUB_OWNER, GITHUB_REPO,
                    GITHUB_TOKEN, LOGGER_NAME)

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(name="report-bug", description="Report a bug to the developers")
    @app_commands.describe(
        title="Brief title of the bug",
        description="Detailed description of the bug",
        steps_to_reproduce="Steps to reproduce the bug (optional)",
        expected_behavior="What should happen (optional)",
        actual_behavior="What actually happens (optional)",
        additional_info="Any additional information, attachments, or notes (optional)",
    )
    async def report_bug(
        interaction: discord.Interaction,
        title: str,
        description: str,
        steps_to_reproduce: str = None,
        expected_behavior: str = None,
        actual_behavior: str = None,
        additional_info: str = None,
    ):
        logger.info(f"Command /report-bug executed by {interaction.user.display_name}")

        try:
            embed = discord.Embed(
                title="🐛 Bug Report",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(name="Title", value=title, inline=False)
            embed.add_field(name="Description", value=description, inline=False)
            if steps_to_reproduce:
                embed.add_field(
                    name="Steps to Reproduce", value=steps_to_reproduce, inline=False
                )
            if expected_behavior:
                embed.add_field(
                    name="Expected Behavior", value=expected_behavior, inline=False
                )
            if actual_behavior:
                embed.add_field(
                    name="Actual Behavior", value=actual_behavior, inline=False
                )
            if additional_info:
                embed.add_field(
                    name="Additional Info", value=additional_info, inline=False
                )
            embed.add_field(
                name="Reported by",
                value=f"{interaction.user.mention} ({interaction.user.display_name})",
                inline=False,
            )
            embed.add_field(
                name="Server",
                value=interaction.guild.name if interaction.guild else "DM",
                inline=False,
            )
            embed.set_footer(text=f"User ID: {interaction.user.id}")

            issue_url = None
            if GITHUB_TOKEN:
                try:
                    with open(
                        "configs/misc/issue_template.md", "r", encoding="utf-8"
                    ) as f:
                        template = f.read()
                except Exception as e:
                    logger.error(f"Failed to load issue template: {e}")
                    template = "**Bug Report from Discord**\n\n{title}\n\n{description}"

                issue_body = template.format(
                    title=title,
                    description=description,
                    steps_to_reproduce=steps_to_reproduce or "Not provided",
                    expected_behavior=expected_behavior or "Not provided",
                    actual_behavior=actual_behavior or "Not provided",
                    additional_info=additional_info or "Not provided",
                    user_name=interaction.user.display_name,
                    user_id=interaction.user.id,
                    server_name=interaction.guild.name if interaction.guild else "DM",
                    channel_name=(
                        interaction.channel.name
                        if hasattr(interaction.channel, "name")
                        else "DM"
                    ),
                    timestamp=discord.utils.utcnow().isoformat(),
                )
                github_url = (
                    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues"
                )
                headers = {
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json",
                }
                data = {
                    "title": f"Bug: {title}",
                    "body": issue_body,
                    "labels": ["bug", "discord-report"],
                }
                response = requests.post(github_url, json=data, headers=headers)
                if response.status_code == 201:
                    issue_data = response.json()
                    issue_url = issue_data.get("html_url")
                else:
                    logger.error(
                        f"Failed to create GitHub issue: {response.status_code} - {response.text}"
                    )

            if issue_url:
                embed.add_field(
                    name="GitHub Issue",
                    value=f"[View Issue]({issue_url})",
                    inline=False,
                )

            bug_report_channel = bot.get_channel(BUG_REPORT_CHANNEL_ID)
            if bug_report_channel:
                await bug_report_channel.send(embed=embed)
            else:
                logger.error("Bug report channel not found")

            if issue_url:
                await interaction.response.send_message(
                    f"Bug reported successfully! GitHub issue created: {issue_url}",
                    embed=embed,
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "Bug reported successfully!", embed=embed, ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in /report-bug command: {e}")
            await interaction.response.send_message(
                "An error occurred while reporting the bug. Please try again later.",
                ephemeral=True,
            )
