# Tribeca Insights

## Instalação
# Tribeca Insights

## Descrição
Tribeca Insights é uma ferramenta modular de análise SEO e extração semântica de sites, desenvolvida em Python 3. Permite rastrear páginas, extrair conteúdo relevante (títulos, descrições, headings, imagens), calcular frequência de palavras, identificar links externos e gerar relatórios em Markdown, CSV e JSON.

## Recursos Principais
- **Crawling Inteligente**: Respeita `robots.txt`, configura delays e identifica sitemaps.
- **Exportação Completa**: Gera arquivos em:
  - Markdown (`pages_md/` e `index.md`)
  - CSV (`keyword_frequency_<domain>.csv`, `visited_urls_<domain>.csv`)
  - JSON (`pages_json/`, `index.json`, `external_urls.json`, `keyword_frequency_<domain>.json`, `visited_urls_<domain>.json`)
- **Análise Semântica**: Limpeza de texto, tokenização e cálculo de frequência de termos com stopwords.
- **Modular e Extensível**: Estruturado como pacote Python (`tribeca_insights`) e CLI via entry-point `tribeca-insights`.
- **Workflow Híbrido**: Markdown para fluxo editorial e JSON para integração com dashboards e bancos de dados.

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/tribecabrasil/tribeca-insights.git
   cd tribeca-insights
   ```

2. Instale em modo de desenvolvimento:
   ```bash
   pip install --upgrade pip
   pip install -e .
   ```

3. Prepare recursos NLTK (stopwords):
   ```bash
   python -c "import nltk; nltk.download('stopwords')"
   ```

## Uso

### Linha de comando
```bash
tribeca-insights --max-pages 50 --language en
```
Opções:
- `--max-pages N`  
  Número máximo de páginas a rastrear.  
- `--language {en,pt-br}`  
  Idioma para tokenização e stopwords.  
- `--domain example.com`  
  (Opcional) Força o domínio a ser analisado.

### Exemplo de execução
```bash
tribeca-insights --max-pages 20 --language pt-br
```

Isso criará uma pasta `example-com/` com toda a estrutura de relatórios.

## Como Funciona

Tribeca Insights opera em sete etapas principais:

1. **Entrada de parâmetros**  
   - O usuário executa o comando `tribeca-insights`, passando `--max-pages`, `--language` e opcionalmente `--domain`.  
   - Internamente, o CLI (`tribeca_insights.cli`) valida inputs e configura o ambiente (SSL e recursos NLTK).

2. **Configuração de pasta de projeto**  
   - Cria uma pasta `<domain_slug>/` (ex: `example-com/`) com subdiretórios:
     - `pages_md/` para arquivos Markdown.
     - `pages_json/` para JSON de cada página.

3. **Carregamento de histórico**  
   - Usa `load_visited_urls` para ler `visited_urls_<domain>.csv` e identificar URLs já processadas.  
   - Chama `reconcile_md_files` para reprocessar páginas sem `.md`.

4. **Reconciliação de Markdown**  
   - Verifica cada entrada com status “visitado” (1) e campo `MD File` vazio.
   - Se o arquivo `.md` existir, preenche o campo; caso contrário, redefine status para 2 (reprocessar).

5. **Crawling & Processamento concorrente**  
   - `crawl_site` busca URLs internas, respeitando `robots.txt` e `crawl-delay`.  
   - Cada URL é processada por `fetch_and_process`:
     - Faz request HTTP com `requests.Session` e cabeçalho `User-Agent`.  
     - Analisa HTML via BeautifulSoup, extraindo:
       - **Título** e **meta description**.
       - Texto visível (limpo de scripts, estilos e tags não relevantes).  
       - **Headings** (h1–h6) e **imagens** (alt).  
       - **Links externos** e detecção de novos links internos.  
     - Gera arquivo Markdown em `pages_md/<slug>.md`.

6. **Exportação de dados**  
   - Atualiza frequência de palavras em CSV com `update_keyword_frequency`.  
   - Exporta lista de URLs externas em Markdown e JSON via `export_external_urls_json`.  
   - Salva histórico de visitas em CSV e JSON (`export_visited_urls_json`).

7. **Geração de índice**  
   - Cria `index.md` e `index.json` listando todos os slugs e títulos de páginas.  
   - Garante consistência entre artefatos Markdown e JSON.

8. **Metadados de projeto**  
   - Gera `project_<domain_slug>.json` contendo:
     - URL base, idioma, timestamps (`created_at`, `last_updated_at`).  
     - Configurações do CLI (`max_pages`, `crawl_delay`).  
     - Lista de `pages_data` com todos os metadados de cada página.  

Todo o fluxo é modular e pode ser integrado como biblioteca ou automação em projetos Django ou pipelines de BI.

## Estrutura de Pastas
```
tribeca-insights/
├── scripts/
│   ├ main.py
│   ├ split_crawler.py
│   └ validate_structure.py
├── tribeca_insights/
│   ├ __init__.py
│   ├ cli.py
│   ├ config.py
│   ├ crawler.py
│   ├ storage.py
│   ├ text_utils.py
│   └ exporters/
│       ├ __init__.py
│       ├ csv.py
│       ├ json.py
│       └ markdown.py
├── example-com/
│   ├ pages_md/
│   ├ pages_json/
│   ├ index.md
│   ├ index.json
│   ├ external_urls.md
│   ├ external_urls.json
│   ├ keyword_frequency_example-com.csv
│   ├ keyword_frequency_example-com.json
│   ├ visited_urls_example-com.csv
│   └ visited_urls_example-com.json
├── pyproject.toml
└── README.md
```

## Integração com Django

1. Adicione `tribeca_insights` a `INSTALLED_APPS` em `settings.py`.  
2. Use `manage.py crawl_site` para executar crawls integrados.


## Code Style (PEP 8)

We follow the official Python style guide (PEP 8). Please ensure:

- **Line length** ≤ 88 characters (configurable in Black).  
- **Import order**: stdlib → third-party → local, with blank lines between groups.  
- **Naming**: `snake_case` for functions and variables, `PascalCase` for classes, and `UPPER_CASE` for constants.  
- **Indentation**: 4 spaces per indent level (no tabs).  
- **Spacing**: one space around operators and after commas, blank lines between top-level definitions.

To automatically format and check:

```bash
pip install black isort flake8
black --check .
isort --check-only .
flake8
```

## Additional PEP Recommendations

In addition to PEP 8 and PEP 257, the following PEPs improve code readability, type safety, and maintainability, which helps AI tools and developers collaborate effectively:

- **PEP 484 – Type Hints**  
  Enables function and variable annotations (`def foo(x: int) -> str:`) for better static analysis and AI-assisted code generation.

- **PEP 526 – Variable Annotations**  
  Allows explicit type declarations for variables (`count: int = 0`), improving clarity and tooling support.

- **PEP 563 – Postponed Evaluation of Annotations**  
  Delays type annotation evaluation, simplifying forward references and preventing import cycles.

- **PEP 585 – Built-in Generic Types**  
  From Python 3.9, use native generics (`list[str]` instead of `List[str]`) for more concise and modern code.

- **PEP 634/635/636 – Structural Pattern Matching**  
  Introduces `match/case` statements (Python 3.10+) for clear control flow, well-supported by modern tooling.

- **PEP 498 – f-Strings**  
  Fast and readable string interpolation.  

- **PEP 572 – Assignment Expressions**  
  The “walrus operator” (`:=`) for in-line assignments, enabling concise loops and conditions.

- **PEP 492 – Async/Await**  
  Native asynchronous programming support, improving clarity in concurrent code.

- **PEP 263 – Source File Encoding**  
  Declares file encoding (`# coding: utf-8`) to avoid parsing errors with non-ASCII characters.

