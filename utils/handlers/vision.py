import base64
import logging

import litellm

from config import GEMINI_API_KEY, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class VisionHandler:
    """
    Classe pour gérer la description d'images en utilisant litellm avec Gemini 2.0 Flash Lite.
    """

    def __init__(self):
        self.model = "gemini/gemma-3-12b-it"

    async def describe_image(self, image_path: str) -> str:
        """
        Décrit une image en utilisant le modèle de vision Gemini Gemma 3-27b.

        Args:
            image_path: Chemin vers le fichier image local.

        Returns:
            Description de l'image en texte.
        """
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            if image_path.lower().endswith(".png"):
                mime_type = "image/png"
            elif image_path.lower().endswith(".jpg") or image_path.lower().endswith(
                ".jpeg"
            ):
                mime_type = "image/jpeg"
            elif image_path.lower().endswith(".gif"):
                mime_type = "image/gif"
            elif image_path.lower().endswith(".webp"):
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are an AI assistant specialized in describing images with maximum precision and detail. Provide comprehensive descriptions including colors, objects, people, actions, settings, and any text visible in the image.\n\nDescribe this image in great detail, including all visible elements, colors, composition, and any text or writing present.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            },
                        },
                    ],
                }
            ]

            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                max_tokens=1024,
                temperature=0.2,
                api_key=GEMINI_API_KEY,
            )

            description = response.choices[0].message.content
            logger.info(f"Image décrite avec succès: {image_path[:50]}...")
            return description

        except Exception as e:
            logger.error(f"Erreur lors de la description de l'image {image_path}: {e}")
            return f"Erreur lors de l'analyse de l'image: {str(e)}"
