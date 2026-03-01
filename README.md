# AlphaLLM

[![GitHub stars](https://img.shields.io/github/stars/YoannDev90/AlphaLLM?style=for-the-badge)](https://github.com/YoannDev90/AlphaLLM/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/YoannDev90/AlphaLLM?style=for-the-badge)](https://github.com/YoannDev90/AlphaLLM/issues)
[![GitHub license](https://img.shields.io/github/license/YoannDev90/AlphaLLM?style=for-the-badge&type=mit)](https://github.com/YoannDev90/AlphaLLM/blob/dev/LICENSE)
[![Wakatime](https://wakatime.com/badge/github/YoannDev90/AlphaLLM.svg?style=for-the-badge)](https://wakatime.com/badge/github/YoannDev90/AlphaLLM)
[![Discord](https://img.shields.io/discord/1327996079786168441?color=blue&label=Discord&logo=discord&style=for-the-badge)](https://discord.com/invite/QGvyrUgwdK)

<img src="https://wakatime.com/share/@dfc968e3-fc46-4804-b046-5564e46d093a/cbdb2974-405c-41cd-acbd-c55b6849f294.svg" alt="ChatGPT" style="width: 800px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
<img src="https://repobeats.axiom.co/api/embed/d1ef951054604efff035919fef4255170881619b.svg" alt="ChatGPT" style="width: 800px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">

AlphaLLM is an advanced Discord bot that integrates multiple AI models for text and image generation. It provides a REST API, RAG memory system, and administrative features.

## 📚 Documentation

Detailed documentation is available in the [`docs/`](docs/) folder:

- [Architecture](docs/architecture.md)
- [Memory System](docs/memory.md)
- [API Reference](docs/api.md)
- [Configuration](docs/configuration.md)
- [Deployment](docs/deployment.md)

## 🚀 Features

- 🤖 Discord bot with text and image generation
- 🌐 REST API for programmatic access
- 🧠 RAG memory system
- 🎯 Automatic AI model selection
- 📊 Monitoring and logging

## 🤖 Supported AI Models

The bot supports many models: ChatGPT, Claude, Cohere, DeepSeek, EvilGPT, Gemini, GLM, Granite, Grok, Hermes, Kimi, Llama, LongCat, MiniMax, Mistral, Nemotron, Phi, Qwen, Sonar, Yi, and more.

| <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/chatgpt.webp" alt="ChatGPT" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/claude.webp" alt="Claude" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/cohere.webp" alt="Cohere" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/deepseek.webp?v=90400c60" alt="DeepSeek" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
|                                                                            <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">ChatGPT</div>                                                                            |                                                                         <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Claude</div>                                                                          |                                                                    <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Cohere</div>                                                                     |                                                                        <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">DeepSeek</div>                                                                         |
| <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/evilgpt.webp" alt="EvilGPT" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/gemini.webp" alt="Gemini" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/glm.webp" alt="GLM" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/ibm.webp" alt="Granite" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> |
|                                                                        <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">EvilGPT</div>                                                                        |                                                                       <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Gemini</div>                                                                        |                                                                       <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">GLM</div>                                                                        |                                                                       <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Granite</div>                                                                       |
| <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/grok.webp" alt="Grok" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/hermes.webp" alt="Hermès" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/moonshot.webp" alt="Kimi" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/llama.webp?v=1ef92b76" alt="Llama" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> |
|                                                                       <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Grok</div>                                                                       |                                                                     <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Hermès</div>                                                                     |                                                                    <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Kimi</div>                                                                     |                                                                       <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Llama</div>                                                                        |
| <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/longcat.webp" alt="LongCat" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/minimax.webp" alt="MiniMax" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/mistral.webp" alt="Mistral" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/nemotron.webp" alt="Nemotron" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> |
|                                                                   <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">LongCat</div>                                                                   |                                                                     <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">MiniMax</div>                                                                     |                                                                    <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Mistral</div>                                                                     |                                                                       <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Nemotron</div>                                                                       |
| <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/phi.webp" alt="Phi" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/qwen.webp" alt="Qwen" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/perplexity.webp" alt="Sonar" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> | <div style="text-align: center; vertical-align: middle;"><img src="https://alphallm.tech/assets/images/models/large/yi.webp" alt="Yi" style="width: 64px; height: 64px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"> </div> |
|                                                                     <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Phi</div>                                                                     |                                                                    <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Qwen</div>                                                                     |                                                                       <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Sonar</div>                                                                        |                                                                      <div style="text-align: center; font-weight: 600; font-size: 0.95rem; padding-top: 0.25rem;">Yi</div>                                                                       |

## 📦 Installation

### Prerequisites

- Python 3.12+
- API Keys
- 2 GB RAM + 5 GB Disk

## ⚙️ Configuration

Edit `config.toml` for:

- Discord IDs (servers, channels)
- API parameters
- Memory models

Edit `.env` for API keys.

## 🛟 Code Quality

Run the following command to format and lint the codebase:

```bash
black --exclude=.venv . && isort --skip=.venv . && flake8 --exclude=.venv .
```

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting and style checking

## 📄 License

MIT
