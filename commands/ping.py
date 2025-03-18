import discord
import logging
import json
import schedule
import time
import asyncio
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from io import BytesIO
from datetime import datetime
from utils.langs import get_translation


logger = logging.getLogger('AlphaLLM')

def save_ping(latence):
    try:
        with open('config/ping_data.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {'pings': []}
    
    data['pings'].append({
        'timestamp': time.time(),
        'latence': latence
    })
    
    with open('config/ping_data.json', 'w') as file:
        json.dump(data, file, indent=4)

def clean_old_data():
    try:
        with open('config/ping_data.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return
    
    data['pings'] = [d for d in data['pings'] if time.time() - d['timestamp'] < 86400]
    
    with open('config/ping_data.json', 'w') as file:
        json.dump(data, file, indent=4)


async def record_ping(bot):
    latence = round(bot.latency * 1000)
    save_ping(latence)
    clean_old_data()
    logger.debug(f"Ping enregistré : {latence} ms")
    return latence

async def plot_ping():
    try:
        with open('config/ping_data.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    
    SEUIL_MAX = 150
    
    timestamps = [d['timestamp'] for d in data['pings']]
    latences = [min(d['latence'], SEUIL_MAX) for d in data['pings']]
    
    plt.figure(figsize=(10, 5))
    plt.gcf().set_facecolor('#2b2d31')
    plt.gca().set_facecolor('#2b2d31')
    plt.grid(visible=False)
    ax = plt.gca()
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.plot(latences, color='#d01919', linewidth=1.125)
    plt.ylim(min(latences) - 2, max(latences) + 2)
    
    plt.fill_between(range(len(latences)), latences, color='#d01919', alpha=0.5)
    for spine in plt.gca().spines.values():
        spine.set_visible(True)
    
    plt.xlabel('', color='white')
    plt.ylabel('', color='white')
    plt.yticks(color='white')
    
    relative_times = []
    for ts in timestamps:
        delta = time.time() - ts
        if delta < 60:
            relative_times.append(f"{int(delta)}s")
        elif delta < 3600:
            relative_times.append(f"{int(delta / 60)}min {int(delta % 60)}s")
        elif delta < 86400:
            relative_times.append(f"{int(delta / 3600)}h {int((delta % 3600) / 60)}min")
        else:
            relative_times.append(f"{int(delta / 86400)}j {int((delta % 86400) / 3600)}h")
    
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
        with open('config/ping_data.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
            latence_moyenne = None
    else:
        if data['pings']:
            latences = [d['latence'] for d in data['pings']]
            latence_moyenne = round(sum(latences) / len(latences))
        else:
            latence_moyenne = None
    return latence_moyenne
        

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
        latence = await record_ping(bot)
        latence_moyenne = await moyenne_ping()
    
        text = (
            f"Latence actuelle : {latence} ms\n"
            f"Latence moyenne : {latence_moyenne if latence_moyenne else 'Non disponible'} ms\n"
            f"Historique sur 24h :"
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
            await interaction.response.send_message(file=file, embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

    asyncio.create_task(schedule_tasks(bot))
