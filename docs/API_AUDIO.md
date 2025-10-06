# API de Génération Audio - AlphaLLM

Cette documentation décrit l'utilisation de l'API de gén# Génération audio MP3
response = requests.post(
    f"{API_BASE_URL}/generate/audio",
    headers=headers,
    data={
        "text": "Bonjour, comment allez-vous ?",
        "voice": "oliver"
    }
)dio intégrée à AlphaLLM.

## 📋 Aperçu

L'API audio permet de :
- ✅ Convertir du texte en parole (TTS - Text-to-Speech)
- 🎙️ Utiliser différentes voix naturelles disponibles  
- 🎵 Générer des fichiers audio au format MP3

## 🔗 Endpoints Disponibles

### 1. Liste des Voix Disponibles ⭐ PUBLIC

```http
GET /voices
```

**Authentification:** ❌ Non requise (endpoint public)
**Tags:** `info`

**Réponse:**
```json
{
  "status": "success",
  "voices": [
    {
      "id": "oliver",
      "name": "Oliver", 
      "language": "en-US",
      "gender": "male",
      "age": "adult",
      "style": "natural"
    }
  ]
}
```

### 2. Génération Audio MP3 🔐 PROTÉGÉ

```http
POST /generate/audio
```

**Authentification:** ✅ Requise
**Tags:** `generation`

**Paramètres:**
- `text` (requis): Le texte à convertir en audio (max 5000 caractères)
- `voice` (optionnel): ID de la voix à utiliser (défaut: "oliver")

**Headers requis:**
```
Authorization: Bearer YOUR_API_KEY
```

**Exemple de requête:**
```bash
curl -X POST "http://localhost:8000/generate/audio" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d "text=Bonjour, ceci est un test" \
  -d "voice=oliver"
```

**Réponse:**
```json
{
  "status": "success",
  "audio_data": "base64_encoded_mp3_data",
  "format": "mp3"
}
```



## 🐍 Utilisation avec Python

### Exemple Simple

```python
import requests
import base64

API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {"Authorization": f"Bearer {API_KEY}"}

# 1. Récupérer les voix disponibles (public)
voices_response = requests.get(f"{API_BASE_URL}/voices")
voices = voices_response.json()["voices"]
print(f"Voix disponibles: {[v['id'] for v in voices]}")

# 2. Génération audio
response = requests.post(
    f"{API_BASE_URL}/generate/audio",
    headers=headers,
    data={
        "text": "Bonjour, comment allez-vous ?",
        "voice": "oliver",
        "format": "mp3"
    }
)

result = response.json()
if result["status"] == "success":
    # Sauvegarder l'audio
    audio_data = base64.b64decode(result["audio_data"])
    with open("output.mp3", "wb") as f:
        f.write(audio_data)
    print("Audio généré avec succès!")
```

### Exemple avec aiohttp (Asynchrone)

```python
import aiohttp
import asyncio
import base64

async def generate_audio():
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": "Bearer your-api-key"}
        
        # Récupération des voix
        async with session.get("http://localhost:8000/voices") as response:
            voices_data = await response.json()
            print(f"Voix disponibles: {len(voices_data['voices'])}")
        
        # Génération audio MP3
        params = {
            "text": "Texte à convertir en audio",
            "voice": "oliver"
        }
        
        async with session.post(
            "http://localhost:8000/generate/audio",
            headers=headers,
            params=params
        ) as response:
            result = await response.json()
            
            if result["status"] == "success":
                audio_data = base64.b64decode(result["audio_data"])
                with open("output.mp3", "wb") as f:
                    f.write(audio_data)

asyncio.run(generate_audio())
```



## 🌐 Utilisation avec JavaScript/Node.js

```javascript
const axios = require('axios');
const fs = require('fs');

async function generateAudio() {
    try {
        // 1. Récupérer les voix (public)
        const voicesResponse = await axios.get('http://localhost:8000/voices');
        console.log('Voix disponibles:', voicesResponse.data.voices.map(v => v.id));
        
        // 2. Génération audio
        const response = await axios.post(
            'http://localhost:8000/generate/audio',
            new URLSearchParams({
                text: 'Bonjour depuis JavaScript',
                voice: 'oliver'
            }),
            {
                headers: {
                    'Authorization': 'Bearer your-api-key'
                }
            }
        );
        
        if (response.data.status === 'success') {
            const audioBuffer = Buffer.from(response.data.audio_data, 'base64');
            fs.writeFileSync('output.mp3', audioBuffer);
            console.log('Audio généré avec succès !');
        }
    } catch (error) {
        console.error('Erreur:', error.response?.data || error.message);
    }
}

generateAudio();
```

## ⚠️ Gestion des Erreurs

L'API retourne différents codes d'erreur HTTP :

- **400 Bad Request**: Paramètres invalides (texte vide, trop long)
- **401 Unauthorized**: Clé API manquante ou invalide  
- **408 Request Timeout**: Timeout lors de la génération
- **429 Too Many Requests**: Rate limiting dépassé
- **500 Internal Server Error**: Erreur interne du serveur

**Exemple de réponse d'erreur:**
```json
{
  "status": "error",
  "message": "Le texte ne peut pas être vide"
}
```

## 📊 Limites et Configurations

- **📝 Longueur du texte**: Maximum 5000 caractères
- **⏱️ Timeout**: 60 secondes par défaut pour la génération
- **🎵 Format supporté**: MP3 uniquement
- **🚦 Rate limiting**: 10 requêtes par minute par clé API (endpoints protégés)
- **🔐 Authentification**: Requise pour l'endpoint de génération

## 🔧 Variables d'Environnement Requises

```bash
# Clé API Speechify (obligatoire)
SPEECHIFY_API_KEY=your_speechify_api_key

# Clé API AlphaLLM (pour authentification)
API_KEY=your_alphallm_api_key
```

## 🧪 Test de l'API

Un script de test complet est fourni dans `test_audio_api.py` :

```bash
# Configurer la clé API dans le script
python test_audio_api.py
```

Un script d'exemples pratiques dans `example_audio_api.py` :

```bash
python example_audio_api.py
```

Ces scripts testent tous les endpoints et génèrent des fichiers audio d'exemple.



## 🚀 Performance

- ⚡ **Génération audio typique**: 1-3 secondes
- 🔄 **Support asynchrone complet**
- 🌊 **Streaming disponible** pour les gros fichiers
- 💾 **Cache automatique** des voix disponibles
- 📈 **Optimisations mémoire** pour les gros volumes

## 🆘 Support et Dépannage

Pour les problèmes liés à l'API audio, vérifiez :

1. ✅ **Configuration des variables d'environnement**
2. 🌐 **Disponibilité du service Speechify**  
3. 📋 **Logs de l'application** (`logs.log`)

## 📖 Documentation Interactive

- 📚 **Swagger UI**: `http://localhost:8000/docs`
- 📘 **ReDoc**: `http://localhost:8000/redoc`
- ℹ️ **Informations API**: `http://localhost:8000/api/info`

Ces interfaces permettent de tester directement les endpoints avec une interface graphique.

---

🎉 **L'API audio AlphaLLM est prête à transformer vos textes en parole naturelle !**