## 🔴 Critique (Architecture & Stabilité)
- Unifier la fonction de génération de texte de l'API et de Discord
- Utiliser une classe pour la mémoire
- Réorganiser les fichiers de /utils (rename+split)

## 🟠 Important (Fonctionnalités API)
- Convertir l'endpoint /text-gen de GET à POST
- Ajouter un paramètre 'files' = [] à l'endpoint /text-gen
- Ajouter des fallbacks sur les modèles d'image

## 🟡 Moyenne (Qualité & Modération)
- Ajouter la modération des images
- Filtrer le NSFW
- Changer de modèle d'embedder

## 🟢 Optionnel (Améliorations)
- Rétablir le logging des traces dans Langfuse
- Nettoyer les modèles d'images inutiles
- Mettre à jour l'endpoint Pollinations
- Ajouter un salon #statut dans Discord