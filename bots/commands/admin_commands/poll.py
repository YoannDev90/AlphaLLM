import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List

import discord

from config import DEV_IDS, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

# Store active polls: {message_id: {"question": str, "options": List[str], "votes": Dict[str, List[int]], "end_time": datetime}}
active_polls: Dict[int, Dict] = {}

# Store poll data to file
POLL_DATA_FILE = "data/polls.json"


def load_poll_data():
    """Load poll data from file"""
    if os.path.exists(POLL_DATA_FILE):
        try:
            with open(POLL_DATA_FILE, "r") as f:
                data = json.load(f)
                # Convert end_time strings back to datetime objects
                for poll_id, poll_data in data.items():
                    if "end_time" in poll_data and poll_data["end_time"]:
                        poll_data["end_time"] = datetime.fromisoformat(
                            poll_data["end_time"]
                        )
                active_polls.update({int(k): v for k, v in data.items()})
        except Exception as e:
            logger.error(f"Failed to load poll data: {e}")


def save_poll_data():
    """Save poll data to file"""
    try:
        # Convert datetime objects to strings for JSON serialization
        data_to_save = {}
        for poll_id, poll_data in active_polls.items():
            data_copy = poll_data.copy()
            if "end_time" in data_copy and isinstance(data_copy["end_time"], datetime):
                data_copy["end_time"] = data_copy["end_time"].isoformat()
            data_to_save[str(poll_id)] = data_copy

        with open(POLL_DATA_FILE, "w") as f:
            json.dump(data_to_save, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save poll data: {e}")


class PollModal(discord.ui.Modal, title="Create Poll"):
    """Modal for creating a poll"""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.question = discord.ui.TextInput(
            label="Poll Question",
            style=discord.TextStyle.short,
            placeholder="What is your favorite color?",
            required=True,
            max_length=200,
        )
        self.add_item(self.question)

        self.options = discord.ui.TextInput(
            label="Options (one per line, 2-10 options)",
            style=discord.TextStyle.paragraph,
            placeholder="Red\nBlue\nGreen\nYellow",
            required=True,
            max_length=1000,
        )
        self.add_item(self.options)

        self.duration = discord.ui.TextInput(
            label="Duration (optional, e.g. 1h, 30m, 2d)",
            style=discord.TextStyle.short,
            placeholder="Leave empty for no time limit",
            required=False,
            max_length=10,
        )
        self.add_item(self.duration)

    async def on_submit(self, interaction: discord.Interaction):
        question = self.question.value.strip()
        options_text = self.options.value.strip()
        duration_text = self.duration.value.strip() if self.duration.value else ""

        # Parse options
        options = [opt.strip() for opt in options_text.split("\n") if opt.strip()]
        if len(options) < 2 or len(options) > 10:
            await interaction.response.send_message(
                "❌ You must provide between 2 and 10 options.", ephemeral=True
            )
            return

        # Remove duplicates
        options = list(dict.fromkeys(options))
        if len(options) < 2:
            await interaction.response.send_message(
                "❌ You must provide at least 2 unique options.", ephemeral=True
            )
            return

        # Parse duration
        end_time = None
        if duration_text:
            try:
                end_time = parse_duration(duration_text)
            except ValueError as e:
                await interaction.response.send_message(
                    f"❌ Invalid duration format: {e}", ephemeral=True
                )
                return

        # Create confirmation embed
        embed = discord.Embed(
            title="📊 Poll Confirmation",
            description=f"**Question:** {question}",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )

        options_text = "\n".join(f"• {opt}" for opt in options)
        embed.add_field(name="Options", value=options_text, inline=False)

        if end_time:
            embed.add_field(
                name="Duration",
                value=f"Ends <t:{int(end_time.timestamp())}:R>",
                inline=True,
            )

        embed.set_footer(text="⚠️ Please confirm to create this poll")

        view = PollConfirmView(question, options, end_time, self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


def parse_duration(duration_str: str) -> datetime:
    """Parse duration string like '1h', '30m', '2d'"""
    duration_str = duration_str.lower().strip()

    if duration_str.endswith("d"):
        days = int(duration_str[:-1])
        return datetime.now() + timedelta(days=days)
    elif duration_str.endswith("h"):
        hours = int(duration_str[:-1])
        return datetime.now() + timedelta(hours=hours)
    elif duration_str.endswith("m"):
        minutes = int(duration_str[:-1])
        return datetime.now() + timedelta(minutes=minutes)
    else:
        raise ValueError(
            "Duration must end with 'd' (days), 'h' (hours), or 'm' (minutes)"
        )


class PollConfirmView(discord.ui.View):
    """View for confirming poll creation"""

    def __init__(self, question: str, options: List[str], end_time: datetime, bot):
        super().__init__(timeout=300)
        self.question = question
        self.options = options
        self.end_time = end_time
        self.bot = bot

    @discord.ui.button(label="✅ Create Poll", style=discord.ButtonStyle.green)
    async def confirm_create(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()

        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)

        # Create and send poll
        await create_poll(interaction, self.question, self.options, self.end_time)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel_create(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="❌ Poll Creation Cancelled",
            description="The poll has been cancelled.",
            color=discord.Color.red(),
            timestamp=datetime.now(),
        )
        await interaction.response.edit_message(embed=embed, view=None)


class PollView(discord.ui.View):
    """View for voting on a poll"""

    def __init__(self, poll_id: int):
        super().__init__(timeout=None)
        self.poll_id = poll_id

    async def create_buttons(self, options: List[str]):
        """Create vote buttons dynamically"""
        for i, option in enumerate(options):
            button = VoteButton(option, i)
            self.add_item(button)


class VoteButton(discord.ui.Button):
    """Button for voting on a poll option"""

    def __init__(self, option: str, option_index: int):
        super().__init__(
            label=option[:80],  # Discord button label limit
            style=discord.ButtonStyle.primary,
            custom_id=f"poll_vote_{option_index}",
        )
        self.option = option
        self.option_index = option_index

    async def callback(self, interaction: discord.Interaction):
        poll_data = active_polls.get(self.view.poll_id)
        if not poll_data:
            await interaction.response.send_message(
                "❌ This poll is no longer active.", ephemeral=True
            )
            return

        # Check if poll has ended
        if poll_data.get("end_time") and datetime.now() > poll_data["end_time"]:
            await interaction.response.send_message(
                "❌ This poll has ended.", ephemeral=True
            )
            return

        user_id = interaction.user.id
        votes = poll_data.setdefault("votes", {})

        # Remove previous vote if any
        for option_votes in votes.values():
            if user_id in option_votes:
                option_votes.remove(user_id)

        # Add new vote
        option_votes = votes.setdefault(self.option, [])
        option_votes.append(user_id)

        # Save data
        save_poll_data()

        # Send confirmation
        await interaction.response.send_message(
            f"✅ Your vote for **{self.option}** has been recorded!", ephemeral=True
        )

        # Update the poll message
        await update_poll_message(interaction.client, self.view.poll_id)


async def create_poll(
    interaction: discord.Interaction,
    question: str,
    options: List[str],
    end_time: datetime = None,
):
    """Create and send a poll"""

    # Create poll embed
    embed = discord.Embed(
        title="📊 Poll",
        description=f"**{question}**",
        color=discord.Color.blue(),
        timestamp=datetime.now(),
    )

    # Add options
    options_text = "\n".join(f"{i + 1}. {opt}" for i, opt in enumerate(options))
    embed.add_field(name="Options", value=options_text, inline=False)

    if end_time:
        embed.add_field(
            name="Ends", value=f"<t:{int(end_time.timestamp())}:R>", inline=True
        )

    embed.set_footer(text=f"Started by {interaction.user.display_name}")

    # Send poll message
    poll_view = PollView(0)  # poll_id will be set after sending
    await poll_view.create_buttons(options)

    poll_message = await interaction.followup.send(embed=embed, view=poll_view)

    # Store poll data
    poll_data = {
        "question": question,
        "options": options,
        "votes": {},
        "creator_id": interaction.user.id,
        "channel_id": interaction.channel.id,
        "guild_id": interaction.guild.id,
        "end_time": end_time,
        "created_at": datetime.now(),
    }

    active_polls[poll_message.id] = poll_data
    poll_view.poll_id = poll_message.id

    # Save data
    save_poll_data()

    logger.info(f"Poll created: {question} (ID: {poll_message.id})")


async def update_poll_message(client, poll_message_id: int):
    """Update the poll message with current results"""
    poll_data = active_polls.get(poll_message_id)
    if not poll_data:
        return

    try:
        channel = client.get_channel(poll_data["channel_id"])
        if not channel:
            return

        message = await channel.fetch_message(poll_message_id)
        if not message:
            return

        # Create updated embed
        embed = discord.Embed(
            title="📊 Poll Results",
            description=f"**{poll_data['question']}**",
            color=discord.Color.blue(),
            timestamp=poll_data["created_at"],
        )

        votes = poll_data.get("votes", {})
        total_votes = sum(len(voters) for voters in votes.values())

        # Add results
        results_text = ""
        for i, option in enumerate(poll_data["options"]):
            vote_count = len(votes.get(option, []))
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            bar = create_progress_bar(percentage)
            results_text += (
                f"{i + 1}. {option}\n{bar} {vote_count} votes ({percentage:.1f}%)\n\n"
            )

        embed.add_field(
            name=f"Results ({total_votes} votes)",
            value=results_text or "No votes yet",
            inline=False,
        )

        if poll_data.get("end_time"):
            if datetime.now() > poll_data["end_time"]:
                embed.add_field(name="Status", value="🛑 Poll Ended", inline=True)
            else:
                embed.add_field(
                    name="Ends",
                    value=f"<t:{int(poll_data['end_time'].timestamp())}:R>",
                    inline=True,
                )

        embed.set_footer(text=f"Started by <@{poll_data['creator_id']}>")

        # Update message
        poll_view = PollView(poll_message_id)
        await poll_view.create_buttons(poll_data["options"])

        await message.edit(embed=embed, view=poll_view)

    except Exception as e:
        logger.error(f"Failed to update poll message {poll_message_id}: {e}")


def create_progress_bar(percentage: float, length: int = 10) -> str:
    """Create a progress bar string"""
    filled = int(percentage / 100 * length)
    bar = "█" * filled + "░" * (length - filled)
    return bar


async def check_expired_polls(client):
    """Check for expired polls and update them"""
    now = datetime.now()
    expired_polls = []

    for poll_id, poll_data in active_polls.items():
        if poll_data.get("end_time") and now > poll_data["end_time"]:
            expired_polls.append(poll_id)

    for poll_id in expired_polls:
        await update_poll_message(client, poll_id)
        logger.info(f"Poll {poll_id} has expired")


async def setup(bot: discord.Client):
    # Load existing poll data
    load_poll_data()

    # Restore poll views
    for poll_id in active_polls.keys():
        poll_view = PollView(poll_id)
        poll_data = active_polls[poll_id]
        await poll_view.create_buttons(poll_data["options"])
        bot.add_view(poll_view)

    @bot.tree.command(name="poll", description="Create a poll for users to vote on")
    async def poll(interaction: discord.Interaction):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message(
                "❌ You are not authorized to use this command.", ephemeral=True
            )
            return

        if not (
            interaction.user.guild_permissions.administrator
            or interaction.user.guild_permissions.manage_messages
        ):
            await interaction.response.send_message(
                "❌ You need administrator or manage messages permission to create polls.",
                ephemeral=True,
            )
            return

        modal = PollModal(bot)
        await interaction.response.send_modal(modal)
