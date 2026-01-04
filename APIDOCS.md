# AlphaLLM API Documentation

## Vue d'ensemble

L'API AlphaLLM est une interface REST complète pour accéder aux fonctionnalités d'AlphaLLM. Elle fournit des endpoints pour la génération de texte, la génération et l'édition d'images, ainsi que diverses utilitaires.

**Version de l'API :** 2.0.0  
**Base URL :** `http://localhost:25692` (configurable)  
**Authentification :** Clé API (optionnelle selon configuration)

## Authentification

L'API supporte plusieurs méthodes d'authentification :

- **Header X-API-Key :** `X-API-Key: votre_clé_api`
- **Header Authorization :** `Authorization: Bearer votre_clé_api`
- **Paramètre de requête :** `?api_key=votre_clé_api`

L'authentification peut être désactivée dans la configuration (`api_key_required = false`).

## Endpoints

### Informations générales

#### GET /
Point d'entrée principal de l'API.

**Réponse :**
```json
{
  "message": "AlphaLLM API",
  "version": "2.0.0",
  "HTTP": "running",
  "HTTPS": "running|stopped|timeout",
  "authenticated": false,
  "client_ip": "adresse_ip"
}
```

#### GET /status
Vérification du statut du système.

**Réponse :**
```json
{
  "status": "ok",
  "timestamp": "2024-01-04T12:00:00",
  "version": "2.0.0",
  "uptime": "1 day, 2:30:45"
}
```

#### GET /resources
Données de monitoring des ressources système (dernières 24h).

**Réponse :**
```json
{
  "data": [
    {
      "timestamp": "2024-01-04T12:00:00",
      "cpu_percent": 45.2,
      "memory_percent": 67.8
    }
  ],
  "total_points": 1440
}
```

### Modèles disponibles

#### GET /text/models
Liste des modèles de texte disponibles.

**Réponse :**
```json
{
  "status": "success",
  "count": 25,
  "models": [
    "llama",
    "openai",
    "mistral",
    "qwen",
    "gemini",
    "sonar",
    "evilgpt",
    "grok",
    "claude",
    "kimi",
    "deepseek",
    "glm",
    "phi",
    "cohere",
    "minimax",
    "nemotron",
    "mercury",
    "yi",
    "hermes",
    "longcat",
    "seed",
    "granite",
    "rocinante",
    "hunyuan",
    "jamba"
  ],
  "default_model": "auto"
}
```

#### GET /image/models
Liste des modèles d'image disponibles.

**Réponse :**
```json
{
  "status": "success",
  "count": 8,
  "models": [
    "flux",
    "gptimage",
    "kontext",
    "nanobanana",
    "seedream",
    "zimage"
  ],
  "default_model": "flux"
}
```

### Génération de texte

#### POST /text/generation
Génère du texte à partir d'un prompt.

**Paramètres (form-data) :**
- `prompt` (string, requis) : Le prompt de génération
- `model` (string, optionnel) : Modèle à utiliser (défaut: "auto")
- `user_id` (integer, requis) : ID de l'utilisateur
- `conv_id` (integer, requis) : ID de la conversation
- `stream` (boolean, optionnel) : Streaming activé (défaut: false)
- `files` (file, optionnel) : Fichiers à analyser

**Exemple de requête :**
```bash
curl -X POST "http://localhost:25692/text/generation" \
  -H "X-API-Key: votre_clé" \
  -F "prompt=Explique-moi comment fonctionne l'IA" \
  -F "user_id=12345" \
  -F "conv_id=67890" \
  -F "model=auto"
```

**Réponse (stream=false) :**
```
Texte généré par l'IA...
```

**Réponse (stream=true) :**
```
Chunk 1 du texte...
Chunk 2 du texte...
...
```

#### POST /text/conv_name
Génère un titre pour une conversation.

**Paramètres JSON :**
```json
{
  "messages": [
    {"role": "user", "content": "Bonjour"},
    {"role": "assistant", "content": "Bonjour ! Comment puis-je vous aider ?"}
  ]
}
```

**Réponse :**
```json
{
  "status": "success",
  "title": "Discussion générale",
  "metadata": {
    "processing_time": 1.23,
    "total_chars": 45
  }
}
```

#### POST /text/summarize
Résume un texte donné.

**Paramètres JSON :**
```json
{
  "input_text": "Texte à résumer...",
  "max_length": 150
}
```

**Réponse :**
```json
{
  "status": "success",
  "summary": "Résumé du texte...",
  "metadata": {
    "original_length": 1000,
    "summary_length": 120,
    "max_length": 150,
    "processing_time": 2.34
  }
}
```

### Génération d'images

#### POST /image/generation
Génère des images à partir d'un prompt.

**Paramètres (form-data) :**
- `prompt` (string, requis) : Description de l'image
- `model` (string, optionnel) : Modèle à utiliser (défaut: "flux")
- `num_images` (integer, optionnel) : Nombre d'images (défaut: 1)
- `size` (string, optionnel) : Taille (défaut: "1024x1024")
- `enhance` (boolean, optionnel) : Amélioration automatique (défaut: true)
- `user_id` (integer, requis) : ID de l'utilisateur

**Réponse :**
```json
{
  "images": ["base64_image_data_1", "base64_image_data_2"],
  "models": ["flux", "flux"]
}
```

