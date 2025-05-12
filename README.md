# AlphaLLM - Documentation GitHub 🚀

**AlphaLLM** est un bot Discord écrit en Python, qui regroupe plusieurs APIs, ainsi que des projets non-officiels:  

- Cerebras AI, un modèle de Llama 3.3 70B ultra-rapide et performant.
- Pollinations AI, un générateur d'images basé sur des modèles de diffusion.

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
3. 🔑 Une clé API pour Cerebras Cloud SDK

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
    DISCORD_TOKEN=""
    CEREBRAS_API_KEY=""
   ```

4. Lancez le bot :

   ```bash
   python main.py
   ```

---

## **Utilisation** 📚

### Commandes principales

1. **Mentionner le bot**
   Mentionnez le bot dans un message ou une réponse avec une question :

   ```text
   @AlphaLLM Peux-tu m'aider avec une commande Linux ?
   ```

   ![image](https://github.com/user-attachments/assets/0f8bb424-f475-4ff9-ad21-fdfc3ba9e1e7)


2. **Générer une image**
   Exemple avec tous les paramètres disponibles :

   ```text
   /image prompt:'A minecraft landscape, plains biome, voxel, blocky style, smooth shaders, blocky trees' model:[] width:2048 height:1024 nologo:True private:True enhance:False safe:True
   ```
   
   ![image](https://github.com/user-attachments/assets/263e4a5a-abcb-437d-8a52-26c58c380ebf)
   ![image](https://github.com/user-attachments/assets/8a1ee898-480e-4d15-bccb-c733b2743d15)
   ![image](https://github.com/user-attachments/assets/cf9c6985-6e81-4bf1-be8b-527527bd8269)
   ![image](https://github.com/user-attachments/assets/5e964ae0-8f8f-4210-8780-1bc6bb3ab545)
   ![image](https://github.com/user-attachments/assets/a295e027-b6b9-45d2-b214-0985377d33bd)
   ![image](https://github.com/user-attachments/assets/54539ba1-d086-4fe4-8ba3-abfbd1da1bed)

  Tous les paramètres à l'exception du prompt sont optionnels. Voici la valeur par défaut et la description de chaque paramètre :
  
  - `prompt` : le prompt décrivant l'image
  - `model` : le nom du modèle parmi ceux disponible (défault = Flux)
  - `size` : la taille de l'image (défault = 1024x1024)
  - `private` : si l'image est publique ou non (rendre l'image privée => True) (défault = False)
  - `enhance` : si le prompt doit être amélioré par un modèle particulier (défault = False)

  Exceptions :

  - si l'image est rendue publique, elle apparaitra dans le [feed public de Pollinations AI](https://image.pollinations.ai/feed) et dans le salon `#🎨-galerie` du serveur de support du bot.

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
