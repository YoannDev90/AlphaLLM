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

# Démarrer en mode développement (avec rechargement automatique si disponible)
echo "🚀 Démarrage en mode développement..."
if command -v uvicorn &> /dev/null; then
    # Si c'est une app FastAPI, utiliser uvicorn avec reload
    echo "🔄 Mode rechargement automatique activé (uvicorn)"
    python -m uvicorn api.api:app --reload --host 0.0.0.0 --port 25692
else
    # Sinon, démarrer normalement
    python main.py
fi