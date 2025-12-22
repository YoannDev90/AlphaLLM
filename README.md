# AlphaLLM

[![GitHub stars](https://img.shields.io/github/stars/YoannDev90/AlphaLLM?style=flat-square)](https://github.com/YoannDev90/AlphaLLM/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/YoannDev90/AlphaLLM?style=flat-square)](https://github.com/YoannDev90/AlphaLLM/issues)
[![GitHub license](https://img.shields.io/github/license/YoannDev90/AlphaLLM?style=flat-square&type=mit)](https://github.com/YoannDev90/AlphaLLM/blob/dev/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue?style=flat-square)](https://www.python.org/downloads/)
[![Discord](https://img.shields.io/discord/1327996079786168441?color=blue&label=Discord&logo=discord&style=flat-square)](https://discord.com/invite/QGvyrUgwdK)

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

## 🚀 Utilisation

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

Endpoints principaux :
- ℹ️ `GET /info` : Informations sur le bot
- 📝 `POST /text_gen` : Génération de texte
- 🔧 `POST /misc` : Fonctions diverses

## Architecture du Projet

```
AlphaLLM/
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

## 🛠️ Développement

### Structure du code

- 🧩 **Modulaire** : Chaque fonctionnalité dans son propre module
- ⚡ **Async/Await** : Programmation asynchrone complète
- 📝 **Type hints** : Annotations de types Python
- 📋 **Logging structuré** : Logs détaillés avec niveaux configurables

### Ajout d'un nouveau modèle IA

1. ➕ Ajoutez la configuration dans `configs/text-models/`
2. 🏗️ Implémentez la classe dans `models/`
3. ⚙️ Ajoutez le modèle dans `config.toml`
4. 🎯 Mettez à jour le sélecteur de modèles

## 🆘 Support

- 💬 **Serveur Discord** : [Lien d'invitation](https://discord.com/invite/QGvyrUgwdK)
- 🐛 **Issues GitHub** : Pour les bugs et demandes de fonctionnalités

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 👥 Contributeurs

- 👨‍💻 YoannDev90 (Développeur principal)

---
