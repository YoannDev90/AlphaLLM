# AlphaLLM

[![GitHub stars](https://img.shields.io/github/stars/YoannDev90/AlphaLLM?style=flat-square)](https://github.com/YoannDev90/AlphaLLM/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/YoannDev90/AlphaLLM?style=flat-square)](https://github.com/YoannDev90/AlphaLLM/issues)
[![GitHub license](https://img.shields.io/github/license/YoannDev90/AlphaLLM?style=flat-square&type=mit)](https://github.com/YoannDev90/AlphaLLM/blob/dev/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue?style=flat-square)](https://www.python.org/downloads/)
[![Discord](https://img.shields.io/discord/1327996079786168441?color=blue&label=Discord&logo=discord&style=flat-square)](https://discord.com/invite/QGvyrUgwdK)

![Alt](https://repobeats.axiom.co/api/embed/d1ef951054604efff035919fef4255170881619b.svg "Repobeats analytics image")

AlphaLLM est un bot Discord avancé qui intègre plusieurs modèles d'IA pour la génération de texte et d'images. Il offre une API REST, un système de mémoire RAG (Retrieval-Augmented Generation), et des fonctionnalités d'administration.

## 🚀 Fonctionnalités

- **🤖 Bot Discord principal** : Gestion des conversations avec les utilisateurs via Discord
- **👑 Bot administrateur** : Commandes d'administration et de gestion
- **📊 Bot logger** : Surveillance et logging des activités
- **🌐 API REST** : Interface programmable pour l'accès aux fonctionnalités
- **🎯 Sélection automatique de modèles** : Choix intelligent du meilleur modèle IA selon la requête
- **🧠 Système de mémoire RAG** : Mémoire à court et long terme avec embeddings
- **🎨 Génération d'images** : Support de multiples modèles de génération d'images
- **📈 Monitoring des ressources** : Suivi de l'utilisation CPU et mémoire
- **🔒 Gestion des permissions** : Système de blacklist et canaux autorisés
- **🗃️ Gestion de fichiers/URLs/LaTeX** : Parsing intelligent et formatage propre pour Discord

## 🤖 Modèles IA supportés

Le bot supporte **25 modèles d'IA** différents :

- **🦙 Llama** : Fiable et polyvalent pour les conversations générales
- **🧠 OpenAI GPT** : Avancé pour les tâches complexes et le raisonnement profond
- **🌪️ Mistral** : Équilibré, excellent pour le français
- **🧩 Qwen** : Optimisé pour le raisonnement logique et la programmation
- **⚡ Gemini** : Rapide et flexible pour les réponses courtes
- **🔍 Sonar** : Spécialisé dans la recherche d'informations
- **😈 EvilGPT** : Non filtré et créatif pour le contenu expérimental
- **🚀 Grok** : Humoristique et casual pour les conversations légères
- **📖 Claude** : Poétique et créatif pour l'écriture littéraire
- **🎓 Kimi** : Clair et pédagogique pour l'éducation
- **📜 DeepSeek** : Fort pour le contenu long et structuré
- **🌏 GLM** : Excellent support multilingue
- **💡 Phi** : Léger et efficace pour les requêtes simples
- **🧮 Cohere** : Puissant en logique et raisonnement analytique
- **🔬 Minimax** : Modèle multi-modal avancé
- **👁️ Nemotron** : Optimisé pour les workflows agentiques et vision
- **⚡ Mercury** : Ultra-rapide basé sur diffusion
- **🌟 Yi** : Multimodal bilingue fort en codage et maths
- **🛡️ Hermes** : Série open-source avec fort raisonnement
- **🐱 LongCat** : Mixture-of-Experts efficace
- **🌱 Seed** : Multimodal avancé de ByteDance
- **🏔️ Granite** : Modèle open efficace d'IBM
- **📚 Rocinante** : Pour l'écriture créative et contenu professionnel
- **📝 Hunyuan** : Modèle de texte avancé de Tencent
- **🎭 Jamba** : Multimodal équilibré pour tâches créatives

## 📦 Installation

### Prérequis

- 🐍 Python 3.12+
- 🤖 Un serveur Discord avec des bots configurés
- 🔑 Clés API pour les différents services IA

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Configuration

1. 📋 Copiez le fichier d'exemple de configuration :
```bash
cp config-sample.toml config.toml
cp .env-sample .env
```

2. ⚙️ Éditez `config.toml` avec vos paramètres :
   - Configurez les IDs Discord (serveurs, canaux, rôles)
   - Ajustez les paramètres de l'API
   - Configurez les modèles de mémoire

3. 🔐 Éditez `.env` avec vos clés API :
   - Tokens Discord pour les bots
   - Clés API pour les services IA (OpenRouter, Gemini, etc.)
   - Clés pour ChromaDB et Grafana si utilisés

## 🔧 Workflows Locaux

Le projet inclut des scripts shell pour faciliter la gestion locale :

### Configuration initiale
```bash
./setup.sh
```
- Vérifie les prérequis (Python 3.12+)
- Crée et configure l'environnement virtuel
- Installe les dépendances
- Copie les fichiers de configuration d'exemple

### Démarrage du bot
```bash
./run.sh
```
- Active l'environnement virtuel
- Vérifie la configuration
- Lance `python main.py`

### Mode développement
```bash
./dev.sh
```
- Lance le bot en mode développement
- Recharge automatiquement en cas de modification (si uvicorn disponible)

### Nettoyage du projet
```bash
./clean.sh
```
- Supprime les logs, caches Python et fichiers temporaires
- Nettoie le dossier cache (préserve les modèles embedder)

## �🚀 Utilisation

### Lancement

```bash
python main.py
```

Le programme démarrera automatiquement :
- 🤖 Le bot principal Discord
- 👑 Le bot administrateur
- 📊 Le bot logger
- 🌐 Le serveur API

### Commandes Discord

Le bot répond aux mentions (@AlphaLLM) et aux commandes slash :

- ❓ `/ask` : Poser une question à l'IA
- 📋 `/commands` : Liste des commandes disponibles
- ❓ `/help-bot` : Aide générale
- 📊 `/ping` : Latence du bot
- 🎨 `/image-gen` : Génération d'images
- 🖍️ `/image-edit` : Edition d'images
- ⚙️ `/guild-config` : Configuration des paramètres du serveur
- 🆘 `/support` : Lien vers le serveur de support
- 💬 `/contact-dev` : Contacter le développeur
- 🧹 `/clear-history` : Réinitialiser l'historique de conversation
- 📈 `/resources` : Afficher l'utilisation des ressources système

### Commandes administrateur

Le bot administrateur dispose des commandes suivantes (réservées aux administrateurs) :

- 🔄 `/restart` : Redémarrer le bot
- 🚪 `/leave` : Faire quitter le bot d'un serveur
- ℹ️ `/guild-info` : Afficher les informations d'un serveur
- 🛑 `/stop` : Arrêter le bot
- 📊 `/poll` : Créer et envoyer un sondage sur tous les serveurs
- 📢 `/announce` : Annoncer un message sur tous les serveurs
- 💬 `/reply` : Répondre à un utilisateur via DM
- 🏠 `/guilds` : Afficher la liste des serveurs où le bot est présent
- 🚫 `/blacklist` : Ajouter un utilisateur à la blacklist
- 🧹 `/clear` : Purger tous les messages DM sans limite de temps

### Commandes du bot logger

- 📝 `/clear-logs` : Effacer le canal de logs et en créer un nouveau

### API REST

L'API est accessible sur `http://localhost:25692` (configurable).

**Documentation complète :** [APIDOCS.md](APIDOCS.md)

Endpoints principaux :
- ℹ️ `GET /info` : Informations sur le bot
- 📝 `POST /text/generation` : Génération de texte
- 🎨 `POST /image/generation` : Génération d'images
- 🖍️ `POST /image/edit` : Édition d'images
- 🔧 `POST /misc` : Fonctions diverses

**Documentation interactive :**
- Swagger UI : `http://localhost:25692/docs`
- ReDoc : `http://localhost:25692/redoc`

## 💡 Exemples d'utilisation

### Utilisation basique

```python
import requests

# Configuration
API_URL = "http://localhost:25692"
API_KEY = "votre_clé_api"

# Génération de texte
response = requests.post(
    f"{API_URL}/text/generation",
    headers={"X-API-Key": API_KEY},
    data={
        "prompt": "Explique-moi l'IA en termes simples",
        "user_id": 12345,
        "conv_id": 67890
    }
)

print(response.text)
```
### Génération d'images

```python
import base64
from PIL import Image
import io

# Génération d'image
response = requests.post(
    f"{API_URL}/image/generation",
    headers={"X-API-Key": API_KEY},
    data={
        "prompt": "Un paysage futuriste avec des robots",
        "user_id": 12345,
        "num_images": 1
    }
)

image_data = response.json()["images"][0]
image = Image.open(io.BytesIO(base64.b64decode(image_data)))
image.save("generated_image.png")
```

## Architecture du Projet

```
AlphaLLM/
├── setup.sh
├── run.sh
├── dev.sh
├── clean.sh
├── main.py
├── config.py
├── config.toml
├── logger.py
├── bots/
│   ├── bot.py
│   ├── admin_bot.py
│   └── logger_bot.py
│   └── commands/
│       ├── cmds.py
│       ├── admin_commands/
│       └── commands/
├── api/
│   ├── api.py
│   ├── endpoints/
│   │   ├── main.py
│   │   ├── text_gen.py
│   │   ├── image_models.py
│   │   ├── summarize.py
│   │   ├── conv_name.py
│   │   ├── resources.py
│   │   └── status.py
│   └── api_utils/
│       ├── app_config.py
│       ├── models_utils.py
│       ├── security_utils.py
│       └── server_utils.py
├── models/
│   ├── text_models.json
│   ├── image_models.json
│   └── image/
│       ├── flux.py
│       ├── gptimage.py
│       └── ...
├── utils/
│   ├── ressources.py
│   ├── unified_image.py
│   ├── unified_text.py
│   ├── ai_process/
│   │   ├── ai_utils.py
│   │   ├── base_chat_model.py
│   │   ├── chat_model.py
│   │   └── llm_selector.py
│   ├── database/
│   │   ├── blacklist.py
│   │   ├── db_manager.py
│   │   ├── perms_conf.py
│   │   ├── server_conf.py
│   │   └── user_conf.py
│   ├── discord_utils/
│   │   ├── commands_ids.py
│   │   ├── permission_checker.py
│   │   └── status.py
│   ├── handlers/
│   │   ├── files.py
│   │   ├── markdown.py
│   │   ├── table.py
│   │   └── vision.py
│   ├── memory/
│   │   ├── base.py
│   │   ├── chroma_manager.py
│   │   ├── embedder.py
│   │   ├── manager.py
│   │   └── rag_handler.py
│   └── views/
│       ├── channels.py
│       └── roles.py
├── configs/
│   ├── misc/
│   │   ├── conv_name.json
│   │   ├── img_enhancer.json
│   │   └── summarizer.json
│   ├── prompts/
│   │   ├── api_prompt.txt
│   │   ├── conv_name.txt
│   │   ├── discord_prompt.txt
│   │   ├── img_enhancer.txt
│   │   └── llm_selector.txt
│   └── text-models/
│       ├── claude.json
│       ├── cohere.json
│       ├── deepseek.json
│       └── ...
├── cache/
│   └── embedder/
└── monitoring.csv
```

### Flux de données

1. 📥 **Entrée utilisateur** : Via Discord (mentions/commands) ou API REST
2. 🎯 **Traitement** : Sélection du modèle IA approprié via `llm_selector.py`
3. 🧠 **Mémoire** : Récupération du contexte via système RAG (`memory/`)
4. 🤖 **Génération** : Appel au modèle IA sélectionné
5. 📤 **Sortie** : Réponse formatée via handlers appropriés

## ⚙️ Configuration avancée

### Mémoire RAG

Le système utilise ChromaDB pour la mémoire :
- 🕒 **STM (Short-Term Memory)** : Mémoire à court terme (4h par défaut)
- 🗂️ **LTM (Long-Term Memory)** : Mémoire à long terme avec similarité
- 📚 **RAG** : Documents pour le contexte enrichi

### Monitoring

- 📊 Logs vers Discord et Grafana Loki
- 💻 Monitoring des ressources (CPU, mémoire)
- 📈 Export CSV des métriques

### Sécurité

- ✅ Vérification des permissions Discord
- 🚫 Blacklist d'utilisateurs
- 🔑 Clés API requises pour l'API REST
- 🛡️ Validation des entrées utilisateur
- 📊 Logging sécurisé sans exposition des secrets

## 🛠️ Développement

### Structure du code

- 🧩 **Modulaire** : Chaque fonctionnalité dans son propre module
- ⚡ **Async/Await** : Programmation asynchrone complète
- 📝 **Type hints** : Annotations de types Python
- 📋 **Logging structuré** : Logs détaillés avec niveaux configurables

### Ajout d'un nouveau modèle IA

1. ➕ Ajoutez la configuration dans `configs/text-models/`
2. 🏗️ Implémentez la classe dans `models/text/`
3. ⚙️ Ajoutez le modèle dans `config.toml`
4. 🎯 Mettez à jour le sélecteur de modèles dans `utils/ai_process/llm_selector.py`

## 🐛 Dépannage

### Problèmes courants

**Erreur "Clé API manquante"**
```bash
cat .env
./clean.sh && ./run.sh
```

**Erreur "Port déjà utilisé"**
```bash
sudo lsof -ti:25692 | xargs kill -9
```

### Logs et debugging

Les logs sont disponibles dans :
- Console du terminal
- Fichiers `.log` dans le répertoire racine
- Canal Discord de logs (si configuré)
- Grafana Loki (si configuré)

Niveaux de logging : `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## 📊 Métriques et monitoring

### Métriques collectées

- 📈 Utilisation CPU et mémoire
- ⏱️ Temps de réponse des APIs
- 📊 Nombre de requêtes par heure
- 🔄 Taux d'erreur par endpoint

### Visualisation

- **Grafana** : Tableaux de bord en temps réel
- **CSV export** : `monitoring.csv` pour analyse
- **API endpoints** : `/status`, `/resources`

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 👥 Contributeurs

- 👨‍💻 **YoannDev90** (Développeur principal)

## 🙏 Remerciements

- 🤖 Communauté des modèles d'IA open-source
- 📚 Documentation FastAPI et Discord.py
- 🛠️ Outils de développement Python

