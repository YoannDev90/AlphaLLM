import discord

# Liens d'invitation des bots
chatgpt_link = "https://discord.com/oauth2/authorize?client_id=1370683080892747796"
deepseek_link = "https://discord.com/oauth2/authorize?client_id=1370682029460684850"
evilgpt_link = "https://discord.com/oauth2/authorize?client_id=1370685660326920252"
gemini_link = "https://discord.com/oauth2/authorize?client_id=1370683258274185349"
grok_link = "https://discord.com/oauth2/authorize?client_id=1370683169522847827"
llama_link = "https://discord.com/oauth2/authorize?client_id=1370685321703854110"
mistral_link = "https://discord.com/oauth2/authorize?client_id=1370685184269352962"
perplexity_link = "https://discord.com/oauth2/authorize?client_id=1370681547740418079"
qwen_link = "https://discord.com/oauth2/authorize?client_id=1370686144542539846"

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
    "Qwen": "🈳 Alibaba's model with excellent multilingual capabilities."
}

class InstallView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        
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
            ("Qwen", qwen_link, "🈳")
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
