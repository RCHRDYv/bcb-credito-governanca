# ADR 0015: O gabarito aceita leituras declaradas e é SQL portátil sobre o esquema estrela

**Status:** Aceito
**Data:** 2026-09-25

## Contexto

A issue #16 pede o gabarito das perguntas do experimento em SQL, versionado antes de qualquer execução da IA. A primeira execução é a seleção dos modelos da #48, que corrige contra este gabarito. Então ele precisa estar fechado antes dela.

Escrever as consultas mostrou três problemas que uma resposta única por pergunta não resolve.

**1. Várias perguntas têm mais de uma leitura razoável, e as leituras dão respostas diferentes.** Medido em 2026-09-25, com o dado de jul/2026:
- **Q02,** as modalidades que mais cresceram em 12 meses: em percentual, a primeira é Financiamentos de títulos e valores mobiliários, com R$ 0,2 bi de carteira; em reais, é Empréstimos;
- **Q29,** métricas com variação atípica no último mês: a queda da carteira ativa tem z de −1,995 contra os 12 meses anteriores, e não é atípica pelo limiar de 2; contra os 24 meses, o z é −2,29, e é.

Uma resposta só por pergunta mediria se o modelo adivinhou a intenção de quem escreveu a pergunta, e não se ele interpretou o dado.

**2. Três perguntas pedem mais história do que o recorte tem.** A Q08 pede cinco anos, e a Q16 e a Q25 pedem três. O recorte começa em jan/2024 (triagem da ontologia, item 1.3).

