# AlphaLLM

[![GitHub stars](https://img.shields.io/github/stars/YoannDev90/AlphaLLM?style=for-the-badge)](https://github.com/YoannDev90/AlphaLLM/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/YoannDev90/AlphaLLM?style=for-the-badge)](https://github.com/YoannDev90/AlphaLLM/issues)
[![GitHub license](https://img.shields.io/github/license/YoannDev90/AlphaLLM?style=for-the-badge&type=mit)](https://github.com/YoannDev90/AlphaLLM/blob/dev/LICENSE)
[![Wakatime](https://wakatime.com/badge/github/YoannDev90/AlphaLLM.svg?style=for-the-badge)](https://wakatime.com/badge/github/YoannDev90/AlphaLLM)
[![Discord](https://img.shields.io/discord/1327996079786168441?color=blue&label=Discord&logo=discord&style=for-the-badge)](https://discord.com/invite/QGvyrUgwdK)

<img src="https://wakatime.com/share/@dfc968e3-fc46-4804-b046-5564e46d093a/cbdb2974-405c-41cd-acbd-c55b6849f294.svg" alt="ChatGPT" style="width: 800px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
<img src="https://repobeats.axiom.co/api/embed/d1ef951054604efff035919fef4255170881619b.svg" alt="ChatGPT" style="width: 800px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">

AlphaLLM is an advanced Discord bot that integrates multiple AI models for text and image generation. It provides a RAG memory system and administrative features.

## 🚀 Features

- 🤖 Discord bot with text and image generation
- 🧠 RAG memory system
- 🎯 Automatic AI model selection
- 📊 Logging and diagnostics

## 🤖 Supported AI Models

The bot supports many models: ChatGPT, Claude, Cohere, DeepSeek, Gemini, GLM, Grok, Llama, Mistral, Qwen, Sonar, and more.

| ![ChatGPT](https://alphallm.tech/assets/images/models/large/chatgpt.webp) |     ![Claude](https://alphallm.tech/assets/images/models/large/claude.webp)      | ![DeepSeek](https://alphallm.tech/assets/images/models/large/deepseek.webp?v=90400c60) | ![Gemini](https://alphallm.tech/assets/images/models/large/gemini.webp) |     ![GLM](https://alphallm.tech/assets/images/models/large/glm.webp)      |
| :-----------------------------------------------------------------------: | :------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------: | :---------------------------------------------------------------------: | :------------------------------------------------------------------------: |
|                                **ChatGPT**                                |                                    **Claude**                                    |                                      **DeepSeek**                                      |                               **Gemini**                                |                                  **GLM**                                   |
|    ![Grok](https://alphallm.tech/assets/images/models/large/grok.webp)    | ![Llama](https://alphallm.tech/assets/images/models/large/llama.webp?v=1ef92b76) |       ![Mistral](https://alphallm.tech/assets/images/models/large/mistral.webp)        |   ![Qwen](https://alphallm.tech/assets/images/models/large/qwen.webp)   | ![Sonar](https://alphallm.tech/assets/images/models/large/perplexity.webp) |
|                                 **Grok**                                  |                                    **Llama**                                     |                                      **Mistral**                                       |                                **Qwen**                                 |                                 **Sonar**                                  |

## 📦 Installation

### Prerequisites

- Python 3.12+
- API Keys
- 2 GB RAM + 5 GB Disk

## ⚙️ Configuration

Edit `config.toml` for:

- Discord IDs (servers, channels)
- Runtime settings
- Memory models

Edit `.env` for provider keys.

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
