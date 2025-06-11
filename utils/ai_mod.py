from jigsawstack import JigsawStack
import os
from dotenv import load_dotenv

load_dotenv()

JIGSAWSTACK_API_KEY = os.getenv("NSFW_CLASSIFIER_API_KEY")

jigsaw = JigsawStack(api_key=JIGSAWSTACK_API_KEY)

def is_nsfw(image_url: str) -> bool:
    response = jigsaw.validate.nsfw({"url": image_url})
    nsfw = True if response.get("nsfw", False) or response.get("nudity", False) else False
    return nsfw