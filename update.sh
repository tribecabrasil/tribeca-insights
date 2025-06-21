#!/usr/bin/env bash
set -euo pipefail

# 0) Torne o script executável (uma vez)
#    chmod +x update.sh

# 1) Renomeia a pasta do pacote (sem Git)
if [ -d tribecaOrganic ]; then
  mv tribecaOrganic tribeca_insights
  echo "📂 Pasta renomeada: tribecaOrganic → tribeca_insights"
else
  echo "⚠️ Diretório tribecaOrganic não encontrado, pulando mv"
fi

# 2) Substitui referências nos arquivos .py, .md e .toml
find . -type f \( -name '*.py' -o -name '*.md' -o -name '*.toml' \) \
  -exec sed -i '' \
    -e 's/tribecaOrganic/tribeca_insights/g' \
    -e 's/tribeca-organic/tribeca-insights/g' {} +
echo "🔍 Referências trocadas em todos os arquivos."

# 3) Atualiza pyproject.toml (nome do pacote e entry-point)
sed -i '' \
  -e 's/^name = "tribecaOrganic"/name = "tribeca-insights"/' \
  -e 's#tribecaOrganic.cli:main#tribeca_insights.cli:main#g' \
  pyproject.toml
echo "⚙️  pyproject.toml atualizado."

# 4) Atualiza README (título e menções)
sed -i '' \
  -e 's/# Tribeca Organic/# Tribeca Insights/' \
  -e 's/Tribeca Organic/Tribeca Insights/g' \
  README.md
echo "📝 README.md atualizado."

echo "✅ Renomeação concluída. Agora teste:"
echo "   # (recarregue seu shell/env virtual se precisar)"
echo "   pip install -e ."
echo "   tribeca-insights --help"