# Architecture

## Overview

AlphaLLM is a Discord bot with REST API capabilities, featuring advanced AI model integration and memory management.

## Components

### 🤖 Discord Bots
- **Main Bot**: Handles user interactions, text/image generation
- **Admin Bot**: Administrative functions
- **Logger Bot**: Logging and monitoring

### 🌐 API Server
- REST API for external integrations
- Supports text and image generation
- Rate limiting and authentication

### 🧠 Memory System
- **STM (Short-Term Memory)**: Conversation history stored in TinyDB
- **LTM (Long-Term Memory)**: Semantic search using Faiss
- Automatic summarization for memory efficiency

### 🎯 AI Integration
- Multi-provider support (OpenAI, Anthropic, Google, etc.)
- Automatic model selection
- Fallback mechanisms
- Streaming responses

### 📊 Monitoring
- Resource monitoring
- Performance tracking
- Error logging

## Data Flow

```
User Input → Permission Check → Model Selection → Memory Retrieval → AI Generation → Response → Memory Storage
```

## Key Technologies

- **Python 3.12+**
- **Discord.py** for bot interactions
- **FastAPI** for REST API
- **TinyDB** for local JSON storage
- **Faiss** for vector search
- **LiteLLM** for unified AI API access