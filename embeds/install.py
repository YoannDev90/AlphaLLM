import discord
from utils.config import BOTS_LINKS, TIMEOUT_INSTALL_VIEW

# Liens d'invitation des bots (depuis config.toml)
chatgpt_link = BOTS_LINKS.get("chatgpt", "")
deepseek_link = BOTS_LINKS.get("deepseek", "")
evilgpt_link = BOTS_LINKS.get("evilgpt", "")
gemini_link = BOTS_LINKS.get("gemini", "")
grok_link = BOTS_LINKS.get("grok", "")
llama_link = BOTS_LINKS.get("llama", "")
mistral_link = BOTS_LINKS.get("mistral", "")
perplexity_link = BOTS_LINKS.get("perplexity", "")
qwen_link = BOTS_LINKS.get("qwen", "")
claude_link = BOTS_LINKS.get("claude", "")
command_link = BOTS_LINKS.get("command", "")
glm_link = BOTS_LINKS.get("glm", "")
kimi_link = BOTS_LINKS.get("kimi", "")
phi_link = BOTS_LINKS.get("phi", "")


# Descriptions des bots
bot_descriptions = {
    "ChatGPT": "🤖 Based on GPT-5, excellent for conversation and general tasks.",
    "DeepSeek": "🧠 Advanced reasoning model specialized in solving complex problems.",
    "EvilGPT": "😈 Alternative version with a more provocative and free personality.",
    "Gemini": "💎 Google's multimodal AI, capable of processing text, images and more.",
    "Grok": "🚀 xAI's AI assistant with a unique and innovative approach.",
    "Llama": "🦙 Meta's open-source model, performant and transparent.",
    "Mistral": "🌪️ Fast and efficient French AI for various tasks.",
    "Perplexity": "🔍 Specialist in search and real-time information.",
    "Qwen": "🈳 Alibaba's model with excellent multilingual capabilities.",
    "Claude": "🎨 Poetic and creative, excellent for literary and reflective writing.",
    "Command": "💡 Powerful in logic and analytical reasoning, suited for comparisons.",
    "GLM": "🌏 Excellent multilingual support, great for translation and cross-language understanding.",
    "Kimi": "📚 Clear and pedagogical, ideal for education, explanation, and learning tasks.",
    "Phi": "⚙️ Lightweight and efficient, best for simple and quick requests."
}

class InstallView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=TIMEOUT_INSTALL_VIEW)
        
        # Ajouter les boutons pour chaque bot
        buttons_data = [
            ("ChatGPT", chatgpt_link, "🤖"),
            ("DeepSeek", deepseek_link, "🧠"),
            ("EvilGPT", evilgpt_link, "😈"),
            ("Gemini", gemini_link, "💎"),
            ("Grok", grok_link, "🚀"),
            ("Llama", llama_link, "🦙"),
            ("Mistral", mistral_link, "🌪️"),
            ("Perplexity", perplexity_link, "🔍"),
            ("Qwen", qwen_link, "🈳"),
            ("Claude", claude_link, "🎨"),
            ("Command", command_link, "💡"),
            ("GLM", glm_link, "🌏"),
            ("Kimi", kimi_link, "📚"),
            ("Phi", phi_link, "⚙️")
        ]
        
        for name, url, emoji in buttons_data:
            button = discord.ui.Button(
                label=f"{emoji} {name}",
                url=url,
                style=discord.ButtonStyle.link
            )
            self.add_item(button)

def create_install_embed(user: discord.User) -> discord.Embed:
    """Créer l'embed pour la commande install"""
    embed = discord.Embed(
        title="🤖 AlphaLLM Bots Installation",
        description="Choose the bots you want to install on your server. Each bot has its own specialties and unique characteristics.",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    
    for name, description in bot_descriptions.items():
        embed.add_field(name=name, value=description, inline=False)
    
    embed.set_footer(
        text=f"Requested by {user.display_name} • Click the buttons below to install",
        icon_url=user.display_avatar.url
    )
    
    return embed