#### POST /image/edit
Édite une image existante avec un prompt.

**Paramètres (form-data) :**
- `prompt` (string, requis) : Instructions d'édition
- `model` (string, optionnel) : Modèle à utiliser (défaut: "gptimage")
- `num_images` (integer, optionnel) : Nombre d'images (défaut: 1)
- `enhance` (boolean, optionnel) : Amélioration automatique (défaut: true)
- `image` (file, requis) : Image à éditer
- `user_id` (integer, requis) : ID de l'utilisateur

**Réponse :**
```json
{
  "images": ["base64_edited_image"],
  "models": ["gptimage"]
}
```

### Transformations d'images

#### POST /image/improve
Améliore les couleurs, le contraste et l'éclairage d'une image.

**Paramètres (form-data) :**
- `image` (file, requis) : Image à améliorer
- `user_id` (integer, requis) : ID de l'utilisateur

**Réponse :**
```json
{
  "image": "base64_improved_image"
}
```

#### POST /image/enhance
Améliore la qualité générale d'une image.

**Paramètres (form-data) :**
- `image` (file, requis) : Image à améliorer
- `user_id` (integer, requis) : ID de l'utilisateur

**Réponse :**
```json
{
  "image": "base64_enhanced_image"
}
```

#### POST /image/auto_enhance
Amélioration automatique intelligente de l'image.

**Paramètres (form-data) :**
- `image` (file, requis) : Image à améliorer
- `user_id` (integer, requis) : ID de l'utilisateur

**Réponse :**
```json
{
  "image": "base64_auto_enhanced_image"
}
```

#### POST /image/upscale
Augmente la résolution d'une image.

**Paramètres (form-data) :**
- `image` (file, requis) : Image à agrandir
- `user_id` (integer, requis) : ID de l'utilisateur

**Réponse :**
```json
{
  "image": "base64_upscaled_image"
}
```

#### POST /image/generative_restore
Restauration générative d'une image dégradée.

**Paramètres (form-data) :**
- `image` (file, requis) : Image à restaurer
- `user_id` (integer, requis) : ID de l'utilisateur

**Réponse :**
```json
{
  "image": "base64_restored_image"
}
```

#### POST /image/remove_background
Supprime l'arrière-plan d'une image.

**Paramètres (form-data) :**
- `image` (file, requis) : Image source
- `user_id` (integer, requis) : ID de l'utilisateur

**Réponse :**
```json
{
  "image": "base64_image_without_background"
}
```

## Codes d'erreur

### Erreurs HTTP communes

- **400 Bad Request** : Paramètres invalides ou manquants
- **401 Unauthorized** : Clé API manquante ou invalide
- **403 Forbidden** : Accès refusé
- **404 Not Found** : Endpoint inexistant
- **500 Internal Server Error** : Erreur serveur

### Erreurs spécifiques

```json
{
  "detail": "Description de l'erreur"
}
```

## Limites et quotas

- **Taille maximale des fichiers :** 10MB par image
- **Nombre maximum d'images :** 4 par génération
- **Longueur maximale du prompt :** 2000 caractères
- **Temps d'attente maximum :** 300 secondes par requête

## Exemples d'utilisation

### Python avec requests

```python
import requests

# Configuration
API_URL = "http://localhost:25692"
API_KEY = "votre_clé_api"

headers = {"X-API-Key": API_KEY}

# Génération de texte
response = requests.post(
    f"{API_URL}/text/generation",
    headers=headers,
    data={
        "prompt": "Explique-moi l'apprentissage automatique",
        "user_id": 12345,
        "conv_id": 67890,
        "model": "auto"
    }
)

print(response.text)

# Génération d'image
response = requests.post(
    f"{API_URL}/image/generation",
    headers=headers,
    data={
        "prompt": "Un chaton jouant dans l'herbe",
        "user_id": 12345,
        "num_images": 1,
        "size": "1024x1024"
    }
)

images = response.json()
print(f"Images générées: {len(images['images'])}")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');
const FormData = require('form-data');

const API_URL = 'http://localhost:25692';
const API_KEY = 'votre_clé_api';

// Génération de texte
const textResponse = await axios.post(`${API_URL}/text/generation`, {
  prompt: 'Bonjour, comment allez-vous ?',
  user_id: 12345,
  conv_id: 67890
}, {
  headers: { 'X-API-Key': API_KEY }
});

console.log(textResponse.data);

// Génération d'image
const formData = new FormData();
formData.append('prompt', 'Un paysage montagneux');
formData.append('user_id', '12345');

const imageResponse = await axios.post(`${API_URL}/image/generation`, formData, {
  headers: {
    'X-API-Key': API_KEY,
    ...formData.getHeaders()
  }
});

console.log(`Images: ${imageResponse.data.images.length}`);
```

## Webhooks et callbacks

L'API ne supporte pas actuellement les webhooks natifs. Pour les traitements asynchrones longs, utilisez le streaming ou implémentez votre propre système de polling.

## Support et contact

- **Documentation interactive :** `/docs` (Swagger UI)
- **Documentation alternative :** `/redoc` (ReDoc)
- **Serveur Discord :** [Lien d'invitation](https://discord.com/invite/QGvyrUgwdK)
- **Issues GitHub :** Pour signaler des bugs ou demander des fonctionnalités
</content>
