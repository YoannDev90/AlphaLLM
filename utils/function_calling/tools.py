"""Tool implementations for function calling."""

import datetime
from typing import Dict, List


async def execute_tool(func_name: str, params: Dict[str, str]) -> str:
    """Execute a tool function."""
    match func_name:
        case "generate_image":
            from utils.unified_image import Format, unified_image_gen

            prompt = params.get("prompt")
            model = params.get("model", "zimage")
            enhance = params.get("prompt_enhance", True)
            if not prompt:
                return "error: Missing prompt parameter"
            try:
                images = await unified_image_gen(
                    prompt, model, num_images=1, enhance=enhance, format=Format.BASE64
                )
                if images:
                    image_data, model_used = images[0]
                    return f"generated_image:{image_data}"
                else:
                    return "error: Failed to generate image"
            except Exception as e:
                return f"error: Error generating image: {e}"
        case _:
            return f"Unknown function: {func_name}"
