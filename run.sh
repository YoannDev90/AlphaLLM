#!/bin/bash

echo "=== Démarrage d'AlphaLLM ==="

# Vérifier si l'environnement virtuel existe
if [ ! -d ".venv" ]; then
    echo "❌ Environnement virtuel non trouvé. Lancez d'abord './setup.sh'"
    exit 1
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source .venv/bin/activate

# Vérifier si les fichiers de configuration existent
if [ ! -f "config.toml" ]; then
    echo "❌ config.toml non trouvé. Lancez './setup.sh' pour la configuration initiale."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "❌ .env non trouvé. Lancez './setup.sh' pour la configuration initiale."
    exit 1
fi

# Démarrer le bot
echo "🚀 Démarrage du bot..."
python main.py