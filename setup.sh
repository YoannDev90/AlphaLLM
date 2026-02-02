#!/bin/bash

echo "=== Configuration initiale du projet AlphaLLM ==="

# Vérifier si Python 3.12+ est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé. Veuillez installer Python 3.12 ou supérieur."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.12"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION détecté. Python $REQUIRED_VERSION ou supérieur est requis."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION détecté."

# Créer l'environnement virtuel
echo "🔧 Création de l'environnement virtuel..."
python3 -m venv .venv

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source .venv/bin/activate

# Mettre à jour pip
echo "🔧 Mise à jour de pip..."
pip install --upgrade pip

# Installer les dépendances
echo "🔧 Installation des dépendances..."
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# Copier les fichiers de configuration
echo "🔧 Configuration des fichiers..."
if [ ! -f config.toml ]; then
    cp config-sample.toml config.toml
    echo "✅ config.toml créé à partir de config-sample.toml"
else
    echo "ℹ️  config.toml existe déjà"
fi

if [ ! -f .env ]; then
    if [ -f .env-sample ]; then
        cp .env-sample .env
        echo "✅ .env créé à partir de .env-sample"
    else
        echo "⚠️  .env-sample non trouvé, créez .env manuellement"
    fi
else
    echo "ℹ️  .env existe déjà"
fi

echo ""
echo "🎉 Configuration terminée !"
echo ""
echo "Prochaines étapes :"
echo "1. Éditez config.toml avec vos paramètres Discord et IA"
echo "2. Éditez .env avec vos clés API"
echo "3. Lancez './run.sh' pour démarrer le bot"
echo ""
echo "Pour nettoyer le projet : ./clean.sh"
echo "Pour relancer la configuration : rm -rf .venv && ./setup.sh"