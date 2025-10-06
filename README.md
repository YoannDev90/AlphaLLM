# AlphaLLM - Documentation GitHub 🚀

## [🇬🇧](https://github.com/YoannDev90/AlphaLLM/main/README.md) / [🇫🇷](https://github.com/YoannDev90/AlphaLLM/main/README-FR.md)

AlphaLLM is a Python-written Discord bot that integrates multiple AI APIs:

- Cerebras
- Pollinations AI
- Mistral AI
- Gemini AI
- OpenRouter
- AI-ML
- Groq
- Navy AI
- Void AI
- Cloudinary
- Cloudflare Workers
- Hackclub AI

---

## **Main Features** 🌟

- 🔗 **Link Processing**: Automatically replaces links with their content in Markdown format, except for JavaScript content.
- 📕 **File Processing**: Handles common file types using the `Markitdown` library.
- 📄 **Markdown Support**: Formats responses using Discord's Markdown syntax.
- ✂️ **Adaptive Formatting**: Formats code blocks, tables, and quotes in the most suitable way for Discord.
- 🖼️ **High-Quality Image Generation**: Generates images up to 2048x2048 resolution.
- ✏️ **Basic Image Editing**: Enables AI-based image editing.
- 🔁 **Regeneration Button**: Regenerates the response or image.
- ⚙️ **Maximum Customization**: Allows customization for specific server use, including the ability to add details to the base system prompt.
- ⚠️ **Error Handling**: Manages errors from different APIs and informs the user accordingly.

---

## **Installation** 🛠️

### Prerequisites

1. 🖥️ Python 3.11.13
2. 🤖 A Discord bot
3. 🔑 An API key for each service
4. 📦 A PostgreSQL database

### Dependencies

Project dependencies are listed in the `requirements.txt` file:

### Installation Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/YoannDev90/AlphaLLM.git
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Configure your settings in the `config.toml` file and your keys in the `.env` file.

6. Launch the bot:

   ```bash
   python main.py
   ```

---

## **Usage** 📚

To chat with the bot, simply mention it in an authorized Discord channel:

@AlphaLLM What is the capital of France?

```md
>>> The capital of France is: **Paris** 🗼️.
```

The bot will respond with a formatted answer. You can also send it links or files for processing.

To ask a one-time question without context, use the `/ask` command:

`/ask` What is the capital of France?

```md
>>> The capital of France is: **Paris** 🗼️.
```

Note that using this command does not affect your conversation history.  
This command is available for use on servers where the bot is not installed, provided the server allows external commands.

To generate an image, use the `/image` command:

`/image` "a beautiful natural landscape"

---

## **Contributions** 🤝

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a branch.
3. Submit a Pull Request with a clear description.

---

## **Support** 📧

For any questions or issues, contact us via the [support Discord server](https://discord.gg/QGvyrUgwdK).

---

Thank you for using AlphaLLM! 🎮✨
