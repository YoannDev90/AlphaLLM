import base64
import logging

import litellm

from config import LOGGER_NAME, read_file

logger = logging.getLogger(LOGGER_NAME)


class VisionHandler:
    """
    Classe pour gérer la description d'images en utilisant litellm avec Gemini 2.0 Flash Lite.
    """

    def __init__(self):
        import json
        import os
        with open("configs/misc/img_vision.json", "r") as f:
            self.config = json.load(f)
        self.model = self.config["litellm_params"]["model"]
        self.api_key = os.getenv(self.config["litellm_params"]["api_key"])
        self.max_tokens = self.config.get("max_tokens", 1024)
        self.temperature = self.config.get("temperature", 0.2)
        self.system_prompt = read_file("configs/prompts/vision_prompt.txt")

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
                            "text": self.system_prompt,
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
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                api_key=self.api_key,
            )

            description = response.choices[0].message.content
            logger.info(f"Image décrite avec succès: {image_path[:50]}...")
            return description

        except Exception as e:
            logger.error(f"Erreur lors de la description de l'image {image_path}: {e}")
            return f"Erreur lors de l'analyse de l'image: {str(e)}"
