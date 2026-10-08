# bcb-credito-governanca

Projeto de portfólio sobre o crédito PJ do SCR.data do Banco Central: ingestão no Databricks Free Edition, camada semântica em dbt, ontologia SKOS, dashboard estático no GitHub Pages e o experimento ontologia contra RAG (ADR 0013). Repositório público. Visão geral em `README.md`, decisões em `docs/adr/`.

## Ambiente
- Windows com Git Bash. `python` não está no PATH: use sempre `uv run python -m <módulo>`.
- Databricks por OAuth do CLI (perfil em `~/.databrickscfg`). Nunca peça nem grave token. Nada de Databricks roda no CI (ADR 0001).
- `data/` (bruto e landing) é ignorado pelo git. Capturas e páginas de revisão ficam fora do repositório, em `../revisao-*`.

## Ingestão (ADR 0004)
Etapas idempotentes, nesta ordem:
1. Download e conversão: `ingestion.baixar`, `ingestion.converter_parquet`, `ingestion.baixar_ibge`, `ingestion.baixar_sgs`, `ingestion.baixar_pix`, `ingestion.baixar_cnpj`, `ingestion.converter_cnpj`.
2. `ingestion.enviar_volume`: envia ao volume `/Volumes/workspace/bcb_scr/raw`.
3. `ingestion.criar_bronze`: executa `ingestion/bronze.sql`, com `CREATE OR REPLACE ... read_files`.
4. `ingestion.verificar_bronze`: confere o bronze contra `ingestion/manifesto.json`.

- Fonte externa nova: use a skill `nova-fonte-externa`.
- As APIs do IBGE mandam gzip mesmo sem pedir. O SIDRA ignora em silêncio período não publicado, então peça uma lista explícita de períodos.

## dbt
- Rode a partir de `dbt/`: `dbt build -s <seleção>`. A construção inteira é pesada, então prefira seleções.
- Schemas: `workspace.bcb_scr` (bronze), `bcb_scr_staging`, `bcb_scr_intermediate`, `bcb_scr_marts`.
- A UF dos fatos é a sigla. Fonte externa chega pelo `codigo_ibge` da seed `ontologia_dimensao`.
- Seeds são geradas da ontologia, nunca escritas à mão: `uv run python -m scripts.gerar_seeds_da_ontologia`.
- Staging corrige a forma e preserva o conteúdo (ADR 0006). Fato externo fica no grão que a fonte publica.

## Validadores (os mesmos do CI, sem credencial)
```bash
uv run python -m scripts.validar_modalidades --estrutura
uv run python -m scripts.validar_dimensoes --estrutura
uv run python -m scripts.validar_fontes_externas
uv run python -m scripts.validar_correspondencia --estrutura
uv run python -m scripts.validar_perguntas
uv run python -m scripts.validar_cobertura
uv run python -m scripts.validar_gabarito
uv run python -m scripts.validar_registro
uv run python -m scripts.validar_registro --autoteste
uv run python -m scripts.validar_dados_do_dashboard
```
Depois de regerar as seeds, `git diff --exit-code -- 'dbt/seeds/ontologia_*.csv'` precisa sair limpo. O CI também roda `dbt parse` com `uvx --from dbt-core==1.12.3 --with dbt-databricks==1.10.9`.

## Experimento e gabarito (ADR 0013 e 0015)
- As perguntas estão em `evaluation/questions_v3.yml`, e o enunciado não muda depois do registro.
- `evaluation/cobertura.yml` e o `pendente` do `evaluation/gabarito.yml` mudam juntos.
- SQL do gabarito: portátil entre Databricks e DuckDB, sem prefixo de catálogo, lendo só as tabelas que a cobertura lista.
- `uv run python -m scripts.gerar_gabarito` usa o Databricks e regrava todas as respostas, `docs/gabarito.md` e `esquema_estrela.json`. Respostas que aparecem como modificadas só por final de linha não mudaram.
- QA por outro caminho em `scripts/analises/`, por exemplo `qa_gabarito`, `qa_fontes_externas` e `qa_renda_do_trabalho`.
- Pré-registro (#47, ADR 0026): `evaluation/hipoteses.yml`, `evaluation/comparacao.yml`, o `gabarito.yml` e os SQL do gabarito estão congelados pelo `evaluation/registro.yml`. Mudança só por errata datada no fim da lista do registro, nunca editando um hash. As respostas JSON ficam fora, porque mudam com o mês.

## Esquema estrela publicado (#45, ADR 0027)
- `uv run python -m scripts.exportar_esquema_estrela` grava os Parquets em `data/esquema_estrela/` e o `esquema_estrela/manifesto.json`. O que pode sair é o `evaluation/gabarito/esquema_estrela.json`, que ele só lê.
- `uv run python -m scripts.analises.qa_esquema_estrela [--com-databricks | --origem hf]` compara o DuckDB com o Databricks: totais por período e os SQL do gabarito.
- A publicação no Hugging Face (`scripts.publicar_esquema_estrela`) pede o token por getpass e é o Yuri quem roda. Nunca peça nem grave o token.

## Dashboard (`dashboard/`)
- JavaScript sem framework (ADR 0017), Vite e ECharts carregado sob demanda, com o palco em tela única (ADR 0022).
- Textos em `src/textos/pt-BR.js`: `t()` lança erro se faltar a chave.
- Os dados são JSON em `public/data/`, exportados por `uv run python -m scripts.exportar_dados_do_dashboard`.
- Verificação: `npm run tokens:check`, `lint`, `typecheck`, `test`, `build`, `budget` e `test:e2e`. O Firefox do Playwright não abre nesta máquina, e o CI cobre os três navegadores.
- Decisões do dashboard entram nas tabelas de `docs/dashboard/requisitos.md`.

## Convenções
- Comentários e docstrings bilíngues, um bloco PT seguido de um bloco EN, no estilo dos arquivos vizinhos.
- Branch por issue (`feat/`, `ci/`, `chore/`), PR com `Closes #n`.
- IMPORTANT: não mexa no `.github/workflows/ci.yml` numa PR que não é do site. Qualquer mudança nele dispara o job do site do dashboard (#105), que leva mais de 10 minutos. Job novo vai num workflow próprio em `.github/workflows/`, como o `esquema-estrela.yml`. Só mude o `ci.yml` se o Yuri pedir.
- Fluxo de uma issue: `/iniciar-issue <n>` até o plano aprovado, `/entregar-issue <n>` do commit à PR. Passo a passo em `docs/fluxo-de-trabalho.md`.
- O hook de pre-commit `mixed-line-ending` corrige o arquivo e reprova o commit: rode `git add` de novo e repita o commit.
- Para editar texto com acento, prefira as ferramentas de edição ou um script em arquivo. Heredoc no Bash quebra com barra invertida.

## Ao compactar
Preserve a issue em andamento, as decisões do Yuri com data, os arquivos alterados, os comandos de verificação que passaram e o que falta.
