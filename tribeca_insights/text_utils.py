import os
import re
import logging
from pathlib import Path

def safe_strip(value):
    if value is None:
        logging.debug('safe_strip recebeu None')
        return ''
    return value.strip() if isinstance(value, str) else ''

def clean_and_tokenize(text: str, language: str='english') -> List[str]:
    """Clean and tokenize text removing stopwords and short words."""
    text = re.sub('[^a-zA-Z\\s]', '', text)
    text = re.sub('\\s+', ' ', text)
    tokens = text.lower().split()
    stop_words = set(nltk.corpus.stopwords.words(language))
    return [word for word in tokens if word not in stop_words and len(word) > 2]

def extract_visible_text(html: str) -> str:
    """Extract visible text from HTML excluding non-content tags."""
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'svg', 'footer', 'nav', 'meta']):
        tag.decompose()
    text = soup.get_text(separator=' ')
    return text.strip() if text else ''