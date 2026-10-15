# bcb-credito-governanca

Projeto de portfólio sobre o crédito PJ do SCR.data do Banco Central: ingestão no Databricks Free Edition, camada semântica em dbt, ontologia SKOS, dashboard estático no GitHub Pages e o experimento ontologia contra RAG (ADR 0013). Repositório público. Visão geral em `README.md`, decisões em `docs/adr/`.

## Ambiente
- Windows. O Yuri roda os comandos no **PowerShell**, na pasta `C:\Users\viday\claude_projects\bcb-credito-governanca`. `python` não está no PATH: use sempre `uv run python -m <módulo>`.
- Databricks por OAuth do CLI (perfil em `~/.databrickscfg`). Nunca peça nem grave token. Nada de Databricks roda no CI (ADR 0001).
- `data/` (bruto e landing) é ignorado pelo git. Capturas e páginas de revisão ficam fora do repositório, em `../revisao-*`.

## Como passar instruções para o Yuri executar
IMPORTANT: quando o Yuri tiver de rodar algo na máquina dele, siga todas estas regras, sem exceção:
- **PowerShell, não Git Bash.** Variável de ambiente é `$env:NOME="valor"`, nunca `export`. Caminho com `\`.
- **Comece pelo `cd` com o caminho completo**: `cd C:\Users\viday\claude_projects\bcb-credito-governanca`. Nunca suponha que ele já está na pasta.
- **Passos numerados, cada um com quatro partes:** onde rodar, o comando, como saber que deu certo e o que fazer se der errado (em geral: "cole a saída inteira aqui").
- **Um comando por bloco de código**, na ordem exata. Diga quando é preciso esperar um terminar antes do próximo.
- **Nada sem explicação.** Se precisar de uma segunda janela, diga como abrir ("tecla Windows, digite PowerShell, Enter") e qual não fechar. Não use nome que você não definiu, como "janela 2".
- **Confira antes de mandar.** Branch, pasta, o que já está rodando (o Ollama da bandeja ocupa a porta 11434), o que o comando pressupõe. Se não der para conferir daqui, mande primeiro um comando de verificação.
- **Avise dos tropeços conhecidos antes que aconteçam:** o pre-commit (gitleaks, final de linha) pode reprovar o commit; o app do Ollama na bandeja precisa ser encerrado com `Get-Process -Name "ollama*" | Stop-Process -Force`.
- **Separe o que é dele do que é seu.** Em cada passo, deixe claro se ele roda ou se ele só te avisa com uma frase exata para colar.
- **Seja curto.** Sem teoria antes dos comandos. A explicação vem em uma linha, depois do comando, se for preciso.

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
uv run python -m scripts.validar_assistente
uv run python -m scripts.validar_assistente --autoteste
uv run python -m scripts.validar_selecao
uv run python -m scripts.validar_selecao --autoteste
uv run python -m scripts.validar_experimento
uv run python -m scripts.validar_experimento --autoteste
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

## RAG (#46, ADR 0028)
- Corpus em `ingestion/fontes.py` (`DOCUMENTOS_DO_CORPUS`), baixado por `uv run python -m ingestion.baixar_documentos` para `data/raw/documentos/`. Documento novo só entra por errata no registro.
- Dependências no grupo `rag` do uv, fora do CI: `uv run --group rag python -m rag.construir` refaz o índice do zero na CPU, e `rag.avaliar` mede e escolhe o modelo. A #49 usa `rag.indice.buscar`.
- `evaluation/recuperacao.yml` é gerado por `scripts.gerar_gabarito_de_recuperacao` e conferido por `scripts.validar_recuperacao`, no workflow `recuperacao.yml`. Mudou uma fonte na ontologia, regere.
- QA por outro caminho: `uv run --group rag python -m scripts.analises.qa_corpus`.
- `evaluation/recuperacao.yml` e `rag/manifesto.json` estão congelados pelo registro: reconstruir ou regerar que mude um deles pede errata.

## Assistente (#49, ADR 0029)
- Pacote `assistente/`: `uv run python -m assistente "pergunta" --condicao B`. C e D pedem `--group rag`, e a interface Gradio pede `--group assistente --group rag` (`python -m assistente.interface`).
- `assistente/parametros.yml` (os dois modelos escolhidos pela #48) e `assistente/modelo_de_prompt.yml` estão congelados por errata. Nunca afine o prompt nas perguntas do `questions_v3.yml`.
- A fumaça com o Ollama (`scripts.analises.fumaca_assistente`) usa só perguntas inventadas, e quem a roda é o Yuri. O `validar_assistente` e o `--autoteste` rodam sem modelo no workflow `assistente.yml`.

## Seleção dos modelos (#48, ADR 0030)
- Candidatos, regras e configuração em `evaluation/selecao.yml`. Os campos medidos (revisão, sha256, `num_ctx`, razão) saem de `uv run --group rag python -m scripts.dimensionar_contexto`, que o Yuri roda.
- Errata 1 (antes de rodar): `evaluation/selecao.yml` e `assistente/modelo_de_prompt.yml`. O `scripts.selecionar_modelos` se recusa a rodar sem ela. Errata 2 (depois): `assistente/parametros.yml` e `evaluation/selecao/resultado.json`.
- A execução (`scripts.selecionar_modelos`) e a correção às cegas (`correcao.as_cegas`) são do Yuri, na máquina dele, com o Ollama. `scripts.resumir_selecao` gera o resultado, a página `docs/selecao-dos-modelos.md` e os modelos do `parametros.yml`.
- O corretor (`correcao/`) compara por valor e é o da #50. O `validar_selecao` e o `--autoteste` rodam sem modelo no workflow `selecao.yml`; o `--ensaio` do executor também.

## Experimento (#50, ADR 0031)
- Estatística em `experimento/estatistica.py`, funções puras usadas pelo resumo, pelo validador e pelo notebook. O Newcombe é o método 10 do artigo de 1998, conferido contra a Tabela III.
- Ordem antes de rodar: `/code-review`, a fumaça nos dois modelos (`fumaca_assistente --modelo`, perguntas inventadas) para medir o tempo e conferir o corte de citações em B, C e D, e só então a errata de congelamento.
- A errata congela o executor, o `experimento/`, o `correcao/`, o `assistente/` (sem a interface e o `__main__`), o `rag/indice.py`, o `scripts/selecionar_modelos.py` e o `scripts/validar_registro.py` (errata 4). A errata 5 da #118 ampliou a lista para tudo o que forma o prompt, a triagem e o retrato do esquema estrela (lista em `CONGELADOS_ANTES_DO_EXPERIMENTO`). Depois dela, mudar um desses arquivos pede errata nova.
- A execução (`uv run --group rag python -m scripts.executar_experimento --perguntas teste --modelo <nome>`) e a correção às cegas (`correcao.as_cegas --experimento --execucao <n>`) são do Yuri, na máquina dele. Erro de servidor não grava a execução e para: basta rodar de novo.
- `scripts.resumir_experimento` gera `evaluation/experimento/resultado.json`, `execucoes.jsonl.gz` e `docs/experimento.md`; `--do-publicado` refaz sem `data/`. O notebook `notebooks/experimento.ipynb` lê só o publicado, e o PDF sai por `uv run --group notebook quarto render`.
- QA por outro caminho: `uv run python -m scripts.analises.qa_experimento`. Tudo isso roda sem modelo no workflow `experimento.yml`, junto do `--ensaio`.

## Emenda do instrumento (#118, ADR 0032)
- A execução 1 falhou no controle de qualidade: a gramática do Ollama gera as chaves do JSON em ordem alfabética, e o modelo escrevia a abstenção antes do SQL. Ela sai como registrada; as afirmações confirmatórias são da execução 2.
- Conjunto de desenvolvimento em `evaluation/desenvolvimento/` (30 perguntas inventadas, D01 a D30). Gabarito no DuckDB: `uv run python -m scripts.gerar_gabarito_de_desenvolvimento` (`--conferir-mapa` confere os tipos nos SQL do teste). Validador: `scripts.validar_desenvolvimento` (+ `--autoteste`; `--embeddings` com o grupo rag). Nenhum ajuste se mede nas 41.
- Variações V−1 a V4 em `assistente/variacoes.py` e `variacoes.yml`; o `responder` recebe `variacao`, e a V−1 é a execução 1 intocada. `scripts.validar_variacoes` (+ `--autoteste`) confere a V−1 contra os registros da execução 1.
- Portão e regras em `evaluation/portao.yml`, medidos por `scripts.medir_portao` (`--variacao`, `--resumo`, `--gravar`, `--autoteste`). Dimensionamento por variação: `uv run --group rag python -m scripts.dimensionar_variacoes`.
- Triagem: `uv run --group rag python -m scripts.executar_experimento --perguntas desenvolvimento --variacao <V> --candidato <nome>`, gravando em `data/desenvolvimento/<V>/`. Fumaça ao vivo das chaves e da seed: `scripts.analises.fumaca_variacoes`. O desempate do corretor (posição contra código) se confere em `scripts.analises.qa_corretor`.
- O resumo e o validador do experimento recebem `--execucao 1` ou `2`; a saída vai para `evaluation/experimento/execucao-N/`. A correção às cegas também: `correcao.as_cegas --experimento --execucao <n>`.
- O executor recarrega o modelo antes de cada execução (o Gemma só repete a seed partindo frio) e roda o DuckDB com uma thread. No teste, só roda a variação registrada, sem `--pasta` nem `--candidato`, e a execução 2 exige o `evaluation/desenvolvimento/triagem.json` em "escolhida".
- Os textos do `hipoteses.yml` de cada variação estão prontos em `evaluation/hipoteses_por_variacao.yml`; a errata 6 só os copia, e o `validar_variacoes` confere. Replay da V−1 contra a execução 1: `scripts.analises.replay_v_menos_1` (precisa de `data/`).
- Errata 5 congela a emenda antes da triagem (lista em `CONGELADOS_ANTES_DO_EXPERIMENTO`, com o retrato do esquema estrela); a errata 6 registra a variação, os modelos, o `num_ctx`, o `triagem.json`, o `hipoteses.yml` copiado e o `resumir_experimento.py`. O conjunto de desenvolvimento pode ser revisto uma vez só (`metadata.versao` = 1 + as erratas do `perguntas.yml` marcadas com `revisao_do_conjunto: true`, até 2).

## Dashboard (`dashboard/`)
- JavaScript sem framework (ADR 0017), Vite e ECharts carregado sob demanda, com o palco em tela única (ADR 0022).
- Textos em `src/textos/pt-BR.js`: `t()` lança erro se faltar a chave.
- Os dados são JSON em `public/data/`, exportados por `uv run python -m scripts.exportar_dados_do_dashboard`.
- Verificação: `npm run tokens:check`, `lint`, `typecheck`, `test`, `build`, `budget` e `test:e2e`. O Firefox do Playwright não abre nesta máquina, e o CI cobre os três navegadores.
- Decisões do dashboard entram nas tabelas de `docs/dashboard/requisitos.md`.

## Convenções
- IMPORTANT: o autor do projeto é o Yuri, e todo texto que vai para o repositório (ADR, docs, README, comentários, docstrings, commits, PR) é escrito na voz dele, em primeira pessoa ("decidi", "rodei na minha máquina") ou impessoal. Nunca "o Yuri decidiu", "decisão do Yuri" ou "na máquina do Yuri". Este CLAUDE.md é a exceção, porque fala com o Claude.
- Sem marcadores do Claude Code no projeto: commit sem `Co-Authored-By` nem `Claude-Session`, PR sem "Generated with Claude Code" nem link de sessão.
- Comentários e docstrings bilíngues, um bloco PT seguido de um bloco EN, no estilo dos arquivos vizinhos.
- Branch por issue (`feat/`, `ci/`, `chore/`), PR com `Closes #n`.
- IMPORTANT: não mexa no `.github/workflows/ci.yml` numa PR que não é do site. Qualquer mudança nele dispara o job do site do dashboard (#105), que leva mais de 10 minutos. Job novo vai num workflow próprio em `.github/workflows/`, como o `esquema-estrela.yml`. Só mude o `ci.yml` se o Yuri pedir.
- Fluxo de uma issue: `/iniciar-issue <n>` até a execução do plano aprovado, `/code-review` no diff da branch com os achados corrigidos, e só então `/entregar-issue <n>` do commit à PR. Passo a passo em `docs/fluxo-de-trabalho.md`.
- O hook de pre-commit `mixed-line-ending` corrige o arquivo e reprova o commit: rode `git add` de novo e repita o commit.
- Para editar texto com acento, prefira as ferramentas de edição ou um script em arquivo. Heredoc no Bash quebra com barra invertida.

## Ao compactar
Preserve a issue em andamento, as decisões do Yuri com data, os arquivos alterados, os comandos de verificação que passaram e o que falta.
