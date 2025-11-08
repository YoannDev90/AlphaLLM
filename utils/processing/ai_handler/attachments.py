"""Attachment and content processing for Discord messages."""

import logging
import re

from utils.config.app_config import LOGGER_NAME
from utils.processing.markdown import md_conversion
from utils.processing.web import crawl

logger = logging.getLogger(LOGGER_NAME)

URL_PATTERN = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+\/?(?:[^\s]*[^\s.,])?'


async def process_attachments(raw_content: str, attachments: list) -> str:
    """Process Discord attachments and external links in user content."""
    processed_content = raw_content
    docs = []

    links = re.findall(URL_PATTERN, raw_content)
    
    # Only log if there are attachments or links to process
    if attachments or links:
        logger.info(f"Processing {len(attachments)} attachments and {len(links)} links")

    for attachment in attachments:
        if attachment.content_type.startswith("image"):
            processed_content += f"\n[Attached image: {attachment.url}]"
            logger.debug(f"Image attachment: {attachment.url}")
        else:
            docs.append(attachment.url)

    for doc_url in docs:
        try:
            doc_content = await md_conversion(doc_url)
            processed_content += f"\nDocument content:\n{doc_content}"
        except Exception as e:
            logger.warning(f"Document conversion failed: {str(e)}")

    for link in set(links):
        try:
            link_content = await crawl(link)
            if link_content:
                processed_content += f"\n\nLink: {link}\nContent:\n{link_content}"
            else:
                processed_content += f"\n[Link inaccessible: {link}]"
        except Exception as e:
            logger.warning(f"Error processing link: {str(e)}")

    logger.info(f"Content processing done. Size: {len(processed_content)} chars")
    return processed_content
