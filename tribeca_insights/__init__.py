# tribeca_insights/__init__.py

import os

import certifi

# Garante que qualquer download (NLTK, requests, etc.) use o bundle correto de certificados
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

# resto do __init__.py (se houver)…
