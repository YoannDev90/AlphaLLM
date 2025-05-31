from mistralai import Mistral
import logging
from dotenv import load_dotenv
import os
import json

logger = logging.getLogger('AlphaLLM')

load_dotenv()

mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

async def mistral_chat(user_message, preprompt, tools, bot, user, parameters):
        try:
            completion = await mistral_client.chat.complete_async(
                messages=[
                {"role": "system", "content": preprompt},
                {"role": "user", "content": user_message}
                ],
                tools=tools,
                tool_choice="auto" if tools else None,
                model="mistral-small-latest"
            )

            response_message = completion.choices[0].message

            from utils.ai_gen import generate_image_tools
            
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "generate_image_tools":
                        try:
                            args = json.loads(tool_call.function.arguments)
                            return await generate_image_tools(
                                prompt=args.get("prompt"),
                                bot=bot,
                                user=user,
                                parameters=parameters,
                                tool_parameters={
                                    "size": args.get("size", "1024x1024")
                                }
                            )
                        except json.JSONDecodeError:
                            logger.error("Erreur de parsing JSON")
                        except ValueError as e:
                            logger.error(str(e))
            
            return response_message.content
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse Mistral : {e}")
            return f"Erreur lors de la génération de la réponse : {e}"
