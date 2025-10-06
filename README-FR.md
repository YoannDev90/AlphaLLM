# AlphaLLM - Documentation GitHub 🚀

## [🇬🇧](https://github.com/YoannDev90/AlphaLLM/blob/main/README.md) / [🇫🇷](https://github.com/YoannDev90/AlphaLLM/blob/main/README-FR.md)

**AlphaLLM** est un bot Discord écrit en Python, qui regroupe plusieurs APIs d'IA:  

- Cerebras
- Pollinations AI
- Mistral AI
- Gemini AI
- OpenRouter
- AI-ML
- Groq
- Navy AI
- Void AI
- Cloudinary
- Cloudflare Workers
- Hackclub AI

---

## **Fonctionnalités principales** 🌟

- 🔗 **Traitement des liens** : Remplace automatiquement les liens par leur contenu au format Markdown, à l'exception du contenu Javascript.
- 📕 **Traitement des fichiers** : Traite les fichiers les plus courants grâce à la librairie `Markitdown`.
- 📄 **Support Markdown** : Formate ses réponses suivant la syntaxe Markdown de Discord.
- ✂️ **Formatage adaptatif** : Formate les blocs de code, les tableaux, les citations, selon la manière la plus adaptée à Discord.
- 🖼️ **Génération d'images de qualité** : Génère des images jusqu'à 2048x2048.
- ✏️ **Edition d'image basique** : Permet l'édition d'une image par l'IA.
- 🔁 **Bouton de régénération** : Régénère la réponse ou l'image.
- ⚙️ **Personnalisation maximale** : Permet de personnaliser le bot pour un usage particulier sur votre serveur, avec possibilité d'ajouter des détails au prompt système de base.
- ⚠️ **Gestion des erreurs** : Gère les erreurs des différentes API et informe l'utilisateur en conséquence.

---

## **Installation** 🛠️

### Prérequis

1. 🖥️ Python 3.11.13
2. 🤖 Un bot Discord
3. 🔑 Une clé pour chaque API
4. 📦 Une base de données PostgreSQL

### Dépendances

Le projet utilise des dépendances qui sont listées dans le fichier `requirements.txt` :


### Étapes d'installation

1. Clonez ce dépôt :

   ```bash
   git clone https://github.com/YoannDev90/AlphaLLM.git
   ```

2. Installez les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

3. Configurez vos paramètres dans le fichier `.env`.

4. Lancez le bot :

   ```bash
   python main.py
   ```

---

## **Utilisation** 📚

Pour discuter avec le bot, il suffit de le mentionner dans un canal Discord autorisé :

@AlphaLLM Quelle est la capitale de la France ?
```md
>>> La capitale de la France est : **Paris** 🗼️.
```

Le bot répondra avec la réponse formatée. Vous pouvez également lui envoyer des liens ou des fichiers pour qu'il les traite.

Pour poser une question ponctuelle, sans contexte, utilisez la commande `/ask` :

`/ask` Quelle est la capitale de la France ?

```md
>>> La capitale de la France est : **Paris** 🗼️.
```

À noter que l'utilisation de cette commande n'a pas d'incidence sur votre historique de conversation.
Cette commande est disponible pour une utilisation sur des serveurs sur lequel le bot n'est pas installé, si toutefois ledit serveur permet l'utilisation de commandes externes.

Pour générer une image, utilisez la commande `/image` :

`/image` "a beautiful natural landscape"

---

## **Contributions** 🤝

Les contributions sont les bienvenues ! Veuillez suivre ces étapes :

1. Forkez le dépôt.
2. Créez une branche.
3. Soumettez une Pull Request avec une description claire.

---

## **Support** 📧

Pour toute question ou problème, contactez-nous via le serveur Discord de support.

---

Merci d'utiliser AlphaLLM ! 🎮✨
