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
