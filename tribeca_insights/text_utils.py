"""
Text utilities for Tribeca Insights.

Provides functions for cleaning, extracting, and tokenizing text content.
"""

import re
import logging

import nltk
from bs4 import BeautifulSoup

from typing import List, Optional, Set
from functools import lru_cache

logger = logging.getLogger(__name__)

_CLEAN_RE = re.compile(r'[^a-zA-Z\s]')
_SPACE_RE = re.compile(r'\s+')

@lru_cache(maxsize=None)
def _get_stopwords(language: str) -> Set[str]:
    """
    Returns the set of stopwords for the language, cached.
    Raises ValueError if the language is not supported.
    """
    try:
        return set(nltk.corpus.stopwords.words(language))
    except LookupError:
        raise ValueError(f"Language '{language}' not supported for stopwords.")

def safe_strip(value: Optional[str]) -> str:
    """
    Returns the string with leading and trailing spaces removed or an empty string if `value` is None.

    :param value: text to be cleaned or None
    :return: text without leading or trailing spaces
    """
    if value is None:
        logger.debug("safe_strip received None")
        return ""
    return value.strip() if isinstance(value, str) else ""

def clean_and_tokenize(text: str, language: str = "english") -> List[str]:
    """
    Cleans the text by removing non-alphabetic characters, normalizes spaces,
    tokenizes, removes stopwords and short words.

    :param text: raw string to be processed
    :param language: language for stopword removal
    :return: list of filtered tokens
    :raises ValueError: if the language is not supported
    """
    logger.debug(f"Cleaning and tokenizing text of length {len(text)}")
    # Remove non-letter characters
    text = _CLEAN_RE.sub("", text)
    # Normalize multiple spaces
    text = _SPACE_RE.sub(" ", text)
    tokens = text.lower().split()
    stop_words = _get_stopwords(language)
    # Filter stopwords and words with less than 3 characters
    return [word for word in tokens if word not in stop_words and len(word) > 2]

def extract_visible_text(html: str) -> str:
    """
    Extracts visible text from HTML, removing scripts, styles, and non-textual tags.

    :param html: raw HTML content
    :return: concatenated readable text
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "svg", "footer", "nav", "meta"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    cleaned = text.strip() if text else ""
    logger.debug(f"Extracted visible text length: {len(cleaned)}")
    return cleaned