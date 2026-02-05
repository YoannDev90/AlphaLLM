#!/bin/bash

echo "=== Nettoyage du projet AlphaLLM ==="

# Supprimer les caches Python
echo "🧹 Suppression des caches Python..."
find . -type d -name "__pycache__" -exec rm -rf {} \;

# Supprimer les fichiers temporaires
echo "🧹 Suppression des fichiers temporaires..."
find . -type f -name "*.tmp" -exec rm -f {} \;
find . -type f -name "*.temp" -exec rm -f {} \;

# Supprimer le contenu du dossier 'data' (cache du projet)
echo "🧹 Nettoyage du cache du projet..."
find data -exec rm -rf {} \;

echo "✅ Nettoyage terminé !"