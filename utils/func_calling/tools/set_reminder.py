import logging
import asyncio
import datetime
import json
import os
from pathlib import Path
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

REMINDERS_FILE = Path("data/reminders.json")

def load_reminders():
    if not REMINDERS_FILE.exists():
        return []
    try:
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading reminders: {e}")
        return []

def save_reminders(reminders):
    try:
        with open(REMINDERS_FILE, "w") as f:
            json.dump(reminders, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving reminders: {e}")

async def set_reminder_tool(params, guild=None):
    if not guild:
        return "error: Discord context missing."

    time_val = params.get("time")
    unit = params.get("unit", "minutes")
    message = params.get("message", "This is your reminder!")
    user_id = params.get("user_id")
    channel_id = params.get("channel_id")

    if not time_val:
        return "error: Missing 'time' parameter."

    multipliers = {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}
    delay_seconds = int(time_val) * multipliers.get(unit, 60)
    
    target_time = datetime.datetime.now() + datetime.timedelta(seconds=delay_seconds)
    target_timestamp = target_time.timestamp()

    try:
        reminders = load_reminders()
        reminders.append({
            "user_id": str(user_id),
            "channel_id": str(channel_id),
            "message": message,
            "target_timestamp": target_timestamp
        })
        save_reminders(reminders)

        msg = f"Reminder set for {time_val} {unit} from now. I will notify you <@{user_id}>."
        logger.info(f"set_reminder_tool: {msg}")
        return msg
    except Exception as e:
        logger.error(f"Error setting reminder: {e}")
        return f"error: Failed to set reminder: {e}"

async def process_reminders(bot):
    while True:
        try:
            reminders = load_reminders()
            if not reminders:
                await asyncio.sleep(30)
                continue

            now = datetime.datetime.now().timestamp()
            remaining = []
            to_send = []

            for rem in reminders:
                if now >= rem["target_timestamp"]:
                    to_send.append(rem)
                else:
                    remaining.append(rem)

            if to_send:
                for rem in to_send:
                    try:
                        channel = bot.get_channel(int(rem["channel_id"]))
                        if channel:
                            await channel.send(f"🔔 <@{rem['user_id']}>: {rem['message']}")
                        else:
                            logger.warning(f"Could not find channel {rem['channel_id']} for reminder.")
                    except Exception as send_err:
                        logger.error(f"Error sending reminder: {send_err}")
                
                # Update file after sending
                save_reminders(remaining)

        except Exception as e:
            logger.error(f"Error in process_reminders loop: {e}")
        
        await asyncio.sleep(30)