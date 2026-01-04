#!/bin/bash

echo "=== Nettoyage du projet AlphaLLM ==="

# Supprimer les logs
echo "🧹 Suppression des fichiers de log..."
find . -type f -name "*.log" -exec rm -f {} \;

# Supprimer les datas temporaires
echo "🧹 Suppression des fichiers de données temporaires..."
find . -type f -name "monitoring.csv" -exec rm -f {} \;
find . -type f -name "local_db.db" -exec rm -f {} \;

# Supprimer les caches Python
echo "🧹 Suppression des caches Python..."
find . -type d -name "__pycache__" -exec rm -rf {} \;

# Supprimer les fichiers temporaires
echo "🧹 Suppression des fichiers temporaires..."
find . -type f -name "*.tmp" -exec rm -f {} \;
find . -type f -name "*.temp" -exec rm -f {} \;

# Nettoyer le cache du projet
if [ -d "cache" ]; then
    echo "🧹 Nettoyage du cache du projet..."
    find cache -exec rm -rf {} \;
fi

echo "✅ Nettoyage terminé !"