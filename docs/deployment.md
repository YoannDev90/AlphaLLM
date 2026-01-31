# Deployment

## Prerequisites

- Python 3.12+
- 2GB RAM minimum
- 5GB disk space
- API keys for AI providers

## Installation

1. **Clone repository:**
   ```bash
   git clone https://github.com/YoannDev90/AlphaLLM.git
   cd AlphaLLM
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure:**
   - Copy `config-sample.toml` to `config.toml`
   - Edit `config.toml` with your settings
   - Create `.env` with API keys

5. **Run:**
   ```bash
   python main.py
   ```

## Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 25692

CMD ["python", "main.py"]
```

## Production Setup

- Use PostgreSQL instead of SQLite
- Set up SSL certificates
- Configure reverse proxy (nginx)
- Enable monitoring
- Set up log aggregation

## Code Quality

Before committing:
```bash
black . && isort . && flake8 .
```

## Troubleshooting

- Check logs in `data/bot.log`
- Verify API keys
- Ensure database connectivity
- Check Discord bot permissions