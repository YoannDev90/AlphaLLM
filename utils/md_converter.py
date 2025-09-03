import requests
import logging
from utils.config import logger_name
import os
from markitdown import MarkItDown

logger = logging.getLogger(logger_name)

class MarkdownConverter:
    def __init__(self):
        self.markitdown = MarkItDown()

    def convert_to_markdown(self, file_path):
        try:
            result = self.markitdown.convert(file_path)
            return result.text_content
        except Exception as e:
            logger.error(f"Erreur lors de la conversion : {e}")
            return None

def extract_file_name(url):
    url_parts = url.split("?")
    file_name = url_parts[0].split("/")[-1]
    return file_name

async def md_conversion(doc_url):
    try:
        file_name = extract_file_name(doc_url)
        if file_name is None:
            logger.error(f"Impossible d'extraire le nom du fichier à partir de l'URL.")
            return None
        
        response = requests.get(doc_url)
        if response.status_code == 200:
            with open(file_name, 'wb') as file:
                file.write(response.content)
            
            converter = MarkdownConverter()
            markdown_content = converter.convert_to_markdown(file_name)
            
            try:
                os.remove(file_name)
                logger.debug(f"Fichier {file_name} supprimé avec succès.")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du fichier {file_name}: {e}")
            
            return markdown_content
        else:
            logger.error(f"Erreur lors du téléchargement du fichier: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement ou de la conversion du fichier: {e}")
        return None