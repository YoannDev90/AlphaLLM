#!/bin/bash

echo "=== Mode développement AlphaLLM ==="

# Vérifier si l'environnement virtuel existe
if [ ! -d ".venv" ]; then
    echo "❌ Environnement virtuel non trouvé. Lancez d'abord './setup.sh'"
    exit 1
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source .venv/bin/activate

# Installer les dépendances de développement si requirements-dev.txt existe
if [ -f "requirements-dev.txt" ]; then
    echo "🔧 Installation des dépendances de développement..."
    pip install -r requirements-dev.txt
fi

# Démarrer en mode développement
echo "🚀 Démarrage en mode développement..."
python main.py