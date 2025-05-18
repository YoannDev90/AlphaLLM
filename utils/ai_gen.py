from cerebras.cloud.sdk import Cerebras
from utils.image_gen import generate_image
import logging
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import aiohttp
from utils.gallery import gallery

logger = logging.getLogger('AlphaLLM')

load_dotenv()

cerebras_client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"),max_retries=3)

image_generation_tool = {
    "type": "function",
    "function": {
        "name": "generate_image_tools",
        "description": "Génère une image à partir d'un prompt textuel",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Description détaillée de l'image à générer"
                    # comment préciser de traduire le prompt en anglais ?
                },
                "size": {
                    "type": "string", 
                    "description": "Taille de l'image à générer en pixels (largeur x hauteur), maximum 2048x2048, minimum 512x512",
                    # comment le faire utiliser une taille custom (2048x1024) ?
                }
            },
            "required": ["prompt", "size"],
        }
    }
}

doc_tool = {
    "type": "function",
    "function": {
        "name": "doc_tools",
        "description": "Envoie la documentation du bot",
    }
}


def load_preprompt() -> str:
    """Charge le pré-prompt depuis un fichier"""
    try:
        with open("config/preprompt.txt", "r", encoding="utf-8") as file:
            preprompt = file.read()
        logger.debug("Preprompt loaded successfully")
        now = datetime.now()
        preprompt += f"\nDate: {now.strftime('%Y-%m-%d')}\nHour: CEST {now.strftime('%H:%M:%S')}\n"
        return preprompt
    except Exception as e:
        logger.error(f"Error loading preprompt: {str(e)}")
        raise

async def chat(user_message, perso_preprompt, bot, user, parameters):
    try:
        if parameters.get("preprompt", True):
            preprompt = load_preprompt()
            if perso_preprompt:
                preprompt += f"\n{perso_preprompt}"
        else:
            preprompt = ""

        tools = [image_generation_tool, doc_tool] if parameters.get("tools", True) else []

        completion = cerebras_client.chat.completions.create(
            messages=[
                {"role": "system", "content": preprompt},
                {"role": "user", "content": user_message}
            ],
            tools=tools,
            tool_choice="auto" if tools else None,
            model="llama3.3-70b"
        )
        logger.info("Réponse générée par Cerebras")
        response_message = completion.choices[0].message
        
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "generate_image_tools":
                    try:
                        args = json.loads(tool_call.function.arguments)
                        image_data = await generate_image_tools(
                            prompt=args.get("prompt"),
                            bot=bot,
                            user=user,
                            parameters={
                                "size": args.get("size", "1024x1024"),
                            }
                        )
                        return image_data
                    except json.JSONDecodeError:
                        logger.error("Erreur de parsing JSON")
                    except ValueError as e:
                        logger.error(str(e))
                if tool_call.function.name == "doc_tools":
                    try:
                        doc = await doc_tools(parameters)
                        return doc
                    except Exception as e:
                        logger.error(f"Erreur lors de la génération du document : {e}")
                        return f"Erreur lors de la génération du document : {e}"
        
        return response_message.content
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse Cerebras : {e}")
        return f"Erreur lors de la génération de la réponse : {e}"

async def generate_image_tools(prompt: str, bot, user, parameters: dict) -> str:
    try:
        if parameters.get("tools", True):
            size = parameters.get("size", "1024x1024")
            width, height = map(int, size.split('x'))
            image_data = await generate_image(
                prompt=prompt,
                width=width,
                height=height
            )
            logger.info(f"Image générée (prompt:{prompt}, taille: {size})")
            await gallery(bot, image_data, prompt, user)
            return image_data
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'image : {e}")
        return f"Erreur lors de la génération de l'image : {e}"

async def doc_tools(parameters: dict) -> str:
    try:
        if parameters.get("tools", True):
            url = "https://raw.githubusercontent.com/YoannDev90/AlphaLLM-Docs/ef53cd3f9692c7d2676950ded45d917426945f92/image-gen.md"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        doc = await response.text()
                    else:
                        logger.error(f"Erreur lors de la récupération de la documentation : {response.status}")
                        return f"Erreur lors de la récupération de la documentation : {response.status}"

            logger.info("Documentation envoyée")
            return doc
    except Exception as e:
        logger.error(f"Erreur lors de la génération du document : {e}")
        return f"Erreur lors de la génération du document : {e}"