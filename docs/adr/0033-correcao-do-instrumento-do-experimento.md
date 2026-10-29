# ADR 0033: A execução 3 do experimento roda com o esquema descrito e a ontologia recuperada por pergunta

**Status:** Aceito
**Data:** 2026-10-23, com a versão do Ollama em 2026-10-24 e o resultado em 2026-10-28

## Contexto

A execução 2 ([ADR 0032](0032-emenda-do-instrumento-do-experimento.md)) rodou com o instrumento consertado, a V4, e nenhuma hipótese foi sustentada. O conserto tirou a abstenção do caminho, mas os dois modelos acertaram de 0 a 3 das 41 perguntas em qualquer condição. Com tão poucos acertos, quase não há par discordante, e o experimento não separa o efeito da ontologia do efeito dos documentos.

Duas causas aparecem no desenho do contexto:

- **O esquema ia cru nas quatro condições:** tabela, coluna e tipo, com as junções da V4, mas sem dizer o que cada coluna guarda. O modelo adivinhava o significado das colunas.
- **A ontologia entrava inteira em B e D:** 147 itens, uns 35 mil tokens, mais de dez vezes o resto do prompt. Para um modelo de 9 a 12 bilhões de parâmetros, o item que importa se perdia no ruído.

A revisão da PR #119 também deixou pendências: a interrupção do SQL no DuckDB, que travou a execução 2 por 27 minutos na Q29; um autoteste que faltava no validador; os números da execução 1 escritos à mão no resumo; e o `metadata.versao` sem uso no conjunto de desenvolvimento.

## Decisões

Decidi em 2026-10-23, no meio-termo entre o conserto mínimo e uma nova seleção dos modelos:

1. **A execução 3 é a confirmatória.** Uma errata do `evaluation/hipoteses.yml`, gravada antes de rodar, descreve o instrumento novo. As execuções 1 e 2 ficam publicadas como foram registradas, e o limite declarado da execução 2 fica guardado em `evaluation/experimento/execucao-2/limite_declarado.txt`, para ela continuar batendo com o registro.
2. **Duas variações novas, cumulativas** (`assistente/variacoes.py`):
   - **V5:** a V4 com a ontologia recuperada em B e D;
   - **V6:** a V5 com o esquema descrito nas quatro condições.

   A ordem é forçada pelo contexto: o pior caso da V4 ocupava 53.043 dos 53.248 tokens do `num_ctx`, e as descrições antes do recorte da ontologia passariam do limite. A execução 3 roda na V6.
3. **O esquema descrito tem só a forma.** Uma frase por tabela, com o que uma linha representa, e uma por coluna, com o que ela guarda e a unidade, em `assistente/esquema_descrito.yml`, iguais em A, B, C e D. Nada de aviso, regra de uso ou definição tirada da ontologia, que continua só em B e D: assim a H1 mede a ontologia além do dicionário de dados. As duas ligações que não são igualdade de chave (`fct_populacao.ano` e `fct_renda_do_trabalho.fim_do_trimestre`) ficam na frase da coluna. Tirei também as frases que chegavam perto da ontologia: o "não é taxa" da carteira inadimplida, o "matrizes" das empresas ativas, a quebra no ativo problemático comparável, as listas de valores e a UF nula do PIX.
4. **A ontologia entra em B e D com os 5 itens mais próximos da pergunta** (`rag/ontologia.py`). Os 147 itens viram embeddings na memória, com o modelo do RAG, sem índice gravado e sem tocar no `rag/manifesto.json`. O texto de cada item é o YAML que vai no prompt. Os itens são buscados uma vez por pergunta, gravados, iguais em B e D e nos dois modelos, e os ids vão para o registro de cada execução.

   O número saiu da cobertura dos ids do campo `fonte` nas 30 perguntas de desenvolvimento, sem olhar as 41 do teste (`scripts/analises/cobertura_da_ontologia.py`):

   | Itens por pergunta | Cobertura média | Perguntas cobertas por inteiro (de 28) | Tokens do maior bloco |
   |---:|---:|---:|---:|
   | 1 | 46,4% | 10 | 656 |
   | 3 | 60,7% | 14 | 1.732 |
   | 5 | 69,6% | 17 | 2.079 |
   | 12 | 69,6% | 17 | 4.704 |
   | 20 | 76,8% | 20 | 8.177 |
   | 30 | 89,3% | 25 | 11.174 |

   A curva fica plana de 5 a 12 itens, e 5 iguala B aos 5 trechos de C, o que deixa a H3 equilibrada. Um texto compacto do item (rótulos, definição e valores) cobriu menos: 60,7% com 5 itens.
5. **A checagem no conjunto de desenvolvimento informa e não barra.** A V4, a V5 e a V6 rodaram só no Gemma, com uma seed, e o resumo soma as quatro condições, sem mostrar qual acerta mais (`scripts/analises/medida_do_desenvolvimento.py`):

   | Variação | Certas, de 120 | Controles positivos | Perguntas mistas certas | Abstenções | Erros |
   |---|---:|---:|---:|---:|---|
   | V4 | 44 | 31 de 32 | 13 de 64 | 41 | 2 de SQL |
   | V5 | 40 | 32 de 32 | 8 de 64 | 55 | nenhum |
   | V6 | 56 | 32 de 32 | 24 de 64 | 38 | nenhum |

   Os controles negativos ficaram quase todos pendentes, porque a abstenção correta depende da correção às cegas, que não fiz nesta checagem. As três variações rodaram em 35, 22 e 19 minutos.
