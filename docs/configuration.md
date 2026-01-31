# Configuration

## Files

### config.toml
Main configuration file with sections for different components.

### .env
Environment variables for API keys and secrets.

## Key Sections

### [config]
```toml
debug = false
dev_id = [1123534156626939945]
admin_server = 1327996079786168441
```

### [api]
```toml
host = "0.0.0.0"
port = 25692
ssl_certfile = "certfile.pem"
ssl_keyfile = "keyfile.pem"
api_key_required = false
```

### [models]
List of available models with descriptions.

### [limits]
```toml
max_stm_messages = 50
max_ltm_results = 5
max_conversation_history = 10
api_rate_limit = 100
discord_rate_limit = 30
```

### [memory]
```toml
embedder_model = "sentence-transformers/all-MiniLM-L6-v2"
function_calling_model = "google/functiongemma-270m-it"
```

## Environment Variables

### Bot Tokens
```
BOT_TOKEN=your_discord_bot_token
ADMIN_BOT_TOKEN=your_admin_bot_token
LOGGER_BOT_TOKEN=your_logger_bot_token
```

### API Keys
```
CEREBRAS_API_KEY=...
GROQ_API_KEY=...
OPENAI_API_KEY=...
# etc.
```

## Database
- Local SQLite for permissions and settings
- TinyDB for conversation memory
- PostgreSQL for production data

## Logging
- Configurable levels
- Loki/Grafana integration
- Discord logging channel