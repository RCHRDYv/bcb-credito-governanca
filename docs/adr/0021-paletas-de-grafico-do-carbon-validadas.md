# ADR 0021: As paletas de gráfico saem do Carbon, com a categórica ajustada e validação automatizada

**Status:** Aceito
**Data:** 2026-09-27

## Contexto

O [ADR 0020](0020-design-system-carbon-com-camada-liquid-glass.md) fixou as paletas de gráfico do Carbon como fundação, e deixou duas pendências para a #63:
- a paleta categórica oficial do Carbon falha na validação;
- a sequencial e a divergente ainda não tinham sido escolhidas.

A falha da categórica foi medida de novo em 2026-09-27, contra o vidro regular de cada tema (#fbfbfb no claro e #222222 no escuro):
- **No claro,** o vermelho 90 fica com luminosidade 0,28, abaixo da faixa de 0,43 a 0,77, e o verde-azulado 70 tem croma 0,074 e parece cinza. O pior par vizinho com daltonismo fica em 6,3, na deuteranopia.
- **No escuro,** a versão oficial reprova em mais critérios: três cores saem da faixa, duas ficam sem croma e, sem daltonismo, vermelho 50 e magenta 40 ficam a 13,3 de distância, abaixo do mínimo de 15.

As candidatas saíram todas das rampas oficiais, do pacote `@carbon/colors` 11.59.0, e das paletas do `@carbon/charts` 1.27.20, conferidas no código publicado em 2026-09-27. Cada uma foi mostrada numa página de revisão, nos dois temas e com dado real do projeto, junto com a simulação dos três tipos de daltonismo e os números do validador. A escolha foi feita na revisão visual de 2026-09-27.

## Decisões

### 1. A categórica é a oficial do Carbon com a menor troca que passa nos dois temas

A abertura da oficial fica igual: roxo, ciano, magenta e vermelho nas mesmas posições. Saem só as cores que reprovam: o verde-azulado vira laranja 50, o vermelho 90 sai, e o azul 50 entra na quinta posição, com o vermelho 50 na sexta.

| Posição | Claro | Escuro | Em relação à oficial |
|---|---|---|---|
| 1 | roxo 70, #6929c4 | roxo 60, #8a3ffc | Igual à oficial nos dois temas |
| 2 | ciano 50, #1192e8 | ciano 50, #1192e8 | Igual no claro. No escuro, o ciano 40 oficial sai da faixa |
| 3 | laranja 50, #eb6200 | laranja 50, #eb6200 | Troca o verde-azulado, que fica sem croma |
| 4 | magenta 70, #9f1853 | magenta 50, #ee5396 | Igual no claro. No escuro, o magenta 40 oficial sai da faixa |
| 5 | azul 50, #4589ff | azul 50, #4589ff | Nova posição |
| 6 | vermelho 50, #fa4d56 | vermelho 50, #fa4d56 | O vermelho 50 oficial, que era a quinta. O vermelho 90 e o vermelho 10 saem |

- **Até seis séries com cor.** A partir da sétima, as menores somam "Outros", em cinza: cinza 50 no claro e cinza 60 no escuro, no token `color.chart.other`.
- **Em dispersão, mapa e pequenos múltiplos, até quatro séries com cor.** Nessas formas, qualquer par de cores pode se encostar, e não só as vizinhas. O ciano 50 e o azul 50 ficam a 5,1 de distância mesmo sem daltonismo, então a quinta série em diante vira "Outros".

**Medidas, contra o vidro regular:**

| | Claro | Escuro |
|---|---|---|
| Menor contraste com o fundo | 3,22:1 | 3,18:1 |
| Pior par vizinho, sem daltonismo | 23,8 | 15,8 |
| Pior par vizinho, protanopia | 20,6 | 13,2 |
| Pior par vizinho, deuteranopia | 15,9 | 8,4 |
| Pior par vizinho, tritanopia | 19,0 | 3,1 |

### 2. A sequencial é a rampa roxa do Carbon, sem o branco

É a paleta monocromática roxa do Carbon, em cinco degraus. O branco da rampa oficial fica de fora, porque some sobre o vidro.
- **Claro:** roxo 40, 50, 60, 70 e 80, do valor baixo ao alto.
- **Escuro:** roxo 70, 60, 50, 40 e 30. A ordem se inverte porque, no escuro, o valor baixo é o que se aproxima do fundo.

**Medidas:**
- **Menor passo entre degraus vizinhos:** 10,2 sem daltonismo, 7,3 na protanopia e 8,6 na deuteranopia, nos dois temas. Na tritanopia, 9,1 no claro e 9,0 no escuro.
- **Ponta junto ao fundo:** 2,27:1 no claro e 2,06:1 no escuro, acima do piso de 2:1.

### 3. A divergente é a roxo e verde-azulado do Carbon, com o meio cinza

É a segunda paleta divergente do Carbon, com três degraus de cada lado. O roxo fica acima da referência, e o verde-azulado abaixo. No desvio contra o país, roxo quer dizer que a inadimplência da UF subiu mais que a do país. O meio é cinza, e não o branco do Carbon, que some no vidro, como o [guia](../dashboard/design-system.md) já pedia.
- **Claro:** verde-azulado 40, 60 e 80 abaixo; cinza 20 no meio; roxo 40, 60 e 80 acima.
- **Escuro:** verde-azulado 70, 50 e 40 abaixo; cinza 80 no meio; roxo 70, 50 e 40 acima.

**Medidas.** Menor distância entre os dois lados no mesmo degrau:

| | Claro | Escuro |
|---|---|---|
| Sem daltonismo | 18,3 | 22,5 |
| Protanopia | 12,9 | 12,9 |
| Deuteranopia | 9,6 | 9,6 |
| Tritanopia | 7,0 | 9,2 |

### 4. A validação é automatizada, com controle negativo

A validação mora no próprio projeto, em `dashboard/src/cor/`:
- `oklab.js` converte a cor para OKLab e OKLCH;
- `daltonismo.js` simula protanopia, deuteranopia e tritanopia pelas matrizes de Machado, Oliveira e Fernandes (2009), com severidade 1,0;
- `validacao.js` aplica os critérios de cada papel.

| Papel | Critérios |
|---|---|
| Categórica | Contraste de 3:1 com o fundo (WCAG 2.2). Luminosidade OKLCH de 0,43 a 0,77 no claro e de 0,48 a 0,67 no escuro. Croma de pelo menos 0,10. Pior par com daltonismo com alvo 8 e piso 6: entre 6 e 8, só com rótulo direto. Pior par sem daltonismo de pelo menos 15 |
| Sequencial | Luminosidade em ordem, passo de pelo menos 0,06 entre degraus, uma matiz só e a ponta junto ao fundo com pelo menos 2:1 |
| Divergente | Cada braço vale como sequencial, os braços são simétricos, o meio é cinza, e os polos continuam distintos com e sem daltonismo |

A distância é medida em OKLab, multiplicada por 100. A tritanopia aparece nos números, mas não reprova: é rara, e o modelo de simulação é menos preciso para ela. Os limites e o modelo seguem o método de visualização de dados usado no projeto, e os números do validador do projeto batem com os do validador de referência desse método.

O teste `dashboard/tests/unit/paletas.test.js` lê as paletas dos tokens gerados e confere as duas superfícies em que um gráfico pode estar: o vidro regular e a camada sólida que o substitui. Dois controles negativos garantem que o teste reprova de verdade: a categórica oficial do Carbon e uma paleta clara demais para o fundo precisam reprovar. O texto do tema dos gráficos é conferido em `tema.test.js`, com 4,5:1.

### 5. Exceção aceita: a ponta das rampas no escuro sem desfoque

Quando o navegador não tem `backdrop-filter`, o vidro vira a camada sólida, #262626 no escuro. Nesse caso, a ponta da sequencial e dos braços da divergente, roxo 70 e verde-azulado 70, fica em 1,96:1, logo abaixo do piso de 2:1. Sobre o vidro, que é o caso normal, fica em 2,06:1.

A exceção foi aceita em 2026-09-27, e a outra saída era trocar o primeiro degrau do escuro, o que mudaria a rampa aprovada na revisão visual. O teste confere as rampas sobre o vidro, e o contraste de 3:1 da categórica nas duas superfícies.

## Alternativas descartadas

**A categórica oficial, sem ajuste.** Reprova nos dois temas, como descrito no contexto.

**Uma categórica reordenada, sem repetir cores reservadas:** verde 60, roxo 60, magenta 50, amarelo 60, ciano 50 e laranja 50, iguais nos dois temas. Passava com mais folga, com pior par vizinho de 16,3 com daltonismo, e não repetia nenhuma cor de quadrante, de estado ou de ação. Em compensação, mudava a ordem e quatro das seis matizes da oficial. A escolhida mantém a abertura da paleta do Carbon.

**Sequencial em azul, ciano ou verde-azulado.** As três rampas oficiais passavam no validador. O azul já é a cor de ação e seleção, e o verde-azulado é a cor do quadrante Entrar. O ciano não tinha outro significado na interface.

**Divergente em vermelho e ciano,** a primeira do Carbon. Passava no validador nos dois temas.

## Consequências

**Positivas.**
- As três paletas passam no validador, nos dois temas, com os números registrados aqui e no guia.
- Uma paleta nova ou alterada que fique abaixo do contraste, fora da faixa ou próxima demais com daltonismo reprova no CI.
- As cores continuam sendo degraus oficiais do Carbon, e o único primitivo novo é a família laranja, também oficial.

**Negativas, e são reais.**
- **Cores que já têm outro significado.**
  - O roxo 70, primeira cor categórica e degrau da sequencial, é a marca do quadrante Manter.
  - A divergente usa as matizes de Manter e de Entrar.
  - No escuro, o azul 50 da categórica é a cor de ação e de informação, e o vermelho 50 é a de erro.

  Continua valendo a regra do guia: as cores dos quadrantes não aparecem com outro significado na mesma tela. Numa visão com a matriz ou com etiquetas de quadrante, essas paletas não entram com outro significado.
- **Até quatro séries em dispersão, mapa e pequenos múltiplos,** por causa do ciano 50 e do azul 50.
- **Tritanopia no escuro.** O pior par vizinho da categórica fica em 3,1, entre o roxo 60 e o ciano 50. Para quem tem tritanopia, a identificação dessas duas séries depende da legenda e do rótulo.
- **A exceção da decisão 5,** no escuro sem desfoque.