- **PEP 20 – The Zen of Python**  
  Principles guiding Pythonic design and readability (`import this`).


## Assistência por IA

> **Observação:** Todo código, modelagem e comentários devem ser escritos 100% em inglês. O README, por enquanto, pode permanecer em Português.

Para facilitar que ferramentas de IA colaborem na evolução do código, recomendamos:

1. **Estrutura de Código Clara**  
   - Separe responsabilidades em módulos coesos (e.g., `crawler.py`, `exporters/`, `storage.py`, `text_utils.py`).  
   - Use nomes de funções e variáveis descritivos e consistentes.

2. **Documentação e Docstrings**  
   - Inclua docstrings [PEP 257] em todas as funções, explicando parâmetros, retorno e possíveis exceções.  
   - Atualize o `README.md` com exemplos de uso e esquemas de JSON gerados.

3. **Type Hints e Anotações**  
   - Adicione tipagem estática em parâmetros e retornos (`typing.List`, `typing.Dict`, `Optional[str]`).  
   - Permite que IA compreenda contratos de API e sugira autocompleções.

4. **Testes Automatizados**  
   - Crie testes unitários (`tests/`) para cada módulo com `pytest`.  
   - Inclua casos de sucesso e falha, mocks de requisições HTTP e validação de JSON/CSV gerados.

5. **Linting e Formatação**  
   - Configure `flake8` ou `pylint` para padronizar estilo e detectar erros cedo.  
   - Use `black` (formatação automática) para manter consistência no layout do código.

6. **Commits Atômicos e Mensagens Descritivas**  
   - Cada commit deve implementar uma única alteração ou feature.  
   - Mensagens com verbo no imperativo e referência ao ticket ou issue quando aplicável.

7. **Workflows de CI/CD**  
   - Configure GitHub Actions para rodar testes, lint e build automaticamente em cada pull request.  
   - Adicione workflows para publicação automática de pacotes e geração de relatórios de cobertura.

8. **Ambientes Isolados**  
   - Utilize `venv` ou `poetry` para gerenciar dependências.  
   - Inclua `requirements.txt` ou `poetry.lock` no repositório para controle de versões.

Seguindo essas diretrizes, ferramentas de IA terão contexto e metadados suficientes para analisar, sugerir melhorias e gerar código de forma rápida e precisa.