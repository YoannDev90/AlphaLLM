import aiohttp
import config
import logging

error_logger = logging.getLogger('ErrorLogger')

async def get_chatbot_response(guild_id, channel_id, user_id, user_input, use_history, conversation_history):
    history = conversation_history[guild_id][channel_id] if use_history else []
    messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": msg} for i, msg in enumerate(history)]
    messages.append({"role": "user", "content": user_input})

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {config.OPENROUTER_API_KEY}"},
            json={
                "model": "mattshumer/reflection-70b:free",
                "messages": messages
            },
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            if response.status == 200:
                data = await response.json()
                content = data['choices'][0]['message']['content']
                if content.strip():
                    if use_history:
                        history.append(user_input)
                        history.append(content)
                    return content
                else:
                    return "Désolé, je n'ai pas pu générer de contenu. Veuillez réessayer."
            else:
                error_data = await response.json()
                error_message = error_data.get('error', {}).get('message', 'Une erreur inconnue s\'est produite.')
                error_code = error_data.get('error', {}).get('code', response.status)
                error_logger.error(f"Erreur API : {error_code} - {error_message}")
                return f"Erreur {error_code} : {error_message}"

async def generate_search_prompt(user_input):
    messages = [
        {"role": "system", "content": "Vous êtes un assistant chargé de générer des prompts de recherche concis et pertinents pour Google Custom Search. Générez un prompt court basé sur l'entrée de l'utilisateur."},
        {"role": "user", "content": user_input}
    ]
    return await get_chatbot_response(messages)

async def generate_synthesis(search_results, user_input):
    results_text = "\n".join([f"- {result['title']}: {result['snippet']}" for result in search_results])
    messages = [
        {"role": "system", "content": "Vous êtes un assistant chargé de synthétiser des résultats de recherche. Créez une synthèse concise et informative basée sur les résultats fournis."},
        {"role": "user", "content": f"Résultats de recherche :\n{results_text}\n\nQuestion originale : {user_input}"}
    ]
    return await get_chatbot_response(messages)

async def generate_final_response(synthesis, user_input):
    messages = [
        {"role": "system", "content": "Vous êtes un assistant IA conversationnel. Utilisez la synthèse fournie pour répondre à la question de l'utilisateur de manière naturelle et engageante."},
        {"role": "user", "content": f"Synthèse : {synthesis}\n\nQuestion de l'utilisateur : {user_input}"}
    ]
    return await get_chatbot_response(messages)
