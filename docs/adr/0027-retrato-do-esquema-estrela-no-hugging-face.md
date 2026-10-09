# ADR 0027: O esquema estrela sai em Parquet, num retrato fixado e publicado no Hugging Face

**Status:** Aceito
**Data:** 2026-10-07

## Contexto

O experimento consulta o esquema estrela no DuckDB, "sobre o retrato exportado pela #45" (`evaluation/hipoteses.yml`). O chat do dashboard lê as mesmas tabelas de um dataset público do Hugging Face ([ADR 0016](0016-site-estatico-no-github-pages-e-chat-no-zerogpu.md), decisão 3, e [ADR 0019](0019-chat-consulta-so-o-esquema-estrela.md)). O pré-registro da #47 lista, entre o que se fixa antes da primeira execução, o "retrato do esquema estrela no DuckDB, com o mes_de_referencia". Faltava dizer em que forma o retrato sai, como ele fica fixado e como se prova que o DuckDB responde igual ao Databricks.

Três fatos medidos em 2026-10-07 pesaram:
- O `fct_carteira` tem 9.687.811 linhas. A consulta do SDK em JSON, usada até aqui, devolve tudo como texto e tem limite de tamanho. O Free Edition aceita o resultado em Arrow por links externos, com os tipos decimal, data, booleano e inteiro intactos.
- O `hf auth login` grava o token em texto puro num arquivo da pasta do usuário.
- As três fontes do Banco Central (SCR.data, SGS e Pix) são publicadas sob a ODbL, que exige a mesma licença para a base derivada. O CNPJ é Creative Commons Attribution, e o IBGE usa licença aberta com crédito.

## Decisões

Decidi em 2026-10-07, antes do código (#45).

1. **Um Parquet por tabela `dim_*` e `fct_*`,** exportado em Arrow pelos links externos e gravado pelo polars, ordenado por todas as colunas e comprimido com zstd, para que o mesmo dado produza os mesmos bytes. O que pode sair é o `evaluation/gabarito/esquema_estrela.json`, que a exportação só lê. Tabela, coluna ou tipo diferente no Databricks para a exportação, e nenhum nome de coluna de dado pessoal passa.
2. **O DuckDB vê as tabelas por views com os nomes do dbt,** em `esquema_estrela/views.sql`, sobre a variável `base`. A mesma view lê a pasta local ou o dataset. Não há arquivo `.duckdb`: ele seria binário, dependeria da versão do DuckDB e duplicaria os Parquets.
3. **O retrato fica fixado em `esquema_estrela/manifesto.json`:** mês de referência, e para cada tabela as colunas, as linhas, o sha256 e os totais por período calculados no Databricks. A publicação acrescenta a revisão do dataset, e o experimento e o CI leem `hf://datasets/vidayuri/bcb-credito-governanca@<revisao_hf>`, e não o `main`, que muda.
4. **A prova de que o DuckDB responde igual ao Databricks** é o `scripts/analises/qa_esquema_estrela.py`:
   - os totais por período batem exatamente;
   - os SQL do gabarito ficam, célula a célula, dentro da tolerância de cada coluna no pré-registro (`hipoteses.yml#comparacao.tolerancia`), contra as respostas versionadas e contra o Databricks ao vivo;
   - o relatório mostra a maior diferença relativa de cada consulta, para que uma diferença real entre os motores não se esconda dentro da banda de 1%.

   Uma divergência é reportada e não ajustada: o SQL do gabarito só muda por errata.
5. **O dataset é `vidayuri/bcb-credito-governanca`, sob a ODbL 1.0,** com o cartão versionado em `esquema_estrela/README.md`. Sobem só os Parquets e o cartão, numa lista explícita. Nada de `evaluation/`, e nada do bronze.
6. **O token de escopo fino é pedido por `getpass` a cada publicação** e fica só na memória do processo. Ele não vai para arquivo, variável de ambiente, cofre ou CI. O token só escreve no dataset, e eu rodo a publicação da minha máquina. É a regra do [ADR 0001](0001-credenciais-e-dado-bruto-fora-do-repositorio.md), ampliada pelo ADR 0016, aplicada ao Hugging Face.
7. **Um job do CI lê o dataset público na revisão fixada,** sem credencial. Ele confere o sha256 pela API do Hub, os arquivos publicados, os totais contra o manifesto e o gabarito contra as respostas versionadas. Se o Hugging Face sair do ar, só esse job reprova.

## Alternativas descartadas

**Consultar em JSON e montar o Parquet na máquina.** Não passa pelo limite do resultado em linha com o `fct_carteira`, e perderia os tipos.

**Gravar o Parquet num volume e baixar pela Files API.** Ficou como plano B, caso o Free Edition recusasse os links externos. Ele aceitou, e o caminho por Arrow é mais curto.

**Um arquivo `.duckdb` no dataset, sozinho ou junto dos Parquets.** Descartado pela decisão 2.

**`fct_carteira` partido por mês.** O Space leria menos dado numa consulta de um mês, mas seriam 31 arquivos a mais, e o retrato ficaria maior sem necessidade.

**`hf auth login`, mesmo com logout logo depois.** Grava o token em texto puro durante a publicação.

**Licença CC-BY 4.0.** Não está entre as licenças compatíveis com a ODbL, que as fontes do Banco Central exigem para a base derivada.

## Consequências

**Positivas.**
- O experimento e o chat leem o mesmo retrato, fixado por revisão, e qualquer pessoa reproduz uma consulta sem Databricks.
- A equivalência entre o DuckDB e o Databricks é medida, e não suposta, e o CI volta a medi-la a cada mudança.
- O retrato do gabarito passa a valer também para os arquivos: se o esquema dos marts mudar, a exportação para até que o gabarito seja regerado.

**Negativas, e são reais.**
- **O job do CI depende da rede do Hugging Face** e baixa o retrato inteiro a cada execução.
- **Cada mês novo pede três passos na máquina local:** exportar, conferir e publicar. Enquanto a publicação não acontece, o manifesto fica sem revisão, e o job do CI reprova.
- **A tolerância do pré-registro é larga para comparar dois motores.** Por isso o relatório mostra a maior diferença relativa, e não só passa ou falha.
