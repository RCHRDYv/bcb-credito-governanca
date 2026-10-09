# ADR 0030: Os candidatos entram pelo contexto, o corretor compara por valor e a correção às cegas cobre só o que muda o acerto

**Status:** Aceito
**Data:** 2026-10-09

## Contexto

O [ADR 0026](0026-modelos-do-experimento-escolhidos-pela-condicao-a.md) definiu a regra da seleção dos dois modelos do experimento:
- as 41 perguntas na condição A;
- 5 execuções por pergunta, com acerto quando 3 ou mais acertam;
- o empate resolvido pela menor VRAM;
- o registro da versão, da quantização, dos parâmetros e do resultado de todos os candidatos.

O [ADR 0029](0029-assistente-local-com-ollama-e-proveniencia-pelo-codigo.md) entregou o mecanismo. Os parâmetros e o prompt ficaram provisórios, e a #48 é que os fixa.

Faltavam quatro coisas para a seleção rodar:
- **Um corretor.** O repositório não tinha código que comparasse uma resposta do modelo com o gabarito. O `scripts/validar_registro.py` só confere o `comparacao.yml` contra as respostas do próprio gabarito.
- **Os candidatos.** Os nomes se escolhem no momento da execução (ADR 0012), e eu os conferi no Hugging Face em 2026-10-09.
- **A correção às cegas.** A regra registrada manda eu conferir a ressalva, a abstenção e a leitura declarada (`hipoteses.yml`, `comparacao.correcao`). Na seleção são 1.025 execuções.
- **A ordem do congelamento.** Era preciso decidir o que se congela antes da seleção e o que se congela depois.

A seleção roda na minha máquina, na RTX 5070 de 12 GB, e não no CI.

## Decisões