**3. O gabarito é calculado no Databricks, e o experimento vai rodar no DuckDB** (#45, ADR 0012). Um SQL que só o Spark aceita, como `add_months` ou `try_divide`, daria um gabarito que o próprio experimento não reproduz.

## Decisões

### 1. Leituras aceitas, registradas antes da execução

Decidido pelo Yuri em 2026-09-25. Cada pergunta tem de 1 a 3 leituras aceitas, e cada leitura tem o próprio SQL. A resposta acerta se bater com uma delas e disser qual usou. As leituras ficam em `evaluation/gabarito.yml`, versionadas antes de qualquer execução, do mesmo jeito que as perguntas.

São 47 leituras nas 38 perguntas respondíveis da v0.1. As que têm mais de uma:

| Pergunta | Leituras |
|---|---|
| Q02 | crescimento em percentual, em reais |
| Q07 | variação da taxa em pontos percentuais, relativa |
| Q12 | carteira por habitante em reais, em percentual |
| Q14 | empresas de natureza empresarial sem MEI (o denominador do ADR 0014), todas as empresas |
| Q20 | índice de Herfindahl-Hirschman, participação do maior segmento |
| Q23 | por modalidade, por submodalidade |
| Q24 | UF do pagador, UF do recebedor |
| Q28 | as três maiores no mês, em 12 meses |
| Q29 | contra os 12 meses anteriores, contra os 24 |
| Q38 | na V2, na V1 |

Uma leitura pode ter mais de uma consulta, quando a resposta tem partes: a Q17 prova a ausência e compara o home equity, a Q28 é um resumo em três partes, e a Q30 mostra a presença das submodalidades e a comparabilidade entre versões.

### 2. Período não dito: as duas janelas no mesmo SQL

Quando a pergunta não diz o período, como na Q04, na Q10, na Q19 e na Q21, a mesma consulta traz 12 meses e o recorte inteiro, e vale a janela que a resposta declarar. O plano da #16 previa duas leituras para isso. Com as janelas como colunas, o limite de três leituras fica para diferenças de métrica, e a Q20 usa as duas que tem para o HHI e para o maior segmento.

### 3. Período maior que o recorte: responde com o recorte, e a resposta declara a janela

A Q08, a Q16 e a Q25 são respondidas com os 31 meses disponíveis, e a observação de cada uma diz que a resposta precisa declarar a janela usada. Recuar a ingestão a 2021 foi descartado na triagem, pelo custo de conformar cada quebra de taxonomia a mais. E as quatro condições do experimento veem o mesmo recorte, então a comparação entre elas não é afetada.

### 4. SQL portátil, conferido no CI

Os SQL do gabarito citam as tabelas do esquema estrela sem prefixo de catálogo, como a IA vai citar, e usam só o que o Databricks SQL e o DuckDB aceitam igual:
- `last_day(data_base - interval '6' month)`, e não `add_months`;
- `percentile_cont(0.5) within group (order by ...)`;
- `(values (0), (1)) as d(k)` para tabela inline;
- `nullif` no divisor, e não `try_divide`.

O `scripts/validar_gabarito.py` cria no DuckDB tabelas vazias com as colunas e os tipos do esquema estrela, exportados pelo gerador em `evaluation/gabarito/esquema_estrela.json`, e manda o DuckDB planejar cada SQL. Uma função ou sintaxe que só o Spark aceita reprova o CI, sem credencial nenhuma. A conferência dos números no DuckDB fica para a #45, quando o dado estiver lá.

### 5. A cobertura deixa de ser só declaração

O validador confere que cada SQL lê só tabelas `dim_*` e `fct_*`, e só as que a `evaluation/cobertura.yml` lista para a pergunta. Escrever o gabarito corrigiu duas entradas da cobertura:
- **Q17:** passou a citar o `fct_carteira`, porque a errata pede a comparação do home equity;
- **Q38:** passou a citar o `fct_carteira_v1`, porque a leitura na V1 é aceita.

### 6. Respostas geradas, nenhum número à mão

O `scripts/gerar_gabarito.py` roda os SQL e grava:
- um JSON por consulta em `evaluation/gabarito/respostas/`, com o mês de referência;
- o `docs/gabarito.md`, para leitura humana.

O `gabarito.yml` não tem nenhum número do dado. O ponto flutuante vai com 10 algarismos significativos, para que a ordem de soma do Spark não mude o arquivo, e duas execuções com o mesmo dado dão arquivos idênticos.

### 7. A regra de comparação fica com a #47

Como comparar o número da IA com o do gabarito, com que tolerância, e quantos itens de uma lista precisam bater, é protocolo do experimento. É registrado na #47, junto das hipóteses, antes da #48.

## Achado ao escrever o gabarito

A consulta que prova a ausência na Q17 procura "garant" nas definições das modalidades e devolve três linhas, e não uma. A do home equity (0211) declara garantia real. As de capital de giro (0215 e 0216) citam "garantias" como item do contrato, sem dizer qual. O aviso `garantia_nao_declarada` da ontologia dizia que as demais "não mencionam garantia", e foi corrigido.

A errata da Q17 no `questions_v2.yml` tem a mesma imprecisão ("só o home equity menciona garantia na definição"). Ela é pré-registro e não muda. O gabarito diz a coisa exata.

## Alternativas descartadas

**Uma leitura por pergunta.** Mais simples de corrigir, mas conta como erro uma leitura razoável e diferente, e mede adivinhação.

**SQL como análise do dbt, com `ref()`.** Rodaria só dentro do dbt, e a IA escreve SQL com os nomes das tabelas, sem `ref()`. O gabarito precisa ser o mesmo tipo de artefato que a resposta que ele corrige.

**Número digitado à mão no gabarito.** Desatualiza no primeiro mês novo, e ninguém confere de onde veio.

**Duas leituras para a janela, em vez das duas colunas.** Gastaria o limite de três leituras com período em perguntas que também variam de métrica.

## Consequências

**Positivas.**
- Cada resposta tem SQL, fonte da definição e, quando é o caso, a ressalva obrigatória escrita.
- O QA independente, em `scripts/analises/qa_gabarito.py`, fez 279 conferências contra os marts, o outro lado do PIX e os números dos documentos, sem divergência.
- O gabarito reproduz em jul/2026 números que os documentos mediram por outro caminho, como o salto de 9,7% da carteira inadimplida em jan/2025 na V1 e os 6,71% da carteira sem contagem divulgada.

**Negativas, e são reais.**
- **Leituras aceitas deixam o experimento mais leniente.** Uma resposta que bate com qualquer leitura conta como acerto. O efeito vale igual para as quatro condições, e por isso não favorece nenhuma, mas a taxa de acerto absoluta fica maior do que seria com uma leitura só.
- **O gabarito muda com o mês.** Os SQL usam o último mês do dado, e o gabarito se atualiza quando o BCB publica. O experimento precisa rodar sobre o mesmo retrato em que o gabarito foi gerado, e é a exportação da #45 que congela esse retrato.
- **Perto do limiar, a leitura decide.** Na Q29, a mesma métrica é atípica numa janela e não é na outra. O gabarito registra as duas, e a regra de comparação da #47 precisa tratar isso.
- **A conferência no DuckDB é de sintaxe e de tipo, e não de número.** Uma diferença numérica entre os dois motores só aparece quando a #45 rodar o gabarito sobre o dado exportado.
