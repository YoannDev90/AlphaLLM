import discord
from discord import app_commands
from discord.ext import commands
from collections import deque, defaultdict
from utils.api_utils import get_chatbot_response

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversation_history = defaultdict(lambda: defaultdict(lambda: deque(maxlen=5)))
        self.use_history = True

@commands.Cog.listener()
async def on_message(self, message):
    if message.author == self.bot.user:
        return
    if isinstance(message.channel, discord.DMChannel):
        return
    
    if self.bot.user in message.mentions and message.content.split(None, 2)[1].startswith("'"):
        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        
        user_input = message.content.split("'", 1)[1].strip()
        
        if not user_input:
            await message.reply("Désolé, je n'ai pas compris votre demande. Pouvez-vous reformuler ?")
            return
        
        async with message.channel.typing():
            chat_cog = self.bot.get_cog('Chat')
            bot_response = await get_chatbot_response(
                guild_id, 
                channel_id, 
                user_id, 
                user_input, 
                chat_cog.use_history, 
                chat_cog.conversation_history
            )
            await message.reply(bot_response)

    @app_commands.command(name="toggle_history", description="Active/désactive l'historique des conversations")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_history(self, interaction: discord.Interaction):
        self.use_history = not self.use_history
        status = "activée" if self.use_history else "désactivée"
        await interaction.response.send_message(f"La fonction historique est maintenant {status}.")
