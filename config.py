import os
import json

if not os.path.exists('config_alphallm.json'):
    TOKEN = input("Veuillez entrer le token du bot : ")
    OPENROUTER_API_KEY = input("Veuillez entrer la clé API OpenRouter : ")
    GOOGLE_API_KEY = input("Veuillez entrer la clé API Google : ")
    SEARCH_ENGINE_ID = input("Veuillez entrer l'ID du moteur de recherche Google : ")
    with open('config_alphallm.json', 'w') as f:
        json.dump({
            "token": TOKEN,
            "openrouter_api_key": OPENROUTER_API_KEY,
            "google_api_key": GOOGLE_API_KEY,
            "search_engine_id": SEARCH_ENGINE_ID
        }, f)
else:
    with open('config_alphallm.json', 'r') as f:
        config = json.load(f)
        TOKEN = config['token']
        OPENROUTER_API_KEY = config['openrouter_api_key']
        GOOGLE_API_KEY = config['google_api_key']
        SEARCH_ENGINE_ID = config['search_engine_id']
