# AlphaLLM

AlphaLLM est un bot Discord avancé qui intègre plusieurs modèles d'IA pour la génération de texte et d'images. Il offre une API REST, un système de mémoire RAG (Retrieval-Augmented Generation), et des fonctionnalités d'administration.

## Fonctionnalités

- **Bot Discord principal** : Gestion des conversations avec les utilisateurs via Discord
- **Bot administrateur** : Commandes d'administration et de gestion
- **Bot logger** : Surveillance et logging des activités
- **API REST** : Interface programmable pour l'accès aux fonctionnalités
- **Sélection automatique de modèles** : Choix intelligent du meilleur modèle IA selon la requête
- **Système de mémoire RAG** : Mémoire à court et long terme avec embeddings
- **Génération d'images** : Support de multiples modèles de génération d'images
- **Monitoring des ressources** : Suivi de l'utilisation CPU et mémoire
- **Gestion des permissions** : Système de blacklist et canaux autorisés

## Modèles IA supportés

Le bot supporte une vingtaine de modèles d'IA différents :

- **Llama** : Fiable et polyvalent pour les conversations générales
- **OpenAI GPT** : Avancé pour les tâches complexes et le raisonnement profond
- **Mistral** : Équilibré, excellent pour le français
- **Qwen** : Optimisé pour le raisonnement logique et la programmation
- **Gemini** : Rapide et flexible pour les réponses courtes
- **Sonar** : Spécialisé dans la recherche d'informations
- **Et bien d'autres...** (Claude, Grok, DeepSeek, etc.)

## Installation

### Prérequis

- Python 3.12
- Un serveur Discord avec des bots configurés
- Clés API pour les différents services IA

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Configuration

1. Copiez le fichier d'exemple de configuration :
```bash
cp config-sample.toml config.toml
cp .env-sample .env
```

2. Éditez `config.toml` avec vos paramètres :
   - Configurez les IDs Discord (serveurs, canaux, rôles)
   - Ajustez les paramètres de l'API
   - Configurez les modèles de mémoire

3. Éditez `.env` avec vos clés API :
   - Tokens Discord pour les bots
   - Clés API pour les services IA (OpenRouter, Gemini, etc.)
   - Clés pour ChromaDB et Grafana si utilisés

## Utilisation

### Lancement

```bash
python main.py
```

Le programme démarrera automatiquement :
- Le bot principal Discord
- Le bot administrateur
- Le bot logger
- Le serveur API

### Commandes Discord

Le bot répond aux mentions (@AlphaLLM) et aux commandes slash :

- `/ask` : Poser une question à l'IA
- `/commands` : Liste des commandes disponibles
- `/help` : Aide générale
- `/status` : État du bot
- `/history` : Historique des conversations
- `/image_gen` : Génération d'images
- Et bien d'autres...

### API REST

L'API est accessible sur `http://localhost:25692` (configurable).

Endpoints principaux :
- `GET /info` : Informations sur le bot
- `POST /text_gen` : Génération de texte
- `POST /misc` : Fonctions diverses

## Architecture

```
AlphaLLM/
├── main.py                 # Point d'entrée principal
├── config.py              # Chargement de la configuration
├── config.toml            # Configuration TOML
├── bots/                  # Bots Discord
│   ├── bot.py            # Bot principal
│   ├── admin_bot.py      # Bot administrateur
│   └── logger_bot.py     # Bot de logging
├── api/                   # API REST
│   ├── api.py            # Serveur API
│   └── endpoints/        # Endpoints API
├── commands/              # Commandes Discord
├── models/                # Modèles IA
├── utils/                 # Utilitaires
│   ├── memory/           # Système de mémoire RAG
│   └── ai_process/       # Traitement IA
├── configs/               # Configurations diverses
└── cache/                 # Cache des embeddings
```

## Configuration avancée

### Mémoire RAG

Le système utilise ChromaDB pour la mémoire :
- **STM (Short-Term Memory)** : Mémoire à court terme (4h par défaut)
- **LTM (Long-Term Memory)** : Mémoire à long terme avec similarité
- **RAG** : Documents pour le contexte enrichi

### Monitoring

- Logs vers Discord et Grafana Loki
- Monitoring des ressources (CPU, mémoire)
- Export CSV des métriques

### Sécurité

- Vérification des permissions Discord
- Blacklist d'utilisateurs
- Clés API requises pour l'API REST

## Développement

### Structure du code

- **Modulaire** : Chaque fonctionnalité dans son propre module
- **Async/Await** : Programmation asynchrone complète
- **Type hints** : Annotations de types Python
- **Logging structuré** : Logs détaillés avec niveaux configurables

### Ajout d'un nouveau modèle IA

1. Ajoutez la configuration dans `configs/text-models/`
2. Implémentez la classe dans `models/`
3. Ajoutez le modèle dans `config.toml`
4. Mettez à jour le sélecteur de modèles

## Support

- **Serveur Discord** : [Lien d'invitation](https://discord.com/invite/QGvyrUgwdK)
- **Issues GitHub** : Pour les bugs et demandes de fonctionnalités

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Contributeurs

- YoannDev90 (Développeur principal)

---