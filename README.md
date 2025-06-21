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

> 💡 Recomendado: Crie e ative um ambiente virtual com Python 3.10+
> 
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> ```

2. Configure o ambiente automaticamente com Make:
   ```bash
   make init
   ```

## Automação

Você pode rodar o fluxo completo com um único comando:
```bash
make init && make test && make run
```

O alvo `make run` executa um crawl de demonstração no domínio
`example.com`, rastreando até 20 páginas em inglês. Isso garante:
- Criação e ativação do ambiente virtual (recomendado)
- Instalação das dependências
- Execução de testes
- Execução de uma varredura padrão

## Uso

### Via Subcomando

Inicie uma varredura:
```bash
tribeca-insights crawl example.com --base-url https://example.com --language pt-br --max-pages 50
```

Exporte relatórios:
```bash
tribeca-insights export md --domain example.com
tribeca-insights export csv --domain example.com
tribeca-insights export json --domain example.com
```

### Ajuda
Para ver todos os comandos disponíveis:
```bash
tribeca-insights --help
```

Opções:
- `--max-pages N`  
  Número máximo de páginas a rastrear.  
- `--language {en, pt-br, es, fr, it, de, zh-cn, ja, ru, ar}`  
  Idioma para tokenização e stopwords.  
- `--workers N`  
  Número de threads a usar no crawl concorrente.  
- `--timeout S`  
  Timeout em segundos para cada requisição HTTP.  
- `--domain example.com`  
  (Opcional) Força o domínio a ser analisado.

### Exemplo

Este exemplo executa uma varredura de até 20 páginas em português, usando 4 threads e timeout de 8 segundos:

```bash
tribeca-insights --max-pages 20 --language pt-br --workers 4 --timeout 8
```

Isso criará uma pasta `example-com/` com toda a estrutura de relatórios.

### Exemplo de uso via subcomando

Para iniciar uma varredura com subcomando:

```bash
tribeca-insights crawl example.com --base-url https://example.com --language pt-br --max-pages 50
```

Para exportar relatórios:

```bash
tribeca-insights export md --domain example.com
tribeca-insights export csv --domain example.com
tribeca-insights export json --domain example.com
```

### Automação com Make

O fluxo completo pode ser executado com:

```bash
make init && make test && make run
```

`make run` executa um crawl padrão em `example.com` com limite de 20
páginas em inglês. Isso garante:
- (Opcional) Criação do ambiente virtual
- Instalação das dependências
- Execução dos testes
- Varredura padrão com configurações do projeto

## Como Funciona

Tribeca Insights opera em oito etapas principais:

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
│       ├ csv.py
│       ├ json.py
│       └ markdown.py
├── example-com/  ← generated outputs
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
  Declares file encoding (`# coding: utf-8`) to avoid parsing errors with non-ASCII caracteres.

- **PEP 20 – The Zen of Python**  
  Principles guiding Pythonic design and readability (`import this`).

## Config Overrides

To keep personal editor or environment settings out of version control, add your local override files to `.gitignore`:
```gitignore
# Local overrides
pyrightconfig.json
pyproject.toml
.flake8
setup.cfg
Makefile
update.sh
```

The included `Makefile` and `update.sh` scripts help avoid manual steps and standardize the environment setup.

## Pyright Configuration

To enable strict type-checking and provide rich diagnostics for AI-assisted development, include a `pyrightconfig.json` at the project root with:

```json
{
  "venvPath": "./.venv",
  "venv": ".venv",
  "include": ["tribeca_insights", "scripts"],
  "exclude": ["example-com", "node_modules", ".git", ".github"],
  "reportMissingTypeStubs": true,
  "reportMissingImports": true,
  "reportOptionalMemberAccess": true,
  "reportOptionalSubscript": true,
  "reportOptionalOperand": true,
  "reportTypedDictNotRequiredAccess": true,
  "pythonVersion": "3.10",
  "typeCheckingMode": "strict"
}
```

This ensures:
- **Strict mode**: all type-checking rules enabled.  
- **Focused scanning**: only your source folders are analyzed.  
- **Optional safety**: flags prevent unintended `None` usage.  
- **Missing-import detection**: catches unresolved or untyped dependencies.  
- **Modern syntax**: supports Python 3.10 features.

Add this file to version control so contributors and CI pipelines all apply the same strict type checks.

## AI Collaboration Guidelines

> **Note:** All code, modeling, comments, and docstrings must be written in **English**. README may remain in Portuguese.

1. **Clear Structure**  
   - Cohesive modules with descriptive names.

2. **PEP 257 Docstrings**  
   - One-line summary + detailed description + parameters/returns.

3. **Type Hints**  
   - Use `list[str]`, `dict[str, int]`, etc.

4. **Automated Tests**  
   - Pytest with mocks and coverage ≥80%.

5. **Lint & Format**  
   - Black, isort, flake8 in CI.

6. **Atomic Commits**  
   - One logical change per commit.

7. **CI/CD Workflows**  
   - GitHub Actions for install, lint, test, build, publish.

8. **Isolated Environments**  
   - venv or poetry; include `requirements.txt` or `poetry.lock`.


For ChatGPT-specific guidelines, see [chatgpt_guidelines.md](chatgpt_guidelines.md) in this repository.