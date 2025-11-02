import discord
import logging
import tempfile
import os
from utils.config import logger_name

logger = logging.getLogger(logger_name)

logger = logging.getLogger(logger_name)

class CodeView(discord.ui.View):
    def __init__(self, codeblock):
        super().__init__()
        self.codeblock = codeblock

    @discord.ui.button(emoji="💾", label="Download", style=discord.ButtonStyle.gray)
    async def export(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Export de bloc de code demandé par {interaction.user.display_name}")
        await interaction.response.defer()

        if self.codeblock.startswith('```') and '```' in self.codeblock:
            lines = self.codeblock.strip().split('\n')
            if len(lines) >= 3 and lines[0].startswith('```'):
                lang = lines[0][3:].strip().lower()
                code = '\n'.join(lines[1:-1])
            else:
                lang = 'txt'
                code = self.codeblock
        else:
            lang = 'txt'
            code = self.codeblock

        ext_map = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'csharp': 'cs',
            'cpp': 'cpp',
            'c': 'c',
            'php': 'php',
            'ruby': 'rb',
            'go': 'go',
            'rust': 'rs',
            'swift': 'swift',
            'kotlin': 'kt',
            'scala': 'scala',
            'perl': 'pl',
            'lua': 'lua',
            'r': 'r',
            'matlab': 'm',
            'shell': 'sh',
            'bash': 'sh',
            'powershell': 'ps1',
            'sql': 'sql',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'xml': 'xml',
            'yaml': 'yaml',
            'yml': 'yml',
            'markdown': 'md',
            'md': 'md',
            'txt': 'txt',
            'vb': 'vb',
            'fsharp': 'fs',
            'haskell': 'hs',
            'clojure': 'clj',
            'erlang': 'erl',
            'elixir': 'ex',
            'dart': 'dart',
            'groovy': 'groovy',
            'julia': 'jl',
            'raku': 'raku',
            'nim': 'nim',
            'crystal': 'cr',
            'zig': 'zig',
            'solidity': 'sol',
            'assembly': 'asm'
        }
        ext = ext_map.get(lang, 'txt')

        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{ext}', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_path = f.name

        try:
            await interaction.followup.send(file=discord.File(temp_path, f'code.{ext}'))
        finally:
            os.unlink(temp_path)