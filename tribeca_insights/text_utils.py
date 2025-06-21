#!/usr/bin/env python3
"""
Text utility functions for Tribeca Insights:
- Cleaning HTML to visible text
- Tokenizing and filtering via NLTK stopwords
- Safe string stripping
- Environment setup (SSL + NLTK)
"""

import logging
import os
import re
from functools import lru_cache
from typing import List, Optional, Set

import nltk

try:
    import certifi
except ImportError:
    certifi = None

# Map CLI language codes to NLTK stopwords language names
_LANGUAGE_MAP = {
    "en": "english",
    "pt-br": "portuguese",
    "es": "spanish",
    "fr": "french",
    "it": "italian",
    "de": "german",
    "zh-cn": "chinese",
    "ja": "japanese",
    "ru": "russian",
    "ar": "arabic",
}

logger = logging.getLogger(__name__)

MIN_TOKEN_LENGTH = 2
_CLEAN_RE = re.compile(r"[^A-Za-zÀ-ÿ]+")
_SPACE_RE = re.compile(r"\s+")

# Fallback stopword sets used when NLTK data is unavailable
FALLBACK_STOPWORDS = {
    "english": {"the", "a", "and", "of", "is", "this"},
    "spanish": {"y", "de", "la", "que"},
    "portuguese": {"e", "de", "que", "o"},
}


def setup_environment() -> None:
    """
    Prepare the environment:
    - Point SSL at certifi CA bundle if available (fix macOS SSL issues)
    - Download NLTK stopwords quietly if missing
    """
    # Configure SSL to use certifi CA bundle if available
    if certifi:
        ca_path = certifi.where()
        os.environ["SSL_CERT_FILE"] = ca_path
        logger.info(f"Using certifi CA bundle for SSL: {ca_path}")

    # Ensure stopwords corpus is present
    try:
        nltk.download("stopwords", quiet=True)
        logger.info("NLTK stopwords ensured.")
    except OSError as e:
        logger.warning(f"Failed to download NLTK stopwords: {e}")


@lru_cache(maxsize=None)
def _get_stopwords(language: str) -> Set[str]:
    """
    Return cached set of stopwords for the given CLI language code.
    Automatically downloads if not already installed.
    """
    lang_key = _LANGUAGE_MAP.get(language, language)
    try:
        return set(nltk.corpus.stopwords.words(lang_key))
    except LookupError:
        if lang_key in FALLBACK_STOPWORDS:
            logger.warning(
                f"Stopwords for '{lang_key}' unavailable; using fallback set"
            )
            return FALLBACK_STOPWORDS[lang_key]
        logger.info(f"NLTK stopwords for '{lang_key}' not found. Downloading…")
        try:
            nltk.download("stopwords", quiet=True)
            return set(nltk.corpus.stopwords.words(lang_key))
        except OSError as e:  # pragma: no cover - network may be blocked
            logger.warning(f"Failed to download stopwords: {e}")
            return set()


def clean_and_tokenize(text: str, language: str = "en") -> List[str]:
    """
    Strip non-letters, lowercase, split on whitespace, filter out stopwords and short tokens.

    :param text: raw visible text
    :param language: CLI code for language (e.g. 'en', 'pt-br')
    :return: list of tokens
    """
    # Collapse non-letters and normalize spaces
    cleaned = _CLEAN_RE.sub(" ", text)
    cleaned = _SPACE_RE.sub(" ", cleaned).strip().lower()
    tokens = cleaned.split()

    # Filter stopwords and short tokens
    stop_words = _get_stopwords(language)
    return [
        tok for tok in tokens if len(tok) >= MIN_TOKEN_LENGTH and tok not in stop_words
    ]


def extract_visible_text(html: str) -> str:
    """
    Remove scripts, styles, and collapse whitespace to produce clean text.

    :param html: raw HTML markup
    :return: visible text
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    # kill scripts/styles
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    # Collapse multiple whitespace characters
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_strip(value: Optional[str]) -> str:
    """
    Safely strip a string, returning empty string for None or non-str.
    """
    if isinstance(value, str):
        return value.strip()
    return ""
