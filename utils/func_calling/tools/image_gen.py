async def image_gen_tool(params):
    import logging
    from config import LOGGER_NAME
    from utils.unified_image import Format, unified_image_gen
    
    logger = logging.getLogger(LOGGER_NAME)

    prompt = params.get("prompt")
    model = params.get("model", "zimage")
    enhance = params.get("prompt_enhance", True)
    style = params.get("style")
    
    if not prompt:
        logger.warning("image_gen_tool: Missing prompt parameter")
        return "error: Missing prompt parameter"
    
    logger.info(f"image_gen_tool: Generating image with model={model}, enhance={enhance}, style={style}")
    try:
        images = await unified_image_gen(
            prompt, model, num_images=1, enhance=enhance, style=style, format=Format.BASE64
        )
        if images:
            image_data, model_used = images[0]
            logger.info(f"image_gen_tool: Image generated successfully using {model_used}")
            return f"generated_image:{image_data}"
        else:
            logger.error("image_gen_tool: Failed to generate image (no output)")
            return "error: Failed to generate image"
    except Exception as e:
        logger.error(f"image_gen_tool: Error generating image: {e}")
        return f"error: Error generating image: {e}"