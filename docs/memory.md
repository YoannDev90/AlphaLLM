# Memory System

## Overview

AlphaLLM features a dual memory system combining short-term and long-term memory for contextual conversations.

## Short-Term Memory (STM)

### Storage
- Uses TinyDB for local JSON storage
- Stores conversation messages per user/channel
- Automatic cleanup (max 50 messages per conversation)

### Structure
```json
{
  "user_id": 123456789,
  "conv_id": "channel_id",
  "content": "Hello world",
  "role": "user",
  "timestamp": 1706745600.0
}
```

### Retrieval
- Fetches last N messages for context
- Configurable via `MAX_CONVERSATION_HISTORY`

## Long-Term Memory (LTM)

### Storage
- Uses Faiss for vector similarity search
- Stores summarized memories and documents

### Retrieval
- Semantic search based on input similarity
- Reranked using LightReranker
- Configurable via `MAX_LTM_RESULTS`

## Memory Integration

### In Prompts
- STM provides recent conversation context
- LTM provides relevant historical information
- Combined for rich, contextual responses

### Automatic Management
- Messages stored after each response
- Periodic summarization (planned)
- Memory limits prevent overflow

## Configuration

```toml
[limits]
max_stm_messages = 50
max_ltm_results = 5
max_conversation_history = 10
```