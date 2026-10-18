# ADR 0031: O experimento roda com a pergunta por fora, julga tudo às cegas e congela o código da análise antes de rodar

**Status:** Aceito; as decisões 1, 2, 4, 6 e 9 foram revistas pelo [ADR 0032](0032-emenda-do-instrumento-do-experimento.md)
**Data:** 2026-10-14

## Contexto

O [ADR 0013](0013-experimento-2x2-ontologia-contra-documentos.md) definiu o experimento 2x2, e o `evaluation/hipoteses.yml` registrou antes de qualquer execução o método: as quatro condições, as 5 execuções por pergunta, a maioria de 3, os testes, o alfa, o Holm por modelo, a margem da H4 e a seed da simulação (#47, [ADR 0026](0026-modelos-do-experimento-escolhidos-pela-condicao-a.md)). A #49 entregou o assistente ([ADR 0029](0029-assistente-local-com-ollama-e-proveniencia-pelo-codigo.md)) e a #48 escolheu os dois modelos e escreveu o corretor ([ADR 0030](0030-selecao-dos-modelos-pelo-gabarito.md)).

O registro deixou em aberto o que só aparece na hora de rodar:
- **A correção às cegas.** O registro manda publicar quantas das 5 execuções acertaram, de 0 a 5, por pergunta, condição e modelo. O corretor da seleção só julga o que muda a maioria, e o resto ficaria pendente.
- **O erro de servidor.** O registro conta como erro a saída fora do formato, o tempo esgotado, o erro de SQL e o prompt maior que o `num_ctx`. O assistente tem um quinto tipo, `servidor`, que é falha da máquina e não do modelo.
- **A ordem das 1.640 execuções** (41 perguntas, 4 condições, 5 seeds, 2 modelos), que roda na minha máquina durante horas.
- **O código da análise.** O registro descreve os testes em texto. O código que os calcula ainda não existia.
- **A forma da publicação**, com o notebook que a issue pede.

## Decisões

Decisões que tomei em 2026-10-14, antes do código (comentário na #50).

1. **Julgo às cegas todas as execuções pendentes.**
   - A contagem de 0 a 5 sai exata, como o registro manda.
   - Execuções com a mesma visão cega viram um item só, e o julgamento vale para todas elas. A visão é o que o item mostra (pergunta, interpretação, valores, ressalva e abstenção, sem citações), mais os aspectos a julgar e as leituras que bateram.
   - O id do item leva a condição, mas é um hash e não a revela. Os itens vêm embaralhados pela visão.
   - Na seleção nada muda: sem condição, o id, o agrupamento e a fila são os mesmos de antes, e o workflow do experimento confere que o resultado publicado da seleção se refaz igual.
2. **Erro de servidor não é gravado.**
   - A execução entra no `data/experimento/repeticoes.json`, e o executor para.
   - Rodar de novo retoma pela mesma pergunta, seed e condição. Com a seed fixa, sai o que teria saído.
   - O resultado publica quantas repetições houve. Os quatro erros do registro continuam contando como erro.
3. **Notebook Jupyter** (`notebooks/experimento.ipynb`), com as saídas versionadas e a memória de cálculo. Ele importa o mesmo `experimento/estatistica.py` do resumo e lê só os arquivos publicados, então roda sem o Ollama e sem `data/`.
4. **O código da análise é congelado antes da primeira execução.**
   - Uma errata no `evaluation/registro.yml` grava o hash do executor (`scripts/executar_experimento.py`), do `experimento/` (a contagem de 0 a 5 e a estatística) e do `correcao/`.
   - O executor se recusa a rodar sem ela, como o da seleção.
   - Assim o pré-registro cobre também o código que calcula, e não só o texto que o descreve.
   - A decisão 9 amplia a lista. Ela inteira fica em `CONGELADOS_ANTES_DO_EXPERIMENTO`, no executor.
5. **A pergunta fica por fora na ordem.**
   - Roda um modelo de cada vez, porque trocar de modelo custa recarga.
   - Dentro do modelo, pergunta por pergunta: a busca do RAG roda uma vez, e depois as quatro condições, cada uma com as 5 seeds.
   - A ordem das condições é sorteada por pergunta e modelo, ordenando pelo sha256 de `ordem|50|<modelo>|<pergunta>|<condição>`. A seed 50 está no código congelado.
   - As condições se intercalam no tempo, e uma deriva da máquina (calor, Ollama reiniciado, driver) não se alinha com nenhuma delas.
6. **Relatório em PDF** (`docs/experimento.pdf`), gerado do notebook pelo Quarto com o Typst embutido, com os gráficos em Python, os achados e a memória de cálculo, sem o código.
7. **Página curta** (`docs/experimento.md`), gerada por `scripts/resumir_experimento.py`, com cada hipótese e os limites. Ela tem diff no git e se refaz do publicado. O PDF não dá para conferir byte a byte.
8. **Uma PR em etapas**, como na #48: o código e o congelamento, depois a execução e a correção na minha máquina, depois o resultado.
9. **O congelamento cobre todo o caminho do dado até o número.** Além do executor, do `experimento/` e do `correcao/`, a errata congela:
   - o código do assistente que monta o prompt, roda a guarda do SQL e chama o Ollama (`assistente/` sem a interface e o `__main__`);
   - a busca do RAG (`rag/indice.py`);
   - as conferências antes de rodar (`scripts/selecionar_modelos.py`) e o hash que o congelamento confere (`scripts/validar_registro.py`).
   - O prompt e os parâmetros já estavam congelados pela #48, mas o código Python que os usa não. Mudar qualquer um desses arquivos depois da errata pede errata nova.
10. **A fumaça com os dois modelos escolhidos roda antes da errata.**
    - Ela usa só as perguntas inventadas do `scripts/analises/fumaca_assistente.py`, que ganhou a opção `--modelo`.
    - Com ela, meço o tempo de B e D para estimar a duração da execução.
    - Também confiro o corte de citações da correção às cegas em respostas reais de B, C e D, que o corretor ainda não tinha visto. Se o corte precisar de ajuste, ele entra antes do congelamento.
11. **A fonte do contexto é neutralizada na visão cega.**
    - A fumaça de 2026-10-14 (perguntas inventadas, os dois modelos escolhidos) não trouxe nenhuma citação no formato que o corte procurava (id da ontologia, trecho, página). Mas duas respostas diziam de onde veio a informação: "a ontologia indica que..." (Qwen, D) e "O documento de metodologia menciona..." (Qwen, C).
    - Essas referências viram "o contexto", com a contração do artigo ("na ontologia" vira "no contexto"). O mesmo vale para "os trechos" e "a documentação".
    - O conteúdo da frase fica. Cortar a frase inteira poderia tirar justamente a explicação da abstenção ou da ressalva e puxar contra B, C e D.
    - Limite declarado: o conteúdo ainda pode dar pista da condição, como "série 4189 do SGS" ou "definida pelo Copom", que o modelo tirou do contexto.

### Como a estatística registrada vira código

Conferi cada fórmula na fonte primária antes de escrever. O que o registro deixa implícito ficou assim:

- **Tabela pareada.** A notação é a de Newcombe (1998, Tabela I): `e` as duas condições acertam, `f` só a primeira, `g` só a segunda, `h` nenhuma. A diferença é `(f − g)/n`.
- **Intervalo de Newcombe, método 10** (Newcombe, R. G. *Improved confidence intervals for the difference between binomial proportions based on paired data*. Statistics in Medicine 17, 2635-2650, 1998, p. 2638-2639).
  - Os intervalos de score de Wilson das duas marginais se combinam pelo φ.
  - O numerador do φ, `eh − fg`, é trocado por `max(eh − fg − n/2, 0)` quando `eh > fg`.
  - Quando o denominador do φ é zero, φ = 0, como o artigo recomenda para marginal nula.
  - O código reproduz os 18 casos do método 10 da Tabela III do artigo, e o `validar_experimento` confere isso no CI.
- **McNemar exato unilateral.** `p = P(Bin(f + g, 1/2) ≥ f)`, calculado em frações. Sem par discordante, p = 1.
- **p da não inferioridade (H4).** É o menor α a partir do qual o limite inferior unilateral de 1 − α fica acima da margem de −0,05 em todo α maior.
  - Com φ alto, o limite inferior pode não ser monótono em z. Por isso a busca sobe z a partir de 0, com passo de 0,01, até o primeiro z em que o limite chega à margem, e afina por bisseção até 1e-12. Assim, p abaixo do alfa sempre implica não inferioridade no intervalo de 90%. O contrário pode falhar só para o lado conservador.
  - Com a diferença na margem ou abaixo dela, nenhum α até 0,5 serve, e o p é 1.
  - O p da H4 é o maior dos dois, como registrado. A H4 se sustenta quando esse p, ajustado pelo Holm, fica no alfa, e o resultado mostra também se cada comparação é não inferior sem ajuste.
- **Interação da H5.**
  - A comparação com a estatística observada é feita em inteiros (multiplicada pelos dois tamanhos de grupo), sem erro de ponto flutuante. Empate conta a favor, como o registro diz ("maior ou igual").
  - O bootstrap usa o percentil com a interpolação linear do NumPy.
  - A permutação e o bootstrap têm cada um o próprio `numpy.random.default_rng(47)` (PCG64), então o resultado não depende da ordem em que rodam.
- **Holm.** Em ordem crescente de p, com empate pelo nome da hipótese, máximo acumulado e teto de 1. O Holm, o maior p da H4 e a decisão usam os p exatos, e o arredondamento a 6 casas só vale no que se grava.
- **Ambiente.** O resultado grava a versão do numpy, porque o fluxo do gerador da H5 pode mudar entre versões. O workflow fixa o Python 3.14, e com ele o numpy do `uv.lock`.
- **Q de Cochran.** O p vem da qui-quadrado com 3 graus de liberdade. Sem variação dentro das perguntas, o Q não se define e sai nulo.
- **Decisão.** "Sustentada" quando o p (ajustado, na família) fica no alfa de 0,05. "Não sustentada" quer dizer que o dado não mostrou o efeito, e o intervalo diz o tamanho que ele pode ter.

O `scripts/analises/qa_experimento.py` confere tudo isso por outro caminho: o McNemar contra o `scipy` e o `statsmodels`, o Cochran e o Holm contra o `statsmodels`, o Newcombe contra uma segunda forma do Wilson, o p da H4 contra uma grade fina de α e a permutação contra a enumeração exata de um caso pequeno.

## Alternativas descartadas

- **Julgar só o que muda a maioria, como na seleção.** A carga seria menor, mas a contagem de 0 a 5 sairia como faixa, e isso seria um desvio do registro.
- **Contar o erro de servidor como erro.** Uma queda do Ollama no meio da noite derrubaria um bloco de execuções seguidas e pesaria contra as condições que rodavam naquela hora.
- **A condição por fora.** O cache de prefixo do Ollama seria mais bem aproveitado, mas uma deriva da máquina ficaria confundida com a condição.
- **Ordem fixa A, B, C, D dentro da pergunta.** A posição na sequência ficaria sempre ligada à mesma condição.
- **marimo ou nenhum notebook.** O marimo não mostra os gráficos no GitHub sem rodar, e sem notebook a issue não ficaria atendida.
- **PDF pelo `nbconvert --to webpdf`.** O PDF parece um notebook impresso, sem legenda numerada e com quebra de página ruim.
- **Não congelar o código.** O histórico do git seria a única garantia de que a análise não mudou depois de ver os dados.

## Consequências

- O executor (`scripts/executar_experimento.py`) só roda com a errata de congelamento. Corrigir o código depois dela pede uma errata nova, datada, com o motivo. Isso vale também para o assistente: uma mudança nele pela #51 depois da errata pede errata.
- O `correcao/` serve aos dois usos. A seleção publicada não muda, e o workflow `experimento.yml` confere isso a cada push.
- A carga da correção às cegas cresce com o número de visões cegas distintas, e não com as 1.640 execuções. Ela só se conhece depois de rodar.
- O resultado sai em `evaluation/experimento/resultado.json`, com os registros em `evaluation/experimento/execucoes.jsonl.gz`, a página `docs/experimento.md`, o notebook e o PDF. Ele entra no registro por errata depois de gerado.
- Os limites continuam os do registro: 41 perguntas, 12 no grupo de ressalva e abstenção, a seleção pela condição A puxando contra a H1 e a H2 (ADR 0026), o piso medido na seleção (ADR 0030) e a condição A podendo ler as colunas de definição das `dim_*` (ADR 0029).
