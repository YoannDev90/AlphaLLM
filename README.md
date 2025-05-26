# AlphaLLM - Documentation GitHub 🚀

**AlphaLLM** est un bot Discord écrit en Python, qui regroupe plusieurs APIs:  

- Cerebras AI, un modèle de Llama 3.3 70B ultra-rapide et performant.
- Pollinations AI, un générateur d'images basé sur des modèles de diffusion.
- Mistral AI, un modèle de langage développé par Mistral.
- Gemini AI, un modèle de langage développé par Google.
- OpenRouter, une plateforme pour accéder à divers modèles de langage.
- Markitdown, une librairie pour traiter les fichiers et les liens.
- Crawl4AI, un outil pour crawler et extraire le contenu des liens.
- Discord.py, une librairie pour interagir avec l'API de Discord.
- PostgreSQL, une base de données relationnelle pour stocker les logs et les données.
- Supabase, une plateforme de base de données en temps réel pour stocker les logs et les données.

---

## **Fonctionnalités principales** 🌟

- 🔗 **Traitement des liens** : Remplace automatiquement les liens par leur contenu au format Markdown, avec `Crawl4AI`.
- 📕 **Traitement des fichiers** : Traite les fichiers (PDF, Docx, etc) grâce à la librairie `Markitdown`.
- 📄 **Support Markdown** : Formate ses réponses suivant la syntaxe Markdown de Discord.
- 🖼️ **Génération d'images de qualité** : Génère des images jusqu'à 2048x2048.
- 🔁 **Bouton de régénération** : Régénère la réponse ou l'image.
- ⚠️ **Gestion des erreurs** : Gère les erreurs des différentes API et informe l'utilisateur en conséquence.

---

## **Installation** 🛠️

### Prérequis

1. 🖥️ Python 3.11
2. 🤖 Un bot Discord
3. 🔑 Une clé API pour Cerebras Cloud SDK (obligatoire)
4. 🔑 Une clé API pour Mistral AI (facultatif)
5. 🔑 Une clé API pour Gemini AI (facultatif)
6. 🔑 Une clé API pour OpenRouter (facultatif)
7. 🔑 Une clé API pour Pollinations AI (facultatif)
8. 📦 Une base de données PostgreSQL (optionnel, pour stocker les logs et les données)

### Dépendances
Le projet utilise les dépendances suivantes, qui seront installées automatiquement via le fichier `requirements.txt` :

```txt
# requirements.txt

markitdown[all]
cerebras_cloud_sdk
discord.py
python-dotenv
colorama
asyncpg
crawl4ai
supabase
fastembed
deep_translator
```

### Étapes d'installation

1. Clonez ce dépôt :

   ```bash
   git clone https://github.com/YoannDev90/AlphaLLM.git
   ```

2. Installez les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

3. Configurez vos paramètres dans le fichier `.env` :

   ```venv
   BOT_TOKEN=""                              # Token du bot Discord
   LOGGER_BOT_TOKEN=""                       # Token du bot de log (optionnel, pour les logs en MP en temps réel)
   DEV_BOT_TOKEN=""                          # Token du bot de développement (optionnel, pour les tests)

   DEV_ID=                                   # ID de mon compte Discord
   GALERIE_ID=                               # ID du salon #galerie sur le Discord de AlphaLLM
   GUILD_ID=                                 # ID du serveur Discord AlphaLLM

   CEREBRAS_API_KEY=""                       # Clé API pour Cerebras Cloud SDK
   MISTRAL_API_KEY=""                        # Clé API pour Mistral AI
   GEMINI_API_KEY=""                         # Clé API pour Gemini AI
   OPENROUTER_API_KEY=""                     # Clé API pour OpenRouter
   POLLINATIONS_API_KEY=""                   # Clé API pour Pollinations AI

   DB_URL=""                                 # URL de la base de données (optionnel, pour stocker les logs et les données)
   DB_KEY=""                                 # Clé de la base de données (optionnel)
   JWT_KEY=""                                # Clé JWT pour l'authentification (optionnel)

   DB_DIRECT_CONN=""                         # Connexion directe à la base de données (optionnel, pour la mémoire)
   DB_HOST=                                  # Adresse de la base de données (optionnel)
   DB_PORT=                                  # Port de la base de données (optionnel)
   DB_USER=                                  # Nom d'utilisateur de la base de données (optionnel)
   DB_PASSWORD=                              # Mot de passe de la base de données (optionnel)
   DB_NAME=postgres                          # Nom de la base de données (optionnel)
   ```

4. Lancez le bot :

   ```bash
   python main.py
   ```

---

## **Utilisation** 📚

Pour discuter avec le bot, il suffit de le mentionner dans un canal Discord. Par exemple :

```
@AlphaLLM Quelle est la capitale de la France ?
```

Le bot répondra avec la réponse formatée en Markdown. Vous pouvez également lui envoyer des liens ou des fichiers pour qu'il les traite.

Pour générer une image, utilisez la commande suivante :

`/image` ou `@AlphaLLM generate`.

```
/image "Paysage naturel"
```

```
@AlphaLLM génère une image de paysage naturel.
```

Note : Dans le second cas, le bot se charge d'éditer le prompt et de définir la taille de l'image, ne pas l'utiliser pour des prompts complexes.

---

## **Contributions** 🤝

Les contributions sont les bienvenues ! Veuillez suivre ces étapes :

1. Forkez le dépôt.
2. Créez une branche.
3. Soumettez une Pull Request avec une description claire.

---

## **Support** 📧

Pour toute question ou problème, contactez-nous via [le serveur Discord de support](https://discord.gg/QGvyrUgwdK).

---

Merci d'utiliser AlphaLLM ! 🎮✨
