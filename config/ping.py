import discord
import logging
import json
import schedule
import time
import asyncio
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from supabase import create_client, Client, ClientOptions
from io import BytesIO
from datetime import datetime, timedelta
from utils.langs import get_translation as tlt
import os
import numpy as np


logger = logging.getLogger('AlphaLLM')

url = os.getenv("DB_URL")
key = os.getenv("DB_KEY")
jwt = os.getenv("JWT_KEY")
supabase: Client = create_client(url, key, options=ClientOptions(
    schema="public",
    headers={"Authorization": f"Bearer {jwt}"},
    auto_refresh_token=True,
    persist_session=True
))


def save_ping(latence):
    try:
        supabase.table("ping").insert({
            "timestamp": datetime.now().isoformat(),
            "latence": latence
        }).execute()
    except Exception as e:
        logger.error(f"Exception while saving ping: {e}")


def clean_old_data():
    try:
        cutoff_time = datetime.now() - timedelta(hours=12)
        supabase.table("ping").delete().lt("timestamp", cutoff_time.isoformat()).execute()
    except Exception as e:
        logger.error(f"Exception while cleaning old data: {e}")


async def record_ping(bot):
    latence = round(bot.latency * 1000)
    save_ping(latence)
    clean_old_data()
    logger.debug(f"Ping enregistré : {latence} ms")
    return latence


async def plot_ping():
    try:
        cutoff_time = datetime.now() - timedelta(hours=24)
        response = supabase.table("ping").select("*").gte("timestamp", cutoff_time.isoformat()).execute()
        data = response.data
    except Exception as e:
        logger.error(f"Exception while fetching ping data: {e}")
        return None

    if not data:
        return None

    SEUIL_MAX = 150

    timestamps = [datetime.fromisoformat(d['timestamp']) for d in data]
    latences = [min(d['latence'], SEUIL_MAX) for d in data]

    def moving_average(data, window_size):
        kernel = np.ones(window_size) / window_size
        return np.convolve(data, kernel, mode='same')

    lissage_window = 3
    latences_lissees = moving_average(latences, lissage_window)

    plt.figure(figsize=(10, 5))
    plt.gcf().set_facecolor('#2b2d31')
    plt.gca().set_facecolor('#2b2d31')
    plt.grid(visible=False)
    ax = plt.gca()
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.plot(latences_lissees, color='#d01919', linewidth=1.125)
    plt.ylim(min(latences) - 2, max(latences) + 2)

    plt.fill_between(range(len(latences)), latences_lissees, color='#d01919', alpha=0.5)
    for spine in plt.gca().spines.values():
        spine.set_visible(True)

    plt.xlabel('', color='white')
    plt.ylabel('', color='white')
    plt.yticks(color='white')

    relative_times = []
    for ts in timestamps:
        delta = datetime.now() - ts
        if delta.total_seconds() < 60:
            relative_times.append(f"{int(delta.total_seconds())}s")
        elif delta.total_seconds() < 3600:
            relative_times.append(f"{int(delta.total_seconds() / 60)}min")
        elif delta.total_seconds() < 86400:
            relative_times.append(f"{int(delta.total_seconds() / 3600)}h")

    ticks = range(len(timestamps))

    if len(ticks) > 12:
        step = max(1, len(ticks) // 12)
        plt.xticks(ticks[::step], relative_times[::step], rotation=45, color='white')
    else:
        plt.xticks(ticks, relative_times, rotation=45, color='white')

    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    return buffer


async def moyenne_ping():
    try:
        cutoff_time = datetime.now() - timedelta(hours=12)
        response = supabase.table("ping").select("latence").gte("timestamp", cutoff_time.isoformat()).execute()
        data = response.data
    except Exception as e:
        logger.error(f"Exception while fetching ping data: {e}")
        return None

    if not data:
        return None

    latences = [d['latence'] for d in data]
    return round(sum(latences) / len(latences))


async def schedule_tasks(bot):
    now = datetime.now()
    current_seconds = now.second
    if current_seconds < 30:
        wait_seconds = 30 - current_seconds
    else:
        wait_seconds = 60 - current_seconds
    await asyncio.sleep(wait_seconds)
    schedule.every(30).seconds.do(lambda: asyncio.create_task(record_ping(bot)))

    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


async def setup(bot: discord.Client):
    @bot.tree.command(name="ping", description="Affiche la latence du bot")
    async def ping(interaction: discord.Interaction):

        await interaction.response.defer(thinking=True)

        latence = await record_ping(bot)
        latence_moyenne = await moyenne_ping()

        text = (
            f"Latence actuelle : {latence} ms\n"
            f"Latence moyenne : {latence_moyenne if latence_moyenne else 'Non disponible'} ms\n"
            f"Historique sur 12h :"
        )

        embed = discord.Embed(
            title=text,
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        logger.info(f"Commande ping exécutée par {interaction.user.display_name}")
        image_buffer = await plot_ping()
        if image_buffer:
            file = discord.File(image_buffer, filename="ping_graph.png")
            embed.set_image(url="attachment://ping_graph.png")
            await interaction.followup.send(file=file, embed=embed)
        else:
            await interaction.followup.send(embed=embed)

    asyncio.create_task(schedule_tasks(bot))