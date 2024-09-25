import discord
from discord.ext import commands
import config
from cogs.admin_commands import AdminCommands
from cogs.user_commands import UserCommands
from cogs.chat import Chat
from utils.logging_setup import setup_logging

intents = discord.Intents.default()
intents.message_content = True

class AlphaLLMBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='§', intents=intents)

    async def setup_hook(self):
        await self.add_cog(AdminCommands(self))
        await self.add_cog(UserCommands(self))
        await self.add_cog(Chat(self))
        await self.tree.sync()

    async def on_ready(self):
        print(f'{self.user} est connecté et prêt!')

bot = AlphaLLMBot()

if __name__ == '__main__':
    setup_logging()
    bot.run(config.TOKEN)