6. **O conserto do SQL é o simples.** Esgotado o tempo na busca das linhas, o `count(*)` do total não roda. Com tempo sobrando, ele ganha um relógio novo, só com o que resta, e com menos de 0,05 s conta como tempo esgotado. Um teste com banco espião no `validar_assistente` prova que o `count(*)` não roda depois do tempo; o `executar` antigo reprova nele.
7. **O Ollama da execução 3 é o 0.40.9** (decidi em 2026-10-24). O app se atualizou sozinho da 0.40.4, a versão das execuções 1 e 2. Em vez de voltar à versão antiga, registrei a versão de cada execução em `experimento/execucoes.py`: o executor confere a da execução que roda, e o `validar_experimento` confere a gravada em cada resultado. As hipóteses comparam condições dentro de uma execução, na mesma versão.
8. **O `num_ctx` continua em 53.248.** O maior prompt estimado da V6 em D fica em uns 10,5 mil tokens.
9. **A comparação entre execuções é descritiva.** A página e o notebook mostram as perguntas certas por execução, modelo e condição, lado a lado. Nenhum teste compara uma execução com outra.

O mapa das execuções (`experimento/execucoes.py`) junta, para cada número, a variação, a pasta local, a versão do Ollama e o título. O executor, a correção às cegas, o resumo, o validador, o QA e o notebook leem dele, e a confirmatória é a mais nova publicada.

## Resultado da execução 3

A execução 3 rodou em 2026-10-24, no commit `101173c`: 820 execuções por modelo, sem repetição por erro de servidor e sem trava. O Gemma levou 5h01, e o Qwen, 3h57. A correção às cegas julgou só o que decide a maioria, como na execução 2.

Perguntas certas, de 41:

| Modelo | A | B | C | D |
|---|---:|---:|---:|---:|
| Gemma 4 12B, execução 3 | 6 | 7 | 5 | 8 |
| Gemma 4 12B, execução 2 | 3 | 1 | 3 | 2 |
| Qwen 3.5 9B, execução 3 | 2 | 2 | 3 | 2 |
| Qwen 3.5 9B, execução 2 | 2 | 3 | 1 | 0 |

- **Nenhuma hipótese foi sustentada, nos dois modelos.** Todos os intervalos de Newcombe cruzam o zero. O menor p ajustado é o da H4 no Gemma, 0,294.
- **A correção ajudou o Gemma e não o Qwen.** O Gemma passou de 39 para 101 execuções certas, de 820, e de 1 a 3 para 5 a 8 perguntas por condição. O Qwen passou de 33 para 38 execuções certas.
- **Ainda há poucos acertos para separar as condições.** Com 5 a 8 perguntas certas, quase não há par discordante.

Os números completos estão em `evaluation/experimento/execucao-3/`, na página [`docs/experimento.md`](../experimento.md) e no notebook `notebooks/experimento.ipynb`.

## Limites declarados junto do resultado

- A V6 foi desenhada depois de ver o piso da execução 2 no teste. As frases e o número de itens não foram afinados nas 41 perguntas: as frases saíram do dicionário de dados do dbt e do retrato, e o número, só do conjunto de desenvolvimento.
- O Ollama mudou da 0.40.4 para a 0.40.9 entre a execução 2 e a 3, junto com o instrumento.
- **Respostas cortadas no limite de tokens.** De 9% a 12% das execuções terminam com a resposta cortada nos 2.048 tokens: 76 no Gemma e 97 no Qwen. Quase sempre o corte é na segunda chamada, quando o modelo copia para os valores o resultado inteiro do SQL, de 24 a 100 linhas. O defeito já existia na execução 2, com 61 e 74 cortes, e fica como limite do instrumento.
- A checagem no desenvolvimento usou uma seed e um modelo. Ela não se compara direto ao teste, e o conjunto de desenvolvimento é mais simples que o teste na estrutura do SQL.

## Alternativas descartadas

- **Descrever o esquema com a ontologia inteira em B e D.** Passaria do `num_ctx`.
- **Tirar as descrições da ontologia,** pela coluna ou pela notação do item. Levaria o conteúdo de B para A e esvaziaria a H1.
- **Reaproveitar o `_marts.yml` do dbt.** Vários textos de lá já trazem avisos da ontologia, que passariam para A.
- **Recuperar 20 ou 30 itens da ontologia.** Mais cobertura, mas de volta parte do ruído, e B com quatro a seis vezes o contexto de C.
- **Um vigia com thread de trabalho para o SQL.** Cobriria uma trava sem uso de CPU que o repositório não comprova, a umas 3 h de trabalho e com mais risco no lock.
- **Voltar o Ollama para a 0.40.4.** Mantinha o instrumento igual ao da execução 2, mas pedia reinstalar e conter a atualização automática do app.
- **Um teste pareado entre as execuções 2 e 3.** A diferença mistura o instrumento e a versão do Ollama, e não é uma hipótese registrada.

## Consequências

- O registro ganhou a errata do `assistente/parametros.yml` (V6), a do `evaluation/hipoteses.yml` e o resultado da execução 3.
- As respostas cortadas no limite de tokens pedem uma issue própria: a segunda chamada não precisa copiar o resultado inteiro do SQL.
- Separar o efeito do contexto ainda pede modelos maiores ou perguntas mais simples. Fica como próximo passo, e não como conclusão.
