# ADR 0029: O assistente roda no Ollama local, a proveniência é montada pelo código, e os parâmetros ficam provisórios até a #48

**Status:** Aceito
**Data:** 2026-10-09

## Contexto

O [ADR 0012](0012-assistente-de-dados-com-modelo-aberto-e-aplicacao-de-custo-zero.md) definiu o assistente: text-to-SQL sobre o esquema estrela, com a ontologia e os documentos como camadas de contexto que se ligam e desligam. O mesmo componente serve ao experimento do [ADR 0013](0013-experimento-2x2-ontologia-contra-documentos.md), em lote, e ao uso interativo. O pré-registro da #47 (`evaluation/hipoteses.yml` e `evaluation/comparacao.yml`, congelados pelo `evaluation/registro.yml`) já fixava:
- o conteúdo das condições: A só o esquema, B o esquema e a ontologia, C o esquema e os trechos, e D exatamente B mais os trechos de C;
- o fluxo de duas chamadas: SQL ou abstenção, e depois a resposta, sem nova tentativa;
- os cinco campos da resposta (`comparacao.formato_da_resposta`), a temperatura de 0,2 e as seeds de 1 a 5;
- que o modelo, o prompt, o `num_ctx` e os limites do SQL se fixam antes da execução (`execucao.fixado_antes_da_execucao`), o que é trabalho da #48.

O "pronto quando" original da #49, "responde às perguntas da v0.1 nas quatro condições", pedia rodar o modelo no conjunto de teste antes da #48. Isso contraria o [ADR 0026](0026-modelos-do-experimento-escolhidos-pela-condicao-a.md), que faz da #48 a primeira execução contra o gabarito, e não se verifica no CI. O Yuri o trocou em 2026-10-08 por testes com modelo e busca falsos (comentário na #49).

## Decisões

