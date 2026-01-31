# API Reference

## Overview

AlphaLLM provides a REST API for programmatic access to AI generation capabilities.

## Base URL
```
https://api.alphallm.tech/
```

## Authentication
- API key required (configurable)
- Header: `Authorization: Bearer YOUR_API_KEY`

## Endpoints

### POST /generate/text
Generate text using AI models.

**Request:**
```json
{
  "prompt": "Hello world",
  "model": "auto",
  "stream": false,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "response": "Hello! How can I help you today?",
  "model": "llama",
  "usage": 150,
  "elapsed_time": "1.2 seconds"
}
```

### POST /generate/image
Generate images.

**Request:**
```json
{
  "prompt": "A beautiful sunset",
  "model": "auto"
}
```

**Response:**
```json
{
  "image_url": "https://...",
  "model": "flux"
}
```

### GET /status
Check API status.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime": "2h 30m"
}
```

## Rate Limiting
- Configurable per endpoint
- Headers indicate limits and remaining requests

## Error Handling
- 400: Bad Request
- 401: Unauthorized
- 429: Rate Limited
- 500: Internal Server Error

## Streaming
- Supported for text generation
- Server-sent events format
- `stream: true` in request