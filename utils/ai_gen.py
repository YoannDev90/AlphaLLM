from cerebras.cloud.sdk import Cerebras
from utils.image_gen import generate_image
import logging
from dotenv import load_dotenv
import os
from datetime import datetime
import json

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
                },
                "size": {
                    "type": "string", 
                    "enum": ["1024x1024", "2048x1024", "2048x2048"],
                    "description": "Taille de l'image à générer"
                }
            },
            "required": ["prompt"]
        }
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

async def chat(user_message, perso_preprompt, parameters):
    try:
        if parameters.get("preprompt", True):
            preprompt = load_preprompt()
            if perso_preprompt:
                preprompt += f"\n{perso_preprompt}"
        else:
            preprompt = ""

        tools = [image_generation_tool] if parameters.get("tools", True) else []

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
                        image_url = await generate_image_tools(
                            prompt=args.get("prompt"),
                            parameters={
                                "size": args.get("size", "1024x1024"),
                            }
                        )
                        return image_url
                    except json.JSONDecodeError:
                        logger.error("Erreur de parsing JSON")
                    except ValueError as e:
                        logger.error(str(e))
        
        return response_message.content
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse Cerebras : {e}")
        return f"Erreur lors de la génération de la réponse : {e}"

async def generate_image_tools(prompt: str, parameters: dict) -> str:
    try:
        if parameters.get("tools", True):
            size = parameters.get("size", "1024x1024")
            width, height = map(int, size.split('x'))
            image_url = await generate_image(
                prompt=prompt,
                width=width,
                height=height
            )

            logger.info(f"Image générée (prompt:{prompt}, taille: {size})")
            return image_url
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'image : {e}")
        return f"Erreur lors de la génération de l'image : {e}"