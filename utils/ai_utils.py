#ai_utils.py
import base64
import logging
import requests
from utils.langs import get_translation

logger = logging.getLogger('AlphaLLM')


def load_preprompt():
    with open('config/preprompt.txt', 'r') as file:
        preprompt = file.read()
    return preprompt

def prompt_test():
    return "Answer \"online\" if you are online"