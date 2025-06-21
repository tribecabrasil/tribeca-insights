#!/bin/bash

echo "🔄 Atualizando ambiente local (sem recriar o ambiente virtual)..."

# ⚠️ Este script assume que o ambiente virtual (.venv) já está ativo.
# É altamente recomendado criar e ativar o ambiente virtual com: source .venv/bin/activate
# Caso ainda não tenha feito isso, execute 'make init' antes de continuar.

# Atualiza dependências
pip install --upgrade pip
pip install -e .

# Reinstala pacotes de tipagem, se necessário
pip install pandas-stubs types-requests

# Atualiza certificados (macOS)
python3 tribeca_insights/config.py

# Executa testes
pytest

echo "✅ Ambiente atualizado com sucesso!"