Decididas pelo Yuri em 2026-10-08, antes do código (comentário na #49). A decisão 1, a ordem entre a #49 e a #48, está no comentário e não se repete aqui.

2. **A proveniência é montada pelo código, não pelo modelo.** O modelo devolve só os cinco campos registrados. O assistente anexa:
   - o SQL executado e o resultado bruto, cortado no limite de linhas;
   - os trechos recebidos;
   - os conceitos da ontologia resolvidos a partir do SQL e do resultado, com rótulo, confiança e fonte. Um conceito é resolvido quando uma coluna lida pelo SQL é a `notation` de uma métrica ou de um conceito de fonte externa, a `coluna` de uma dimensão ou está no `afeta` de uma quebra, ou quando um literal de texto do SQL, ou uma célula de texto do resultado, é o código ou o rótulo no dado de uma modalidade. A comparação é sempre pelo valor inteiro, nunca por um pedaço.
3. **Na ontologia de B e D entram os itens inteiros.** São os 147 itens dos quatro YAML de `ontology/`, quebras incluídas, com todos os campos, menos o rótulo em inglês e os metadados de acesso à fonte (endereço, licença, leiaute, formato, transporte, publicador, periodicidade e documentação). A estimativa de 2026-10-08 falava em 151 itens, porque contava os quatro cabeçalhos `esquema`, que são metadados do arquivo e ficam de fora. O bloco tem cerca de 103 mil caracteres, perto de 29 mil tokens pela estimativa. A versão compacta, de 12 mil tokens, perdia o texto de 16 dos 72 itens que o gabarito cita, além dos códigos de filtro.
4. **Servidor: a API nativa `/api/chat` do Ollama.** Ela aceita `num_ctx`, `seed` e `temperature` a cada requisição, e o esquema JSON da resposta em `format`, que restringe a decodificação. A rota compatível com a OpenAI não aceita `num_ctx` por requisição. O cliente usa só a biblioteca padrão.
5. **A interface é Gradio local,** num grupo próprio do uv (`assistente`). Não é o chat do Space ([ADR 0019](0019-chat-consulta-so-o-esquema-estrela.md)).
6. **`valores` sai como tabela `{colunas, linhas}`,** a mesma forma das respostas do gabarito.
7. **O resultado do SQL é cortado, e o modelo é avisado** com "resultado cortado em N de M linhas". Os valores provisórios são 100 linhas e 30 segundos. A maior resposta do gabarito tem 64 linhas.
8. **O vazamento na condição A é aceito e declarado.** As `dim_*` trazem definição, confiança, fonte e aviso, e o modelo pode consultá-los por SQL mesmo em A. Ver as consequências.

As decisões abaixo são convenções de implementação que seguem delas e ficam aqui para revisão.

9. **A guarda do SQL é uma lista do que é permitido,** pela árvore do próprio DuckDB:
   - um comando só, do tipo SELECT, conferido por `duckdb.extract_statements`;
   - a árvore sai do `json_serialize_sql`, que só serializa SELECT;
   - passam só tabelas base `dim_*` e `fct_*`, ou CTEs do próprio comando, sem prefixo de esquema ou de catálogo;
   - função de tabela (`read_*`, `query`, `glob` e afins), `SHOW`, `DESCRIBE`, `ATTACH`, `PRAGMA`, `SET` e `COPY` reprovam.

   Atrás da guarda, o banco tem o acesso a arquivo restrito à pasta do retrato e o acesso externo desligado, e a configuração travada por `lock_configuration`. Um SQL que escapasse da guarda continuaria sem ler outro arquivo.
10. **Limites fora do SQL.** O tempo é cortado por `conexao.interrupt()` num timer. Para as linhas, o código busca N+1 e, só quando passa de N, conta o total com `count(*)` sobre o próprio comando, dentro do mesmo limite de tempo. Contar buscando as linhas no Python levava 104 s no `fct_carteira` inteiro (medido em 2026-10-08).
11. **Falha é erro tipado, sem nova tentativa.** Saída fora do formato, tempo esgotado, recusa da guarda, erro de SQL e prompt maior que o `num_ctx` viram `erro` com o tipo e a etapa. O Ollama não recusa um prompt grande, ele o corta, e o `prompt_eval_count` pode deixar de fora o prefixo em cache. Por isso são duas conferências. Antes do envio, os tokens são estimados pelos caracteres, à razão provisória de 3,0 caracteres por token, abaixo dos cerca de 3,1 medidos na fumaça, para errar estimando tokens a mais. Depois da resposta, vale o `prompt_eval_count`. Se qualquer uma, somada ao limite de tokens da resposta, passa do `num_ctx`, a execução conta como erro de contexto. A chamada entra no registro antes da segunda conferência, para que o prompt grande demais fique medido. A estimativa não é exata: a #48 calibra a razão pelos caracteres e tokens que a fumaça registra. O JSON não é consertado: uma cerca de código em volta já é erro de formato.
12. **Abstenção na primeira chamada encerra a execução.** Não há SQL nem segunda chamada. A resposta sai com `sql` e `valores` vazios, e com a interpretação e a abstenção da primeira chamada.
13. **Os trechos vêm de uma busca só,** feita por quem chama o assistente antes da geração, com o enunciado sem reescrita. Assim, C e D da mesma pergunta recebem os mesmos trechos. O modelo não chama a busca.
14. **Parâmetros provisórios num arquivo só.** `assistente/parametros.yml` traz `provisorio: true`, o modelo `qwen3:8b` (só para a fumaça), `num_ctx` de 45.056, o limite de 2.048 tokens da resposta, a razão de caracteres por token da estimativa, `think: false` e os limites do SQL. `assistente/modelo_de_prompt.yml` é o rascunho do prompt, sem nenhum fato do domínio e sem ajuste nas perguntas registradas. A temperatura e as seeds são conferidas contra o pré-registro. A #48 troca os valores, tira o `provisorio` e congela os dois arquivos por errata no `registro.yml`.
15. **A verificação roda sem modelo, sem rede e sem dado.** `scripts/validar_assistente.py` usa um cliente falso, de respostas gravadas, tabelas vazias com o esquema estrela e trechos inventados, no workflow próprio `assistente.yml`. O `--autoteste` troca uma peça por vez por uma versão estragada e confere que cada uma reprova pelo motivo certo. A fumaça com o Ollama (`scripts/analises/fumaca_assistente.py`) usa três perguntas inventadas, e o validador confere que nenhuma repete uma das 41 registradas.

## Resultado medido

A fumaça de 2026-10-08 rodou na máquina do Yuri, com o `qwen3:8b` no Ollama, as 3 perguntas inventadas nas 4 condições e a seed 1, com os valores anteriores (`num_ctx` de 40.960 e razão de 3,5). Das 12 execuções, 9 terminaram com resposta ou abstenção. As outras 3 viraram erro tipado, sem nova tentativa:
- 2 de SQL: o modelo escreveu um SQL que não roda;
- 1 de contexto, na segunda chamada de D. O prompt de 38.923 tokens, mais os 2.048 da resposta, passou do `num_ctx` por 11 tokens. Quem pegou foi a conferência pelo `prompt_eval_count`, porque a estimativa de 3,5 caracteres por token dava cerca de 34 mil para o prompt de D, uns 11% abaixo do medido.

| Condição | Maior prompt medido |
|---|---|
| A | 2.443 |
| B | 36.878 |
| C | 3.499 |
| D | 38.923 |

Por isso, o `num_ctx` provisório passou a 45.056, o próximo múltiplo de 4.096, e a razão passou a 3,0. Com 45 mil de contexto, o cache KV do `qwen3:8b` em 16 bits fica perto de 6,6 GB, e o total encosta nos 12 GB da placa. Quem fixa o definitivo é a #48, com o modelo do experimento.

## Alternativas descartadas

**Proveniência escrita pelo modelo,** com conceitos e trechos citados num campo da resposta. O modelo pode citar o que não usou. Além disso, o campo a mais mudaria o formato registrado da resposta, e a resposta deixaria de ser comparável entre as condições.

**Ontologia compacta, só com rótulo e definição curta.** Descartada pela decisão 3: perdia texto citado pelo gabarito.

**Rota compatível com a OpenAI, ou uma biblioteca de cliente.** Sem `num_ctx` por requisição, ou com uma dependência a mais para uma chamada HTTP.

**Guarda por lista do que é proibido, ou por regex.** Uma lista do que é proibido falha aberta diante da função de tabela que ninguém lembrou. A árvore do DuckDB diz o que o comando lê.

**`LIMIT` acrescentado ao SQL do modelo.** Mudaria o comando que o modelo escreveu e esconderia o total. O corte por fora preserva o SQL e diz N de M.

**Nova tentativa depois de uma falha.** O pré-registro proíbe.

## Consequências

**Positivas.**
- A #48 recebe o mecanismo pronto: troca os valores do `parametros.yml` e do modelo de prompt, roda e congela por errata.
- A #50 chama `assistente.responder.responder` em lote. Cada execução devolve um registro completo, com parâmetros, mensagens, trechos, SQL, resultado, resposta, proveniência e tempos.
- O CI prova a montagem das condições, a guarda, os limites e o fluxo sem baixar modelo nenhum.

**Negativas, e são reais.**
- **A condição A não é só esquema.** As `dim_*` trazem colunas de definição, confiança, fonte e aviso, e o modelo pode lê-las por SQL. Isso puxa A para perto de B e reduz a diferença medida entre as duas, na mesma direção conservadora do viés do ADR 0026.
- **Os avisos sem ligação com o dado não aparecem na proveniência.** Um aviso que não tem coluna nem código para casar com o SQL nunca é resolvido, por mais que se aplique à pergunta. Isso é consequência da decisão 2, não uma falha da resolução.
- **A Q28 e a Q30 têm gabarito com várias consultas,** e o assistente aceita um comando só. O prompt diz que vale juntar etapas com WITH. A #48 decide se isso basta.
- **O contexto de D aperta os 12 GB da placa.** O 8B com 45 mil já encosta no limite, e um 14B em 4 bits vai pedir cache KV em 8 bits ou parte do modelo na CPU. A fumaça mede o `prompt_eval_count` real de cada condição, para a #48 dimensionar o `num_ctx` por um número medido.
- **A fumaça e a interface não rodam no CI.** Elas dependem do Ollama, do retrato local e do índice do RAG, e quem as roda é o Yuri, na máquina dele.