Decisões que tomei em 2026-10-09, antes do código (comentário na #48).

1. **Regra de entrada pelo contexto publicado.**
   - O candidato precisa de pelo menos 65.536 tokens de contexto: o `max_position_embeddings` do `config.json` da revisão fixada, sem mudar o RoPE.
   - O mesmo modelo roda as quatro condições, e o prompt de D passa de 38 mil tokens (ADR 0029).
   - Saem o Phi-4, com 16.384, e o Qwen3-14B e o Qwen3-8B, com 40.960. Nenhum deles comporta D sem YaRN.
2. **Os candidatos, em 4 bits.**

   | Classe | Candidato | GGUF | Contexto |
   |---|---|---|---|
   | ~14B | Gemma 4 12B IT, QAT Q4_0 | `google/gemma-4-12B-it-qat-q4_0-gguf` | 262.144 |
   | ~14B | Ministral 3 14B Instruct 2512, Q4_K_M | `mistralai/Ministral-3-14B-Instruct-2512-GGUF` | 262.144 |
   | ~7 a 8B | Qwen3.5-9B, Q4_K_M | `unsloth/Qwen3.5-9B-GGUF` | 262.144 |
   | ~7 a 8B | Granite 4.2 8B, Q4_K_M | `ibm-granite/granite-4.2-8b-GGUF` | 131.072 |
   | ~7 a 8B | Ministral 3 8B Instruct 2512, Q4_K_M | `mistralai/Ministral-3-8B-Instruct-2512-GGUF` | 262.144 |

   O Qwen3.5-9B fica na beira da classe. A Qwen não lançou um 14B depois do Qwen3, e o Qwen3.5/3.6/3.8 pula de 9B para 27B. Tudo isso está em `evaluation/selecao.yml`.
3. **A versão exata é a do conteúdo.**
   - Cada candidato registra o repositório, a revisão, o arquivo e o sha256 do GGUF.
   - O executor lê o manifesto local do Ollama e para se o digest da camada do modelo não for o sha256 registrado.
4. **A seleção roda com a configuração do experimento.**
   - O cache KV fica em `q8_0`, com flash attention, igual para todos, e o `think: false` também.
   - O `num_ctx` de cada candidato sai do `tokenizer.json` da revisão fixada, sem rodar o modelo (`scripts.dimensionar_contexto`). É o menor múltiplo de 4.096 que comporta, no pior caso:
     - o maior prompt de D, com os trechos da busca das 41 perguntas;
     - o limite da resposta da primeira chamada;
     - o resultado no limite de linhas;
     - o limite da segunda resposta.
   - O resultado no limite de linhas é medido pela linha com mais tokens entre as respostas do gabarito, repetida 100 vezes.
   - A razão de caracteres por token da estimativa sai da mesma medida.
   - A VRAM do desempate é o `size_vram` do `/api/ps`, lido logo depois de carregar o modelo com esse `num_ctx` e antes das execuções.
   - Assim, o A da seleção é o A do experimento, e a VRAM medida é a que o experimento vai usar.
5. **O corretor compara por valor, sem olhar o nome da coluna** (`correcao/corretor.py`). O modelo dá nomes livres às colunas, e pedir os nomes no prompt vazaria a forma do gabarito.
   - **Valor.** Uma conferência procura, na tabela da resposta, uma célula dentro da tolerância da coluna do gabarito. Quando a linha do gabarito tem um texto ou uma data que só ela tem, como o mês de uma série, a janela ou a medida, a busca fica nas linhas da resposta que o trazem. Um valor igual em todas as linhas do gabarito, como uma mediana, vale em qualquer linha.
   - **Lista.** O item casa pelo código ou pelo nome, lido de uma coluna só da resposta, a que identifica mais itens. Cada coluna de valores tem de bater numa mesma coluna da resposta, com a mesma escala, em todos os itens.
   - **Ranking.** Os n primeiros do gabarito estão na resposta, com os valores certos, e nenhum outro item do gabarito aparece com valor que o poria entre eles fora da tolerância. Uma linha que não se identifica com item do gabarito, como um total ou o bloco de outra consulta na mesma tabela (Q28), não compete. A ordem sai dos valores: com os valores certos, a ordem é a do gabarito, e a troca dentro da tolerância é aceita.
   - **Conjunto.** Todos os itens, sem item a mais. Vale uma de três leituras:
     - os itens listados;
     - os marcados como verdadeiros numa coluna booleana;
     - os de um bloco da tabela em formato longo, as linhas com o mesmo texto numa coluna que não é a do item, como "tipo | modalidade | ganho" com os dois conjuntos da Q21;
     - num conjunto por limiar, a tabela inteira com os valores do filtro certos, porque então os próprios números põem cada item do lado certo.

     Um item na zona de indiferença pode estar ou não. Uma linha que não se identifica com nenhum item, como um total, não conta como item a mais.
   - **Escala.** Em reais e contagens, a resposta pode vir em mil, milhão, bilhão ou trilhão. Em percentual e pontos, pode vir como fração. O número é convertido antes da comparação (`comparacao.tolerancia.escala`). Inteiro pequeno, abaixo de 10.000, não ganha escala: um ano ou uma posição, vezes 10^9, não é uma carteira. Também aceito texto em formato brasileiro, com R$, % e palavra de escala.
   - **Classificação** (Q08). A classificação precisa estar nos valores, como texto: sim ou não, verdadeiro ou falso, ou a palavra do nome da coluna ("acima", "abaixo"). Número e marca de uma letra (0, 1, s, n) só contam numa coluna inteira de marcas, nunca numa célula solta. Na zona de indiferença, qualquer uma vale.
   - **Leitura e janela.** A resposta bate com uma leitura, numa janela, quando cumpre todas as conferências de todas as consultas dela.
6. **Q28 e Q30: o WITH basta.** O fluxo registrado continua com um SQL só, e o modelo pode juntar as partes com WITH ou UNION. O corretor procura as conferências de todas as consultas da leitura na tabela única da resposta. Isso fecha a consequência que o ADR 0029 deixou para a #48.
7. **A situação de cada execução** (`correcao/acerto.py`):
   - **errado:** erro da execução, abstenção numa pergunta com resposta, resposta numa pergunta de abstenção, valores que não batem com nenhuma leitura, ou ressalva vazia numa pergunta de valor com ressalva;
   - **certo:** valores que batem, sem nada a julgar;
   - **pendente:** falta o julgamento da ressalva (valor com ressalva), da abstenção (abstenção) ou da leitura declarada (mais de uma leitura, ou janela em aberto).
8. **A correção às cegas cobre só o que muda o acerto** (`correcao/as_cegas.py`).
   - Uma pergunta com 3 execuções certas, ou que já não chega a 3, está decidida, e as pendentes dela não vão a julgamento. O resultado da seleção é o mesmo de julgar tudo.
   - A correção roda no terminal, um item por vez, embaralhada entre candidatos e perguntas por um identificador opaco, e é resumível.
   - O item mostra a pergunta, a rubrica e os campos da resposta, sem modelo, condição, SQL ou trechos. As citações (id da ontologia, documento, seção, página, trecho) saem do texto.
9. **O modelo de prompt congela como está.** Ajustar agora seria afinar sem dado novo, porque a fumaça só usou perguntas inventadas e as 41 não podem ser olhadas.
10. **Duas erratas no `registro.yml`.**
    - A primeira congela o `evaluation/selecao.yml` e o `assistente/modelo_de_prompt.yml` antes de qualquer execução contra o gabarito. O `scripts.selecionar_modelos` se recusa a rodar sem ela.
    - A segunda congela o `assistente/parametros.yml` final, com os dois escolhidos, e o `evaluation/selecao/resultado.json`.
11. **Tudo fica publicado no repositório.**
    - `evaluation/selecao/resultado.json` traz:
      - as execuções de cada pergunta e as perguntas certas;
      - os erros por motivo, a VRAM e o ambiente de cada candidato;
      - os escolhidos e os meus julgamentos.
    - `evaluation/selecao/execucoes.jsonl.gz` traz os registros completos.
    - A página `docs/selecao-dos-modelos.md` é gerada por script, sem número digitado.
12. **O desempate final.** Se a VRAM também empata, fica o primeiro da classe na lista do `selecao.yml`. O ADR 0026 não previa esse caso, e eu o fixo antes de ver resultado.

## Resultado medido

Rodei a seleção em 2026-10-09 na minha máquina, com o Ollama 0.40.1, o cache KV em `q8_0` e o `num_ctx` de 53.248 em todos os candidatos. As 1.025 execuções levaram cerca de 5 horas. O Ministral 3 14B levou 3,5 horas sozinho, com mediana de 38 s por chamada, contra 2 a 6 s dos outros: parte das camadas dele ficou na CPU. Corrigi às cegas 27 execuções, as únicas que ainda mudavam o acerto de alguma pergunta. A página completa, gerada por script, está em [`docs/selecao-dos-modelos.md`](../selecao-dos-modelos.md).

| Classe | Candidato | Perguntas certas | Quais | Abstenções | Na GPU | Total |
|---|---|---:|---|---:|---:|---:|
| ~14B | **Gemma 4 12B** | 3 de 41 | Q17, Q33, Q41 | 181 de 205 | 7,0 GiB | 7,0 GiB |
| ~14B | Ministral 3 14B | 2 de 41 | Q33, Q41 | 92 de 205 | 8,8 GiB | 12,6 GiB |
| ~7 a 8B | **Qwen3.5-9B** | 2 de 41 | Q17, Q41 | 204 de 205 | 6,2 GiB | 6,2 GiB |
| ~7 a 8B | Granite 4.2 8B | 2 de 41 | Q17, Q41 | 139 de 205 | 9,4 GiB | 9,4 GiB |
| ~7 a 8B | Ministral 3 8B | 1 de 41 | Q11 | 16 de 205 | 8,6 GiB | 8,6 GiB |

As abstenções contam todas as execuções, com as 10 das duas perguntas de abstenção. "Na GPU" é o `size_vram` do `/api/ps`, que decide o empate; "Total" é o `size`, e a diferença ficou na CPU.

Ficam o **Gemma 4 12B** e o **Qwen3.5-9B**, pela regra congelada na primeira errata. O Qwen3.5-9B empatou com o Granite 4.2 8B em 2 perguntas, e o desempate foi a menor VRAM. Os dois couberam inteiros na GPU, então o `size_vram` mediu o mesmo que o tamanho total.

**O resultado tem efeito chão, e eu o aceito como registrado** (decisão de 2026-10-09). Na condição A, só com o esquema, os candidatos acertaram de 1 a 3 das 41 perguntas:
- **A abstenção domina.** O Qwen3.5-9B se absteve em 204 das 205 execuções, e o Gemma 4 12B em 181. Os dois acertaram justamente as duas perguntas de abstenção (Q17 e Q41), e a escolha saiu sobretudo delas. A regra escolheu os modelos que mais se abstêm sem contexto.
- **Quem tenta errar o número.** O Ministral 3 8B quase não se abstém (16), mas 75 das execuções dele terminaram em erro de SQL e 48 em valor errado. Ele foi o único com uma pergunta de valor certa (Q11).
- **Conferi que é o modelo, e não o corretor.** Nas respostas com número que reprovaram, o erro está na resposta: a Q01 com as duas carteiras certas e sem a variação, que o gabarito registrado exige; a Q22 somando o PIX sem o filtro da pergunta; e a Q06 com as modalidades antigas no lugar dos códigos.
- **Não mudei a regra depois de ver o resultado.** Declarar a seleção inconclusiva com um critério novo, ou mexer no prompt para reduzir a abstenção, seria ajustar o método ao resultado no próprio conjunto de teste. O pré-registro existe para impedir isso.

**Consequências para o experimento (#50).**
- O viés da seleção pela condição A é ainda mais conservador do que o ADR 0026 previa: os escolhidos se abstêm em quase tudo sem contexto. Se a ontologia (B) ou os trechos (C) reduzirem a abstenção, a diferença aparece contra uma linha de base perto de zero.
- Com a condição A perto de zero, a H1 e a H2 podem dar certo por pouco que B e C acertem. Por isso, o tamanho de efeito com intervalo, que o pré-registro já exige, pesa mais que o p.
- A abstenção indevida é um resultado em si, e entra na análise por tipo de acerto da #50.
- O `num_ctx` de 53.248 foi medido com o cache KV em 8 bits. O experimento precisa do `ollama serve` com `OLLAMA_KV_CACHE_TYPE=q8_0` e `OLLAMA_FLASH_ATTENTION=1`, como a seleção (o cabeçalho do `assistente/parametros.yml` diz isso). Com o cache em 16 bits, o Gemma 4 12B passa a jogar camadas para a CPU, como o Ministral 3 14B jogou.

**Errata 3, do mesmo dia.** Depois da segunda errata, a revisão de código achou defeitos no corretor:
- a guarda de escala recusava qualquer inteiro abaixo de 10.000, e não só posição e ano;
- o menos Unicode não era lido;
- o "1.234" em texto não era lido como milhar;
- no ranking, um `uma_de` quebrava a checagem.

Corrigi, recorrigi as 1.025 execuções publicadas e regerei o resultado pelo `scripts.resumir_selecao --do-publicado`. Mudou uma execução só: a Q33 do Ministral 3 8B na seed 4 passou de errada para não julgada, porque a pergunta já estava decidida. Nenhuma pergunta mudou de acerto, e nenhum escolhido mudou. O `validar_selecao` agora recorrige os registros publicados e confere que dão o resultado congelado.

**Limite da regra de desempate.** O `size_vram` não conta a parte que fica na CPU. Um candidato que não cabe na GPU pareceria mais barato que um que cabe. Aqui não pesou: o empate do 8B foi entre dois modelos inteiros na GPU. A regra está congelada assim e fica declarada.

## Alternativas descartadas

**Manter os Qwen3 com YaRN.** Seria um RoPE diferente do publicado, a Qwen avisa que o YaRN piora textos curtos, e o suporte no Ollama é instável. Seria mais um parâmetro a declarar.

**Rodar todos e excluir depois o que não comporta D.** Gasta horas de GPU com quem não pode ganhar.

**Pedir os nomes das colunas no prompt.** Vazaria a forma do gabarito e mudaria o prompt a cada pergunta. O CLAUDE.md e o ADR 0029 proíbem afinar o prompt nas perguntas registradas.

**Ler a ordem do ranking pela ordem das linhas da resposta.** A resposta de uma leitura com várias consultas (Q28) junta totais e dois rankings numa tabela só, e a ordem das linhas não diz qual ranking é qual. Com os valores certos, a ordem já está dada.

**Corrigir tudo às cegas.** São centenas de julgamentos que não mudam o resultado.

**Só o script na seleção.** Desviaria da decisão 2 do ADR 0026, que manda usar a regra registrada inteira.

**Permitir vários comandos SQL.** Mudaria a guarda e o fluxo de duas chamadas, que estão no pré-registro.

**Ranking externo.** Já descartado pelo ADR 0012 e pelo ADR 0026.

## Consequências

**Positivas.**
- O CI confere o corretor nas 56 respostas do gabarito, disfarçadas de quatro jeitos, e contra a retirada de cada valor e de cada item conferido. O workflow é o `selecao.yml`.
- A #50 reaproveita o corretor, o acerto e a correção às cegas, e o `assistente/parametros.yml` já traz os dois modelos, cada um com o próprio `num_ctx`.
- Nada roda contra o gabarito sem o prompt e a configuração congelados, e o digest confere que o modelo carregado é o registrado.

**Negativas, e são reais.**
- **O corretor por valor é mais leniente que o casamento por nome.** Um valor que repete outro dentro da tolerância passa por coincidência. O controle negativo mostra três casos: a mediana da Q14, que é o valor da UF da mediana, e a razão nacional da Q15, a menos de 1% da de uma UF. Fora deles, retirar o valor conferido faz a leitura deixar de bater.
- **O corretor não lê o rótulo de um bloco.** Na tabela em formato longo, os blocos se separam pela coluna de texto, mas o corretor não sabe qual rótulo é de qual conjunto. Uma resposta da Q21 com os conjuntos certos e os rótulos "IP" e "fintech" trocados acerta, porque a correção às cegas da leitura declarada não olha os rótulos.
- **A terceira leitura do conjunto aceita a tabela inteira.** Uma resposta que despeja todos os itens com os números certos, sem dizer quais passam no limiar, acerta. Os números certos põem cada item do lado certo, mas a resposta não destaca o conjunto.
- **Os percentuais como fração e as palavras de escala ampliam a regra de escala do pré-registro.** O pré-registro fala em bilhões e trilhões de reais. A fração de um percentual é a mesma unidade em outra escala, e eu declaro isso junto do resultado.
- **O `num_ctx` pelo pior caso é alto.** A linha mais longa do gabarito, de definições, repetida 100 vezes, soma perto de 10 mil tokens. Isso empurra o `num_ctx` para perto de 53 mil, e um candidato de 14B pode precisar de parte das camadas na CPU, mais lento. Ficar abaixo do pior caso faria execuções de D virarem erro de contexto, contra D.
- **O dimensionamento conta os tokens sem o modelo de chat.** São 16 tokens por mensagem para o modelo de chat, uma estimativa. O `prompt_eval_count` de cada execução registra o valor real.
- **O tamanho de classe é aproximado.** O Gemma 4 12B tem 11,95B de parâmetros e o Qwen3.5-9B tem 9B: ficam nas classes de ~14B e ~7 a 8B pela proximidade, sem outro candidato oficial com contexto suficiente nesses tamanhos.
