# ADR 0032: A execução 2 do experimento roda com o instrumento consertado, escolhido por custo-benefício

**Status:** Aceito
**Data:** 2026-10-15, revisto em 2026-10-17

## Contexto

A execução 1 do experimento 2x2 ([ADR 0031](0031-execucao-e-analise-do-experimento.md)) rodou as 1.640 execuções do registro em 2026-10-14 e 2026-10-15, sem nenhuma repetição por erro de servidor, e falhou no controle de qualidade do instrumento.

- **Abstenção em massa.** O Gemma 4 12B se absteve em 713 das 820 execuções, e o Qwen 3.5 9B, em 817. A abstenção foi quase igual nas quatro condições. Pelo script, 1 execução saiu certa em 1.640, e quase não há par discordante entre as condições.
- **A causa é mecânica.** A gramática do Ollama 0.40.4 gera as chaves do JSON em ordem alfabética: 1.637 das 1.640 primeiras chamadas começam por `"abstencao"`. O modelo escrevia o motivo de não responder antes de interpretar a pergunta e antes do SQL. O mesmo aconteceu na seleção (#48).

A execução 1 sai como registrada, julgada às cegas e analisada, em `evaluation/experimento/execucao-1/`, com nenhuma hipótese sustentada.

## O caminho que comecei e parei

Primeiro montei uma emenda com rigor de pesquisa: um conjunto de desenvolvimento de 30 perguntas inventadas, seis variações do instrumento, um portão com triagem e re-seleção dos modelos, dezenas de arquivos congelados por errata e a recarga do modelo antes de cada execução. A triagem chegou a medir três variações, nas 30 perguntas, com 5 seeds e as quatro condições somadas:

| Variação | O que muda | Gemma: X / Y1 / Y2 / Z | Qwen: X / Y1 / Y2 / Z |
|---|---|---|---|
| V−1 | o instrumento da execução 1 | 36 / 84 / 4,5 / 100 | 0 / 0 / 0 / 100 |
| V0 | chaves com prefixo, na ordem certa | 59 / 91 / 36 / 77 | 47 / 66 / 16 / 76 |
| V1 | V0 mais critério de abstenção e exemplos | 64 / 97 / 36 / 71 | não terminou |

X é a parcela de execuções que respondem com valores nas perguntas respondíveis; Y1 e Y2, os controles fáceis e as perguntas difíceis certos pela maioria; Z, a abstenção nas perguntas impossíveis. Os números mostram que o conserto funciona: o Gemma passa de 36% para 64% de respostas, e o acerto dos controles sobe para 97%.

O resto da triagem pedia até 35 h de máquina, e a re-seleção mais 6 h, para chegar a um resultado do mesmo tipo. O projeto simula um case de negócios, em que tempo, escopo e orçamento se equilibram, e esse custo não se paga.

## Decisões

Decidi em 2026-10-17:

1. **A execução 2 roda com a V4**, a variação com todos os consertos (`assistente/variacoes.py`):
   - as chaves do JSON com prefixo, na ordem interpretação, plano, SQL, abstenção e motivo;
   - o critério de abstenção e dois exemplos num esquema de brinquedo, com o de abstenção primeiro e a mensagem fechando com a pergunta;
   - uma nova tentativa quando o SQL dá erro ou volta vazio;
   - as colunas que ligam os fatos às dimensões no bloco do esquema.

   O texto é o mesmo nas quatro condições. A V4 passou na fumaça ao vivo nos dois modelos, sem chave fora da ordem. Os modelos continuam os da #48, sem re-seleção.
2. **O congelamento por errata do código sai.** O executor grava o commit em cada `ambiente.json` e se recusa a rodar o teste com mudança sem commit. O registro fica com o pré-registro da #47, os arquivos da #46, da #48 e da #49 e o resultado da execução 1. Isso substitui as decisões 4 e 9 do ADR 0031.
3. **Sem recarga do modelo.** O Gemma só repete a resposta com a mesma seed quando parte do modelo recém-carregado, mas a recarga custa umas 2 h na execução 2. Cada execução continua sendo uma amostra válida e a ordem das condições é sorteada, então a diferença é ruído e não viés. Uma execução refeita depois de erro de servidor pode sair diferente. Isso revê a decisão 2 do ADR 0031.
4. **A correção às cegas da execução 2 julga só o que decide a maioria**, como na seleção. Nas perguntas já decididas, a contagem de 0 a 5 sai como mínima; o acerto de cada pergunta não muda. Isso revê a decisão 1 do ADR 0031 para a execução 2.
5. **O fechamento é a página `docs/experimento.md` e o notebook**, sem o PDF do Quarto. Isso revê a decisão 6 do ADR 0031.

O que fica da emenda: as variações, o conjunto de desenvolvimento com o gerador e o validador, o replay da V−1 contra a execução 1 (`scripts/analises/replay_v_menos_1.py`, 1.639 de 1.640 execuções iguais), o corretor com o desempate entre posição e código (`scripts/analises/qa_corretor.py`, sem mudança no que já foi corrigido) e o DuckDB com uma thread só.

## Limites declarados junto do resultado

- O instrumento da execução 2 foi escolhido depois de ver as saídas da execução 1 no teste, e a V4 não foi medida inteira no conjunto de desenvolvimento.
- O critério de abstenção é o mesmo texto nas quatro condições, mas a cláusula sobre o contexto só tem a que se referir em B, C e D.
- O conjunto de desenvolvimento é mais simples que o teste na estrutura do SQL.
- O `num_ctx` de 53.248 dos dois modelos serve à V4: o pior caso medido do Gemma é de 53.043 tokens.

## Alternativas descartadas

- **Terminar a triagem e re-selecionar os modelos.** Mais 35 a 41 h de máquina para um resultado do mesmo tipo.
- **Rodar a execução 2 com a V1**, a melhor medida. O Gemma ainda se abstinha em 36% das perguntas respondíveis, e a V4 junta os consertos que atacam justamente isso.
- **Descartar a execução 1.** Ela é o resultado registrado e fica publicada com o defeito explicado.

## Consequências

- A execução 2 rodou as 1.640 execuções em `data/experimento/execucao-2/`, com os trechos da execução 1, em 2026-10-18. Levou umas 10 h, com até 32 s por execução nas perguntas mais pesadas, e não teve repetição por erro de servidor. Ela travou uma vez: na Q29, condição D, seed 5 do Gemma, o processo ficou 27 minutos parado, sem uso de CPU nem de GPU, dentro do SQL que passou do limite de 30 s. Parei o processo e retomei, e o executor refez só essa execução, que dessa vez passou. A interrupção do SQL no DuckDB fica para a issue de correção.
- Mudar o código depois não pede errata; o commit gravado diz com que código cada execução rodou.
- O resultado da execução 2 entra no registro por errata, como o da execução 1.
