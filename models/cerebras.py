from cerebras.cloud.sdk import Cerebras
import logging
from dotenv import load_dotenv
import os
import json

logger = logging.getLogger('AlphaLLM')

load_dotenv()

cerebras_client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

async def cerebras_chat(user_message, preprompt, tools, bot, user, parameters):
    try:
        completion = cerebras_client.chat.completions.create(
            messages=[
                {"role": "system", "content": preprompt},
                {"role": "user", "content": user_message}
            ],
            tools=tools,
            tool_choice="auto" if tools else None,
            model="llama3.3-70b"
        )
        response_message = completion.choices[0].message

        from utils.ai_gen import generate_image_tools
        
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "generate_image_tools":
                    try:
                        args = json.loads(tool_call.function.arguments)
                        image_data = await generate_image_tools(
                            prompt=args.get("prompt"),
                            bot=bot,
                            user=user,
                            parameters=parameters,
                            tool_parameters={
                                "size": args.get("size", "1024x1024"),
                            }
                        )
                        return image_data
                    except json.JSONDecodeError:
                        logger.error("Erreur de parsing JSON")
                    except ValueError as e:
                        logger.error(str(e))
        
        return response_message.content
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse Cerebras : {e}")
        return f"Erreur lors de la génération de la réponse : {e}"