# ADR 0032: O instrumento do experimento é emendado num conjunto de desenvolvimento separado, e a execução 2 é a última

**Status:** Aceito
**Data:** 2026-10-15

## Contexto

A execução 1 do experimento 2x2 ([ADR 0031](0031-execucao-e-analise-do-experimento.md)) rodou as 1.640 execuções do registro em 2026-10-14 e 2026-10-15, sem nenhuma repetição por erro de servidor. Ela falhou no controle de qualidade do instrumento:

- **Abstenção em massa.** Na primeira chamada, o SQL saiu vazio em 698 das 820 execuções do Gemma 4 12B e em 797 das 820 do Qwen 3.5 9B, quase igual nas quatro condições (Gemma: A 181, B 163, C 175 e D 179, de 205 cada). Contando as abstenções finais, as do Gemma foram A 182, B 173, C 179 e D 179. No fim, o Gemma teve 713 abstenções, 62 respostas e 45 erros, e o Qwen, 817 abstenções e 3 erros de formato. Pelo script, 1 execução saiu certa em 1.640, e quase não há par discordante entre as condições.
- **A causa é mecânica, e eu a conferi nos registros.**
  - A gramática do Ollama 0.40.4 gera as chaves do JSON em ordem alfabética: 1.637 das 1.640 primeiras chamadas começam por `"abstencao"`, e as outras 3 não são JSON válido. Na seleção (#48), que rodou no Ollama 0.40.1, 1.006 das 1.025 primeiras chamadas começam por `"abstencao"`, e as outras 19 não são JSON válido.
  - Assim, o modelo escreve o motivo de não responder antes de interpretar a pergunta e antes do SQL, ao contrário da ordem registrada em `comparacao.formato_da_resposta`.
- **O que agrava.**
  - O prompt põe a abstenção no mesmo pé do SQL.
  - O `think: false` e modelos pequenos com contexto longo.
  - O SQL que volta vazio: 8 das 10 abstenções da segunda chamada vieram logo depois de um resultado vazio ou nulo.
  - O modelo também pesa: com a mesma ordem de chaves, o Ministral 3 8B se absteve só 16 vezes em 205 na seleção.

O dado, o SQL, o contexto das condições e o corretor funcionam. Mas a execução 1 não informa sobre as hipóteses.

O [ADR 0030](0030-selecao-dos-modelos-pelo-gabarito.md) já tinha avisado que mexer no prompt para reduzir a abstenção seria ajustar o método ao resultado no próprio conjunto de teste. Esta emenda responde a esse aviso de cinco formas:
- um conjunto de desenvolvimento separado das 41 perguntas;
- um cardápio de variações do instrumento congelado antes de medir;
- o mesmo texto nas quatro condições;
- um portão que não mostra acerto por condição;
- uma regra de parada.

Um agente revisor (`.claude/agents/revisor-de-experimento.md`) revisou o plano duas vezes e o código três vezes. Os achados dele estão incorporados abaixo.

## Decisões

Tomei estas decisões em 2026-10-15, antes de qualquer triagem. Elas estão nos comentários da #118.

### O desenho da emenda

1. **A execução 1 fica registrada.** Ela é julgada às cegas (95 itens), analisada como registrado e publicada como "resultado registrado, com instrumento falho", em `evaluation/experimento/execucao-1/`, com o limite declarado do texto original (`limite_declarado.txt`).
2. **As afirmações confirmatórias são da execução 2.** A execução 1 sai como registrada. Nenhuma das duas é escolhida depois de ver o resultado, e isso fica declarado antes.
3. **Regra de parada.**
   - A execução 2 é a última.
   - Se nenhuma variação passar o portão, ou se uma classe ficar sem modelo aprovado, vale a execução 1 e a emenda se encerra.
4. **Conjunto de desenvolvimento** (`evaluation/desenvolvimento/`), com 30 perguntas inventadas, de D01 a D30:
   - 8 controles positivos: valor, dependência semântica baixa, uma leitura, sem janela e sem data fixa. Os únicos literais admitidos no SQL são ano, trimestre e sigla de UF. Aceitei a sigla de UF como convenção porque a pergunta dá o nome do estado, e a `dim_uf` traz o nome ao lado da sigla: o SQL chega à sigla pelo esquema. Na seleção e na execução 1, nenhum SQL filtrou UF por sigla. Os 7 filtros de UF com literal eram `uf = 'BR'`, que não existe na `dim_uf`.
   - 6 controles negativos, de abstenção evidente pelo esquema.
   - 16 mistas, que espelham o teste no tipo de acerto, na dependência semântica e na estrutura do SQL, com um piso de estrutura medido por script.
   - O gabarito sai do DuckDB (`scripts/gerar_gabarito_de_desenvolvimento.py`).
   - O `scripts/validar_desenvolvimento.py` confere que nenhuma pergunta repete as 41 pelo enunciado (Jaccard abaixo de 0,6), pelos embeddings do RAG (cosseno de 0,78 para cima vai a revisão) e pelo SQL.
   - Os fatos regulatórios das perguntas foram confirmados na fonte. Por exemplo, o porte 0 como "indisponível" vem da seção C das Instruções de Preenchimento do Documento 3040.
5. **Variações cumulativas**, em `assistente/variacoes.py` e `assistente/variacoes.yml`. Vence a primeira que passa o portão.
   - **V−1:** o instrumento exato da execução 1.
   - **V0:** a correção mecânica. As chaves ganham prefixo de letra (`a_interpretacao`, `b_sql`, `c_abstem`, `d_motivo`), a leitura confere a ordem e devolve os nomes registrados, a abstenção vira booleano mais motivo, e o SQL não vazio roda mesmo com a abstenção marcada.
   - **V1:** a V0 mais o critério de abstenção e dois exemplos num esquema de brinquedo, na mensagem do usuário, depois da pergunta, iguais nas quatro condições.
   - **V2:** a V1 mais um campo de plano antes do SQL, com no máximo 1.500 caracteres. O limite vai só no esquema da gramática, e não testei se o Ollama 0.40.4 o respeita; nas fumaças, os planos tiveram de 157 a 367 caracteres.
   - **V3:** a V2 mais uma nova tentativa, uma só, quando o SQL dá erro de SQL, para na guarda ou volta vazio ou só com nulos. A nova resposta substitui a anterior, e a segunda chamada vê só a tentativa válida.
   - **V4:** a V3 mais as colunas que ligam cada fato às dimensões, no bloco do esquema.
6. **Triagem em duas etapas.**
   - Cada variação roda primeiro nos dois modelos registrados.
   - Se um deles reprova, os outros candidatos da classe dele rodam a mesma variação antes de ela ser descartada.
   - Escolhida a variação, os candidatos que faltam rodam só ela, para a re-seleção.
7. **Re-seleção no conjunto de desenvolvimento, só na condição A**, entre os candidatos que passam o portão com a variação escolhida. Fica o de mais perguntas certas em cada classe, com desempate pela menor VRAM. Isso mantém o viés conservador contra a H1 e a H2 que o [ADR 0026](0026-modelos-do-experimento-escolhidos-pela-condicao-a.md) já declarou.
8. **O portão** (`evaluation/portao.yml`, medido por `scripts/medir_portao.py`). Ele é medido por modelo, com as 5 seeds e a maioria de 3 em 5, nas quatro condições somadas, e pendente conta como errado. Uma variação passa quando todas as métricas passam:

   | Métrica | O que mede | Limite |
   |---|---|---|
   | G0 | Erro de formato, corte pelo limite de tokens ou estouro de contexto, em cada condição, e o modelo inteiro na GPU | até 5% |
   | X | Execuções que terminam com valores, nas perguntas respondíveis | pelo menos 70% |
   | Y1 | Controles positivos certos pela maioria | pelo menos 50% |
   | Y2 | Mistas de valor certas pela maioria | pelo menos 25% |
   | Z | Abstenção nos controles negativos | pelo menos 70% |

   **Sanidade.**
   - A V−1 tem de reprovar.
   - O teto das mistas de valor, na variação que venceu, não passa de 85% em nenhum dos dois modelos da primeira etapa.
   - Se a sanidade falhar, a triagem para, o conjunto é revisto por errata e a triagem recomeça pela V−1.
   - O conjunto pode ser revisto uma vez só. A versão dele (`metadata.versao` do `perguntas.yml`) é 1 mais as erratas de revisão, marcadas com `revisao_do_conjunto: true`, e não passa de 2; o código confere isso. Uma errata que só corrige um comentário não conta como revisão. Se a sanidade falhar de novo, vale a execução 1.

   Fora o G0, nenhuma métrica aparece por condição durante a triagem. O executor também não mostra a condição, o desfecho nem o tempo de cada execução no conjunto de desenvolvimento: a abstenção é mais rápida e o tempo a denunciaria.
9. **Uma issue nova (#118), na mesma branch**, com uma PR só no fim.
10. **O revisor é um agente fixo do projeto.** Ele revisou o plano e as fases 1 a 3. Nas fases seguintes, a revisão é o `/code-review` do fluxo da issue, que eu disparo, e não o agente a cada fase (decidi em 2026-10-15, depois da revisão da fase 3).

### As decisões que vieram das revisões e da fumaça

11. **O exemplo de abstenção vem primeiro**, e a mensagem fecha com "Agora responda à pergunta: {pergunta}". Do outro jeito, o último texto antes da geração seria uma abstenção do brinquedo, e o modelo tende a repetir o que está perto do fim do prompt (Zhao et al., *Calibrate Before Use*, 2021).
12. **O DuckDB roda com uma thread só**, no banco do assistente e no gerador do gabarito de desenvolvimento.
    - **Por quê.** Com várias threads, a ordem das linhas sem `order by` e os últimos dígitos de agregações em ponto flutuante podem mudar entre duas rodadas, e a documentação do DuckDB recomenda `set threads = 1` para isso.
    - **O custo, medido pelo revisor.** Os 79 SQL dos dois gabaritos rodam em até 3 s. Dos SQL que os modelos escreveram na execução 1 e na seleção, 3 passariam do limite de 30 s com uma thread, e os três já estavam errados.
    - **Na V−1.** Ela também roda com uma thread, então refazer a V−1 hoje pode mudar o resultado de um SQL lento ou sem `order by`.
13. **Com a abstenção marcada, um SQL que falha deixa a abstenção valer.** O SQL que roda continua ganhando da abstenção. Na V3 e na V4, isso vale depois da nova tentativa. O SQL que falhou fica no registro (`sql_da_abstencao`).
14. **O modelo é recarregado antes de cada execução.** A fumaça de 2026-10-15 mostrou que o Gemma só repete a resposta com a mesma seed quando parte do modelo recém-carregado. Qualquer chamada antes muda a saída, até a mesma pergunta repetida ou uma chamada mínima e fixa. O Qwen repete sempre.
    - **O teste.** Num diagnóstico na minha máquina, fora do repositório, descarreguei o modelo antes de cada execução, com outra execução no meio, em três perguntas e nas condições A e D: a execução inteira se repetiu nos 6 casos. A fumaça refeita com a recarga, que grava `recarrega_a_cada_execucao` no relatório, repetiu as três execuções da reprodução nos dois modelos.
    - **O custo.** A recarga do Gemma leva cerca de 4,4 s, e a espera dela não entra no tempo gravado da execução. A mediana gravada na V4 foi de 18,4 para 19,1 s no Gemma e de 15,3 para 17,5 s no Qwen.
    - **A causa provável** é a dependência da saída em relação ao estado do lote e do cache, que existe mesmo com temperatura baixa (He, *Defeating Nondeterminism in LLM Inference*, Thinking Machines, 2025).
15. **A execução 2 só roda o que a triagem escolheu.** No conjunto de teste, o executor se recusa a rodar:
    - sem o `evaluation/desenvolvimento/triagem.json` na situação "escolhida";
    - com uma variação ou modelos diferentes dos que a triagem escolheu;
    - com `--candidato` ou `--pasta`.

    A execução 2 grava em `data/experimento/execucao-2/` e recebe os mesmos trechos da execução 1.
16. **Os textos do `hipoteses.yml` que mudam com a variação estão escritos antes da triagem**, em `evaluation/hipoteses_por_variacao.yml`:
    - o fluxo, as falhas e o contexto do modelo;
    - os modelos, com a re-seleção no conjunto de desenvolvimento;
    - o que fica fixado antes da execução e a lista de ADRs;
    - o limite declarado da execução 2, com a origem do critério só da V1 em diante;
    - na V4, o bloco comum das condições;
    - as ressalvas de cada variação.

    A errata 6 só copia os valores da variação que venceu. O `experimento/hipoteses_por_variacao.py` confere três coisas: os valores, que, fora desses caminhos, o `hipoteses.yml` não mudou (por um sha256 do resto), e que copiar basta para cada variação. Ele roda no `validar_variacoes` e no executor, antes da execução 2.
17. **O corretor ganhou um desempate.** No `_identificar`, uma coluna de posição (1, 2, 3) empatava com a coluna do código ("01", "02", "03") em itens achados e vencia por ser a primeira. Agora vence a coluna com mais células iguais ao texto do gabarito.
    - **Quando.** A mudança veio depois de a execução 1 rodar e antes de ela ser corrigida às cegas.
    - **Sem efeito no que já foi corrigido.** O `scripts/analises/qa_corretor.py` corrige de novo, com o `_identificar` antigo e com o novo, as 1.025 execuções da seleção e as 1.640 da execução 1, e nenhuma correção muda. Ele também confere que a cópia antiga reproduz o defeito no caso de regressão do `validar_selecao`.
    - **O que fica de fora.** O conserto é parcial: se o modelo grava o código como número (2), as duas colunas empatam também nas células iguais, e a primeira continua vencendo.
18. **O `num_ctx` de cada modelo e variação** sai de `scripts/dimensionar_variacoes.py`, para `evaluation/desenvolvimento/dimensionamento.json`. É o menor múltiplo de 4.096 que comporta três coisas no pior caso:
    - a segunda chamada de D;
    - a chamada da nova tentativa;
    - a estimativa em caracteres que o cliente confere antes do envio.

    A estimativa entrou porque, no Granite 4.2 8B, ela passava do `num_ctx` na pior segunda chamada e daria um erro de contexto falso. Ele foi para 57.344, como os dois Ministral 3 na V4. O Gemma e o Qwen ficam em 53.248 em todas as variações. O pior caso do Gemma na V4 tem 53.043 tokens. Para o modelo registrado, o `num_ctx` do `parametros.yml` tem de bater com o dimensionamento.

### O que fica declarado junto do resultado

- **A origem das regras da V1.** O critério de abstenção e os exemplos saíram da leitura das saídas da execução 1 no conjunto de teste, por mim, e não dos modelos. O texto não traz fato do domínio e não foi afinado nas 41 perguntas, mas a ideia veio de ver as falhas no teste.
- **O critério tem efeito diferente por condição.**
  - O trecho "ou quando o contexto diz que ele não vale para esse uso" é igual nas quatro condições, mas só encontra a que se referir em B, C e D.
  - Ele pode aumentar a abstenção indevida nas 10 perguntas de valor com ressalva e ajudar B e D nas 2 de abstenção.
  - O validador garante que o texto é o mesmo, não que o efeito seja neutro, e o portão somado não detecta essa diferença.
- **O conjunto de desenvolvimento é mais simples que o teste na estrutura do SQL.** Nas 15 mistas com SQL, há junção em 5, CTE em 10 e comparação no tempo em 8, contra 51, 49 e 34 das 56 consultas do teste. O teto controla a facilidade pelo acerto, não pela estrutura, e o ganho das junções da V4 quase não tem onde aparecer no conjunto.
- **A H1 testa a ontologia inteira no contexto.** A condição B recebe todos os itens da ontologia, não os relevantes para a pergunta. Recuperar só os itens relevantes ficou fora desta emenda.
- **A re-seleção conta, na prática, 19 das 30 perguntas.** Com pendente contando como errado, 11 perguntas nunca saem certas pelo script: as 6 negativas, a D30 de abstenção e as 4 com ressalva. Nenhuma pergunta de valor do conjunto pede leitura declarada, então Y1 e Y2 são mecânicos. Quem cobre o comportamento de abstenção é o Z.
- **A sanidade da V−1 informa pouco.** A V−1 deve reprovar pelo X, pela própria mecânica da abstenção. Quem mede se o conjunto está fácil demais é o teto.
- **A nova tentativa não cobre o tempo esgotado.** Ela vale para erro de SQL, guarda e resultado vazio.
- **A instrução de sistema diz que o SQL roda uma vez.** Ela é a do `assistente/modelo_de_prompt.yml`, congelado, e isso é falso na V3 e na V4. O pedido de nova tentativa é explícito e resolve na prática.
- **As junções da V4** ligam só fato com dimensão, pela primeira coluna da dimensão. Não há junção de fato com fato nem por `ano`.
- **O Ministral 3 14B fica fora da triagem.** Ele não cabe inteiro na GPU de 12 GB com o `num_ctx` do experimento: na seleção, parte dele rodou na CPU. A classe 14b fica só com o Gemma 4 12B.
- **Os modelos podem mudar entre a execução 1 e a 2**, pela re-seleção.
- **As ressalvas de cada variação estão escritas antes da triagem**, em `declaracoes` do `evaluation/hipoteses_por_variacao.yml`, e saem com o resultado da execução 2 sem mudar uma palavra.
- **A decisão 2 do ADR 0031 não valia para o Gemma.** Ela dizia que, com a seed fixa, rodar de novo dá o mesmo. Isso não vale para o Gemma sem a recarga, e a execução 1 rodou sem ela. Cada execução continua sendo uma amostra válida, e a ordem das condições é sorteada, então a diferença vira ruído e não viés. Mas uma execução da execução 1 refeita hoje pode sair diferente.
- **O replay da V−1.** O `scripts/analises/replay_v_menos_1.py` passa as 1.640 execuções da execução 1 pelo `responder` da V−1, com as respostas gravadas do modelo, e compara mensagens, resposta, erro e resultado do SQL.
  - Em 2026-10-15, com uma thread só no DuckDB, 1.639 saíram idênticas.
  - A outra mudou só porque o resultado do SQL mudou: um SQL sem `order by`, cortado no limite de linhas.
  - Nenhuma diferença veio do código.
- **O poder.**
  - Com 41 pares e o alfa mais exigente do Holm (0,0125), o efeito mínimo que o McNemar detecta com 80% de poder fica entre 25 e 35 pontos percentuais, conforme a parcela de pares discordantes (de 30% a 50%).
  - A H4 tem um piso: mesmo com as 41 perguntas concordantes entre D e a outra condição, o p da não inferioridade fica entre 0,015 (20 ou 21 acertos) e 0,093 (1 ou 40 acertos), conforme a taxa de acerto. Com acerto muito baixo ou muito alto, ele passa de 0,05.
  - A margem de −5 pontos não muda.

## Alternativas descartadas

- **Consertar o prompt e rodar de novo no teste.** Seria ajustar o método ao resultado nas próprias 41 perguntas, o que o ADR 0030 já tinha avisado.
- **Descartar a execução 1.** Ela é o resultado registrado. Escondê-la seria escolher a execução depois de ver o resultado.
- **Escolher a variação pelo acerto por condição.** Abriria espaço para escolher a variação que favorece uma hipótese.
- **Variações fora do cardápio, ou triagem sem limite.** Sem um cardápio fechado e uma regra de parada, a triagem viraria busca até dar certo.
- **Chamada mínima e fixa antes de cada execução, em vez da recarga.** Testei, e as cinco respostas do Gemma saíram diferentes.
- **Aceitar a falta de reprodução do Gemma e só declarar.** A recarga custa pouco e faz a retomada depois de um erro de servidor repetir o que teria saído.
- **Manter várias threads no DuckDB.** A execução poderia mudar entre duas rodadas por um motivo que não é o modelo.

## Consequências

- **A errata 5 congela tudo antes da primeira execução da triagem:**
  - o conjunto de desenvolvimento;
  - o portão;
  - as variações;
  - os textos prontos do `hipoteses.yml`;
  - o executor, o `medir_portao` e o dimensionamento (`dimensionamento.json`);
  - o que forma o prompt: o esquema, a ontologia, o código do contexto e a busca do RAG.

  Só o núcleo entra, o que muda o resultado: o que o modelo vê e como a resposta é corrigida e decidida. Os validadores e os scripts que geram ou dimensionam ficam fora (decidi em 2026-10-15, depois de ver que congelar tudo só atrapalhava): o CI os confere, e consertá-los não muda o resultado. A lista inteira está em `CONGELADOS_ANTES_DO_EXPERIMENTO`, no executor, e ele se recusa a rodar sem ela. O executor e o `medir_portao` também conferem que os Parquets locais são os do `esquema_estrela/manifesto.json` congelado e que as respostas do conjunto de desenvolvimento são do mesmo mês do retrato.
- **O congelamento trava outras issues.** A ontologia, o `validar_gabarito` (os tipos do bloco do esquema), o `validar_perguntas` (a leitura das perguntas) e o retrato do esquema estrela ficam congelados até o fim da execução 2; uma mudança neles por outra issue pede errata. O `scripts/resumir_experimento.py` entra na errata 6, antes da execução 2.
- **A errata 6 vem depois da triagem e registra:**
  - a variação escolhida;
  - os modelos e o `num_ctx` no `assistente/parametros.yml`;
  - o `triagem.json`;
  - os textos do `hipoteses.yml` daquela variação.
- **A triagem custa umas 4 h por modelo e variação** (600 execuções de 19 s, mais a recarga), de madrugada, na minha máquina.
- **O resumo, o validador e a correção às cegas recebem a execução**, 1 ou 2, e cada uma tem a sua pasta.
- **A página e o relatório cobrem as duas execuções.** A execução 1 aparece com o instrumento falho, e a execução 2 com as afirmações confirmatórias.
- **Se a triagem parar pela regra de parada, o resultado publicado é só o da execução 1**, com este ADR explicando por quê.
