import logging
import mimetypes
import os
import tempfile
from typing import Dict, List, Optional, Union
from urllib.parse import unquote, urlparse

import requests

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

from starlette.datastructures import UploadFile

from utils.handlers.markdown import MarkdownConverter
from utils.handlers.vision import VisionHandler


class FileHandler:
    """
    Classe pour gérer le téléchargement et la classification temporaire des fichiers.
    Supporte les URLs et les fichiers directs avec métadonnées.
    """

    def __init__(self, files: List[Union[str, Dict, UploadFile]]):
        """
        Initialise le handler de fichiers.

        Args:
            files: Liste de fichiers. Chaque élément peut être :
                - str: URL du fichier
                - dict: Fichier direct avec clés 'content' (bytes), 'filename' (str), 'content_type' (str optionnel)
                - UploadFile: Objet UploadFile de Starlette
        """
        self.files = files
        self.temp_dir = tempfile.mkdtemp(prefix="betallm_files_")
        self.converter = MarkdownConverter()
        self.vision_handler = VisionHandler()
        self.saved_files: Dict[str, List[str]] = {
            'image': [],
            'text': [],
            'audio': [],
            'video': [],
            'other': []
        }
        self.text_contents: List[str] = []
        # process_files will be called asynchronously

    async def process_files(self):
        """Traite tous les fichiers : téléchargement/sauvegarde et classification."""
        for file in self.files:
            try:
                if isinstance(file, str):
                    await self._download_file(file)
                elif isinstance(file, dict):
                    await self._save_direct_file(file)
                elif isinstance(file, UploadFile):
                    content = await file.read()
                    file_dict = {
                        'content': content,
                        'filename': file.filename,
                        'content_type': file.content_type
                    }
                    await self._save_direct_file(file_dict)
                else:
                    logger.warning(f"Type de fichier non supporté: {type(file)}")
            except Exception as e:
                logger.error(f"Erreur lors du traitement du fichier {file}: {e}")

    async def _download_file(self, url: str):
        """Télécharge un fichier depuis une URL."""
        logger.info(f"Téléchargement du fichier depuis {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        filename = self._extract_filename(url, response)
        if not filename:
            filename = "unknown_file"

        # Déterminer le suffixe depuis le filename
        suffix = ""
        if '.' in filename:
            suffix = '.' + filename.split('.')[-1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=self.temp_dir) as temp_file:
            temp_file.write(response.content)
            path = temp_file.name

        file_type = self._detect_type(path, response.headers.get('content-type'))
        if file_type == 'image':
            description = await self.vision_handler.describe_image(path)
            self.text_contents.append(f"Image description:\n{description}")
            logger.info(f"Image décrite: {filename}")
        else:
            markdown_content = self.converter.convert_to_markdown(path)
            if markdown_content:
                self.text_contents.append(markdown_content)
                logger.info(f"Fichier converti en markdown: {filename}")
            else:
                self.saved_files[file_type].append(path)
                logger.info(f"Fichier sauvegardé: {filename} (type: {file_type})")

    async def _save_direct_file(self, file_dict: Dict):
        """Sauvegarde un fichier direct."""
        content = file_dict.get('content')
        filename = file_dict.get('filename', 'direct_file')
        content_type = file_dict.get('content_type')

        if not content:
            logger.warning("Contenu manquant pour fichier direct")
            return

        # Déterminer le suffixe depuis le filename
        suffix = ""
        if '.' in filename:
            suffix = '.' + filename.split('.')[-1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=self.temp_dir) as temp_file:
            temp_file.write(content)
            path = temp_file.name

        file_type = self._detect_type(path, content_type)
        if file_type == 'image':
            description = await self.vision_handler.describe_image(path)
            self.text_contents.append(f"Image description:\n{description}")
            logger.info(f"Image directe décrite: {filename}")
        else:
            markdown_content = self.converter.convert_to_markdown(path)
            if markdown_content:
                self.text_contents.append(markdown_content)
                logger.info(f"Fichier direct converti en markdown: {filename}")
            else:
                self.saved_files[file_type].append(path)
                logger.info(f"Fichier direct sauvegardé: {filename} (type: {file_type})")

    def _extract_filename(self, url: str, response) -> Optional[str]:
        """Extrait le nom du fichier depuis l'URL ou les headers."""
        # Essai depuis Content-Disposition
        content_disposition = response.headers.get('content-disposition')
        if content_disposition:
            import re
            match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
            if match:
                filename = match.group(1).strip('\'"')
                return unquote(filename)

        # Essai depuis l'URL
        parsed = urlparse(url)
        path = unquote(parsed.path)
        if '/' in path:
            filename = path.split('/')[-1]
            if filename:
                return filename

        # Fallback
        return None

    def _detect_type(self, path: str, content_type: Optional[str] = None) -> str:
        """Détecte le type de fichier."""
        logger.debug(f"Détection du type pour {path}, content_type: {content_type}")

        # Utilise le content-type si fourni
        if content_type:
            main_type = content_type.split('/')[0]
            subtype = content_type.split('/')[1] if '/' in content_type else ''
            if main_type in ['image', 'audio', 'video']:
                logger.debug(f"Type détecté via content-type: {main_type}")
                return main_type
            elif main_type == 'text' or (main_type == 'application' and subtype in ['json', 'xml', 'javascript', 'x-javascript']):
                logger.debug(f"Type détecté comme texte via content-type: {content_type}")
                return 'text'

        # Utilise mimetypes basé sur l'extension
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type:
            main_type = mime_type.split('/')[0]
            subtype = mime_type.split('/')[1] if '/' in mime_type else ''
            if main_type in ['image', 'audio', 'video']:
                logger.debug(f"Type détecté via mimetypes: {main_type}")
                return main_type
            elif main_type == 'text' or (main_type == 'application' and subtype in ['json', 'xml', 'javascript', 'x-javascript']):
                logger.debug(f"Type détecté comme texte via mimetypes: {mime_type}")
                return 'text'
        else:
            logger.debug("Aucune extension détectée via mimetypes")

        # Essai avec magic si disponible (détection binaire)
        try:
            import magic
            mime_type = magic.from_file(path, mime=True)
            if mime_type:
                main_type = mime_type.split('/')[0]
                subtype = mime_type.split('/')[1] if '/' in mime_type else ''
                if main_type in ['image', 'audio', 'video']:
                    logger.debug(f"Type détecté via magic: {main_type}")
                    return main_type
                elif main_type == 'text' or (main_type == 'application' and subtype in ['json', 'xml', 'javascript', 'x-javascript']):
                    logger.debug(f"Type détecté comme texte via magic: {mime_type}")
                    return 'text'
                else:
                    logger.debug(f"Type magic détecté mais non supporté: {mime_type}")
            else:
                logger.debug("Magic n'a pas pu déterminer le type")
        except ImportError:
            logger.warning("python-magic non installé, détection binaire ignorée")
        except Exception as e:
            logger.debug(f"Erreur avec magic: {e}")

        logger.debug("Type par défaut: other")
        return 'other'

    def get_files_by_type(self, file_type: str) -> List[str]:
        """Retourne la liste des chemins des fichiers d'un type donné."""
        return self.saved_files.get(file_type, [])

    def cleanup(self):
        """Supprime les fichiers temporaires."""
        import shutil
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info("Fichiers temporaires supprimés")
            else:
                logger.debug("Répertoire temporaire déjà supprimé")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des fichiers temporaires: {e}")

    def __del__(self):
        """Nettoyage automatique."""
        self.cleanup()
