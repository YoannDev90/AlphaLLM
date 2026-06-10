<div align="center">

# AlphaLLM

### *The sophisticated, AI-powered Discord agent.*

<img src="assets/images/alphallm.png" alt="AlphaLLM Icon" width="160" style="border-radius:24px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); margin: 20px 0;" />

---

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Discord](https://img.shields.io/badge/Discord.py-2.7.1-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Uv](https://img.shields.io/badge/Package--Manager-uv-F43F5E?style=for-the-badge)](https://github.com/astral-sh/uv)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-000000?style=for-the-badge&logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-004d40?style=for-the-badge)](https://github.com/YoannDev90/AlphaLLM/graphs/commit-activity)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-673ab7?style=for-the-badge)](https://github.com/YoannDev90/AlphaLLM/pulls)
[![Open Issues](https://img.shields.io/github/issues-raw/YoannDev90/AlphaLLM?style=for-the-badge&logo=github&color=CE93D8)](https://github.com/YoannDev90/AlphaLLM/issues)
[![Stars](https://img.shields.io/github/stars/YoannDev90/AlphaLLM?style=for-the-badge&logo=github&color=FFF176&logoColor=black)](https://github.com/YoannDev90/AlphaLLM/stargazers)
[![Repo Size](https://img.shields.io/github/repo-size/YoannDev90/AlphaLLM?style=for-the-badge&logo=git-lfs&color=4DB6AC)](https://github.com/YoannDev90/AlphaLLM)
[![Last Commit](https://img.shields.io/github/last-commit/YoannDev90/AlphaLLM?style=for-the-badge&logo=git&color=FF8A65)](https://github.com/YoannDev90/AlphaLLM/commits/master)
[![CI](https://img.shields.io/github/actions/workflow/status/YoannDev90/AlphaLLM/pre-commit.yml?style=for-the-badge&logo=github-actions&label=CI&color=4CAF50)](https://github.com/YoannDev90/AlphaLLM/actions)
[![OS](https://img.shields.io/badge/OS-Linux-E95420?style=for-the-badge&logo=linux&logoColor=white)](https://www.linux.org/)
[![Made with LiteLLM](https://img.shields.io/badge/Powered%20by-LiteLLM-black?style=for-the-badge)](https://github.com/BerriAI/litellm)
[![Profile](https://img.shields.io/badge/Follow-YoannDev90-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/YoannDev90)

---

**AlphaLLM** is a powerful Discord bot integrating state-of-the-art AI models to provide intelligent and contextual responses.

</div>

## Table of contents

- [Features](#-features)
- [Hosted Version](#🌐-hosted-version)
- [Commands](#📜-commands)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Dependencies](#-dependencies)
- [Development](#-development)
- [Adding Providers / Models](#adding-new-providers)
- [License](#-license)

## Hosted Version

You can invite the official hosted version of **AlphaLLM** to your server:

[**Invite AlphaLLM**](https://discord.com/oauth2/authorize?client_id=1513828113627222016)

## Commands

<!-- COMMANDS-START -->
| Command | Description |
| :--- | :--- |
| `/announce` | Send an announcement to all servers |
| `/health` | Show runtime health for bot subsystems |
| `/list-tools` | List all tools available to the model |
| `/memory-clear` | Clear the conversation history for a user |
| `/memory-delete` | Delete a specific turn from conversation history |
| `/memory-list` | List the most recent turns in memory |
| `/ping` | Check bot latency and responsiveness |
| `/poll` | Create a poll for users to vote on |
| `/support` | Show the support server link |

<!-- COMMANDS-END -->

## Features

- **Discord Integration**: Seamless integration with Discord using discord.py
- **Multi-Model Support**: Support for multiple AI models via LiteLLM
- **Multiple Providers**: Configure different API providers with ease
- **Async Processing**: Non-blocking message processing using asyncio
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Thread-Safe**: Prevents multiple concurrent requests from the same user
- **Dynamic Model Selection**: Automatically selects the best model based on capabilities
- **Persistent Memory**: Conversation history stays in a local CocoIndex-backed SQLite store
- **Transparent Deletion**: Use `/memory list`, `/memory delete`, and `/memory clear` to inspect or purge stored turns

## Quick Start

### Prerequisites

- Python 3.8+
- Discord Bot Token
- API credentials for your chosen AI provider / fallback providers

### Installation

1. **Clone and Setup**

   ```bash
   git clone https://github.com/YoannDev90/AlphaLLM.git
   cd AlphaLLM
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Dependencies** (Using `uv` is recommended for speed)

   ```bash
   pip install uv
   uv pip install -r requirements.txt
   ```

### Configuration

1. **Create a `.env` file** in the root directory:
<!--ENV-START-->
```env
BOT_TOKEN=
WEBHOOK_URL=
AIHUBMIX_API_KEY=
AQUA_API_KEY=
BLAZE_API_KEY=
LOGFLARE_API_KEY=
MEGANOVA_API_KEY=
MISTRAL_API_KEY=
MNN_API_KEY=
NAVY_API_KEY=
NVIDIA_NIM_API_KEY=
SECRETS_API_KEY=
TOKEN_REPLY_API_KEY=
DEPLOY_REMOTE_USER=
DEPLOY_REMOTE_HOST=
DEPLOY_REMOTE_DIR=
DEPLOY_SERVICE_NAME=
```
<!--ENV-END-->

1. **Configure providers** (optional)
   - Edit [`config/providers.json`](config/providers.json) to add or modify API providers
   - Edit [`config/models.json`](config/models.json) to configure available AI models

2. **Set up your Discord bot**
   - Create a bot on [Discord Developer Portal](https://discord.com/developers/applications)
   - Enable the "Message Content Intent" for the bot to read messages
   - Copy the bot token to your `.env` file

### Running the Bot

```bash
python main.py
```

## Deployment

AlphaLLM is designed for simple and reliable deployment on Linux servers.

### 1. Automated SSH Deployment

A powerful [`deploy.sh`](deploy.sh) script is provided to automate the entire process (transfer, dependencies, service restart).

1. **Prerequisites**: Install `sshpass` locally: `sudo apt install sshpass`.
2. **Setup**: Configure your server details in the `.env` file (see [Configuration](#configuration)).
3. **Execute**:

   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

### 2. Systemd Service

The bot includes a pre-configured [`alphallm.service`](alphallm.service) file.
The deployment script automatically installs this for you in `/etc/systemd/system/`, ensuring the bot starts on boot and restarts automatically if it crashes.

## Project Structure

Below is current snapshot of repository. This section is auto-updated by `./lint.sh` on demand.

<!-- TREE-START -->
```
.
├── alphallm.service
├── assets
│   ├── fonts
│   │   ├── NotoSans-BoldItalic.ttf
│   │   ├── NotoSans-Bold.ttf
│   │   ├── NotoSans-Italic.ttf
│   │   └── NotoSans-Regular.ttf
│   └── images
│       └── alphallm.png
├── bot.py
├── cmds
│   ├── annoncements.py
│   ├── health.py
│   ├── __init__.py
│   ├── list_tools.py
│   ├── loader.py
│   ├── memory_clear.py
│   ├── memory_delete.py
│   ├── memory_list.py
│   ├── ping.py
│   ├── polls.py
│   ├── _registry.py
│   ├── _shared.py
│   └── support.py
├── config
│   ├── links.json
│   ├── mcp.json
│   ├── models.json
│   ├── moods
│   │   └── basic.txt
│   ├── perms.json
│   ├── providers.json
│   └── tools
│       ├── image_ocr.json
│       ├── run_bash.json
│       ├── run_nodejs.json
│       ├── run_python.json
│       ├── safe_eval_math.json
│       ├── sandbox_create.json
│       ├── sandbox_exec.json
│       ├── sandbox_fs_list.json
│       ├── sandbox_fs_mkdir.json
│       ├── sandbox_fs_read.json
│       ├── sandbox_fs_remove.json
│       ├── sandbox_fs_stat.json
│       ├── sandbox_fs_write.json
│       ├── sandbox_inspect.json
│       ├── sandbox_list.json
│       ├── sandbox_metrics.json
│       ├── sandbox_remove.json
│       ├── sandbox_run.json
│       ├── sandbox_shell.json
│       └── sandbox_stop.json
├── config.toml
├── core
│   ├── config.py
│   ├── __init__.py
│   ├── model.py
│   ├── models_loader.py
│   └── tools.py
├── deploy.sh
├── .github
│   └── workflows
│       └── pre-commit.yml
├── .gitignore
├── LICENSE
├── lint.sh
├── main.py
├── managers
│   ├── context.py
│   ├── mcp.py
│   ├── memory.py
│   └── tools
│       ├── image_ocr.py
│       ├── __init__.py
│       ├── run_bash.py
│       ├── run_nodejs.py
│       ├── run_python.py
│       ├── safe_eval_math.py
│       ├── sandbox_create.py
│       ├── sandbox_exec.py
│       ├── sandbox_fs_list.py
│       ├── sandbox_fs_mkdir.py
│       ├── sandbox_fs_read.py
│       ├── sandbox_fs_remove.py
│       ├── sandbox_fs_stat.py
│       ├── sandbox_fs_write.py
│       ├── sandbox_inspect.py
│       ├── sandbox_list.py
│       ├── sandbox_metrics.py
│       ├── sandbox_remove.py
│       ├── sandbox_run.py
│       ├── sandbox_shell.py
│       └── sandbox_stop.py
├── requirements.txt
├── scripts
│   ├── generate_docs.py
│   ├── __init__.py
│   └── tests
│       ├── __init__.py
│       ├── test_codeblock.py
│       ├── test_config.py
│       ├── test_latex.py
│       ├── test_messages.py
│       ├── test_models.py
│       └── test_table.py
└── utils
    ├── handlers
    │   ├── codeblock.py
    │   ├── latex.py
    │   ├── messages.py
    │   └── table.py
    └── logger.py

17 directories, 97 files
```
<!-- TREE-END -->

Run `./lint.sh` to format code and regenerate this project tree snapshot. CI runs the same script on every push/PR.

## Technical Details

### AI Model Selection

The bot automatically selects the most appropriate model based on:

- Required input/output formats
- API parameters support
- Model availability

### Message Processing

1. Message received from Discord user
2. Bot checks if user is already processing a request (prevents spam)
3. Message payload is constructed
4. AI model generates response in a thread pool (non-blocking)
5. Response is sent back to Discord

### Supported Features

- Text-to-text AI generation
- Configurable API endpoints
- Fallback model selection
- Token counting and usage tracking
- Performance timing
- Persistent conversation memory with per-turn deletion

## Dependencies

<!--DEPS-START-->
```markdown
- `discord.py==2.7.1` - A Python wrapper for the Discord API (latest: 2.7.1)
- `python-dotenv==1.2.2` - Read key-value pairs from a .env file and set them as environment variables (latest: 1.2.2)
- `litellm==1.88.1` - Library to easily interface with LLM API providers (latest: 1.88.1)
- `requests==2.34.2` - Python HTTP for Humans. (latest: 2.34.2)
- `colorama==0.4.6` - Cross-platform colored terminal text. (latest: 0.4.6)
- `cairosvg==2.9.0` - A Simple SVG Converter based on Cairo (latest: 2.9.0)
- `Pillow==12.2.0` - Python Imaging Library (fork) (latest: 12.2.0)
- `pilmoji==2.0.5` - Pilmoji is an emoji renderer for Pillow, Python's imaging library. (latest: 2.0.5)
- `microsandbox==0.5.6` - Python SDK for microsandbox — secure, fast microVM-based sandboxing. (latest: 0.5.6)
- `aiohttp==3.14.1` - Async http client/server framework (asyncio) (latest: 3.14.1)
- `discord-webhook==1.4.1` - Easily send Discord webhooks with Python (latest: 1.4.1)
- `cocoindex==1.0.7` - With CocoIndex, users declare the transformation, CocoIndex creates & maintains an index, and keeps the derived index up to date based on source update, with minimal computation and changes. (latest: 1.0.7)
- `fastmcp==3.4.2` - The fast, Pythonic way to build MCP servers and clients. (latest: 3.4.2)
- `pytesseract==0.3.13` - Python-tesseract is a python wrapper for Google's Tesseract-OCR (latest: 0.3.13)
- `pint==0.25.3` - Physical quantities module (latest: 0.25.3)
```
<!--DEPS-END-->

## Development

### Linting & CI

- Project provides `lint.sh` at repo root.
- Run locally before commit:

```bash
./lint.sh
```

- CI: GitHub Actions workflow runs `lint.sh` on `push` and `pull_request` to `master` and feature branches. Fix issues locally and push again.

### Adding New Providers

1. Add provider configuration to `config/providers.json`
2. Set up environment variable for API key
3. Update `config.py` if needed

### Adding New Models

1. Configure the model in `config/models.json`
2. Ensure the provider has the necessary API credentials

### Tests

The project includes comprehensive tests in `scripts/tests/` to ensure code quality and prevent regressions:

- **CodeBlock Tests** (`test_codeblock.py`): Tests for Discord code block handling
- **Config Tests** (`test_config.py`): Tests for configuration loading and validation
- **LaTeX Tests** (`test_latex.py`): Tests for LaTeX rendering and detection
- **Message Tests** (`test_messages.py`): Tests for message processing and formatting
- **Table Tests** (`test_table.py`): Tests for markdown table conversion
- **Model Tests** (`test_models.py`): Tests for model selection and error handling

All tests can be run with:

```bash
python -m pytest scripts/tests/ -v
```

To run specific test modules:

```bash
python -m pytest scripts/tests/test_config.py -v
python -m pytest scripts/tests/test_models.py -v
```

## Important Notes

- The bot ignores messages from other bots and direct messages
- Users cannot send multiple concurrent requests (prevents API overload)
- Message content intent must be enabled for the bot to work
- API keys and tokens should never be committed to version control
- Local memory state lives under `data/memory_state.json` and syncs into a local SQLite store through CocoIndex

## License

This project is provided as-is. Please respect Discord's Terms of Service and API usage policies.

## Contributing

Feel free to submit issues and enhancement requests!
