"""Tool implementations for function calling."""
import datetime
from typing import Dict, List

async def execute_tool(func_name: str, params: Dict[str, str]) -> str:
    """Execute a tool function."""
    match func_name: 
        case "generate_image":
            from utils.unified_image import unified_image_gen, Format
            prompt = params.get('prompt')
            model = params.get('model', 'flux')
            if not prompt:
                return "Error: prompt is required"
            try:
                images = await unified_image_gen(prompt, model, num_images=1, format=Format.BASE64)
                if images:
                    image_data, model_used = images[0]
                    return f"generated_image:{image_data}"
                else:
                    return "Failed to generate image"
            except Exception as e:
                return f"Error generating image: {e}"
        case _:
            return f"Unknown function: {func_name}"
