# ADR 0022: As visões cabem numa tela no computador, sem rolagem da página

**Status:** Aceito.
**Data:** 2026-10-05

## Contexto

O dashboard vai ficar aberto num monitor secundário, ao lado do trabalho principal, e quem usa não deve precisar rolar a página para ver tudo (#87). Os modelos de página do [guia](../dashboard/design-system.md) não tratavam a altura: cada bloco tinha a altura do próprio conteúdo, e a página rolava. Na revisão da Tela 1, em 2026-10-05, numa janela de 1920×950:
- a página tinha 2.132 px de altura, ou 2,2 telas;
- o conteúdo parava em 1.536 px de largura, o limite do grid do Carbon, e 384 px ficavam vazios.

A tela-alvo é um notebook Full HD, com qualquer escala do Windows, com a janela maximizada ou não, ou em tela cheia. A escala divide a tela em pixels de CSS, e o navegador e a barra de tarefas tiram a parte deles da altura:

| Escala do Windows | Tela, em pixels de CSS | Janela maximizada, aproximada |
|---|---|---|
| 100% | 1920×1080 | 1920×950 |
| 125% | 1536×864 | 1536×730 |
| 150% | 1280×720 | 1280×590 |

## Decisões

### 1. O piso é uma janela de 1280×720 px

A partir dessa janela, em largura e em altura, a visão cabe sem rolagem da página. O piso cobre as escalas de 100% e de 125%, maximizadas ou em tela cheia. Ficam abaixo dele a escala de 150% maximizada e a de 125% com a barra de favoritos aberta.

### 2. O que passa da altura de um cartão rola dentro dele

A página tem a altura da janela, e os cartões dividem o que sobra:
- **Listas longas** rolam dentro do próprio cartão: o ranking das 27 UFs, a tabela e o painel de detalhe.
- **Os gráficos** preenchem o cartão e se redesenham quando a janela muda de tamanho.

### 3. Abaixo do piso, a página rola, sem nada cortado

Abaixo de 1280×720, vale o fluxo de antes, e a página rola:
- **No computador,** os blocos ficam lado a lado pelo grid, cada um com a própria altura.
- **No celular,** nada muda: tudo empilha, e o detalhe abre na folha que sobe de baixo.

Nenhum bloco é cortado nem fica por cima de outro.

### 4. A visão usa a largura toda

O limite de 1.584 px do grid do Carbon deixa de valer para as visões. Quando a altura é o recurso escasso, é a largura que dá espaço aos gráficos.

### 5. Formas alternativas trocam no mesmo lugar, e não empilham na página

Quando uma pergunta pode ser vista de mais de um jeito, as formas trocam no mesmo cartão, por um controle segmentado na barra de filtros.
- **Na Tela 1,** o território tem quatro formas: "Mapa | Grade | Matriz | Tabela".
- **A tabela** com os mesmos números (RF-G06) é uma das formas, e o download em CSV aparece só nela.
- **Formas que pedem largura,** como a matriz de UF por modalidade e a tabela, ocupam também a coluna da direita enquanto estão escolhidas. Com um elemento escolhido, a coluna volta, só com o painel de detalhe.

### 6. A ressalva continua visível, numa linha

A ressalva fica junto do número que ela qualifica, numa linha curta, e não escondida atrás de um ícone. É o que pede o [ADR 0005](0005-projeto-termina-em-recomendacao.md): a fronteira do dado é parte da entrega.

### 7. O visual espacial fica num palco, com os painéis dos lados

Decidido na revisão visual da Tela 1, em 2026-10-05, para o mapa ter mais destaque que os outros gráficos e caixas:
- **O palco** é um cartão sólido grande, no centro, na altura toda, com o dobro da largura de cada coluna lateral. As cores dos gráficos continuam validadas contra a superfície sólida ([ADR 0021](0021-paletas-de-grafico-do-carbon-validadas.md)), e o campo de luz aparece em volta do palco e atrás dos painéis.
- **À esquerda,** os filtros em cima e, embaixo, o que o visual mostra: título, fonte, resumo do recorte e ressalvas.
- **À direita,** os números em reais em cima e, embaixo, o ranking ou o painel de detalhe, um de cada vez.
- **A legenda** é uma escala compacta no canto inferior direito do palco, onde o desenho do Brasil não chega, e o mapa fica com a altura toda.

Medido em 2026-10-05: o desenho do mapa passou de 333 para 605 px de altura numa janela de 1536×730, e de 589 para 825 px numa de 1920×950.

## Alternativas descartadas

**Um layout fixo em 1920×1080.** Só funcionaria a 100% de escala e em tela cheia. Em qualquer outra escala, cortaria o conteúdo ou rolaria.

**Encolher a página toda com `transform: scale` para caber.** Caberia em qualquer janela, mas o texto encolheria junto e poderia ficar abaixo do tamanho legível. A área de toque também deixaria de corresponder ao que se vê.

**Abas que trocam a visão inteira, como slides.** Cada aba caberia na tela, mas separaria o que se compara: o mapa, o ranking e o detalhe da UF precisam estar à vista juntos.

**Mapa no centro entre cartões, ou filtros e números na barra do topo,** as opções A e B do mockup da revisão de 2026-10-05. A primeira dava cerca de 440 px de altura ao mapa a 1536×730; a segunda, cerca de 520, ao custo de tirar o número de destaque do tamanho que o guia pede e de mudar a barra de topo, comum a todas as visões.

**O palco sem moldura, com a superfície sólida no fundo da visão inteira.** Dava 34 px a mais ao mapa, mas cobria o campo de luz na tela toda. **Uma faixa sólida só no centro, de cima a baixo,** mantinha a altura e devolvia o campo de luz dos lados, mas fugia da linguagem de cartões do resto do site.

**O piso de 1056×560 px.** Cobriria também a escala de 150% maximizada, mas, nessa janela, os gráficos ficariam com menos de 250 px de altura.

## Consequências

**Positivas.**
- Quem deixa o dashboard aberto num monitor secundário vê a visão inteira sem rolar.
- A largura que sobrava nas telas grandes passa a ser usada.
- Um teste de ponta a ponta mede a altura da página, e uma mudança que a faça rolar acima do piso reprova no CI.

**Negativas, e são reais.**
- A 150% de escala maximizada, e a 125% com a barra de favoritos aberta, a página rola.
- No piso, os gráficos têm menos altura do que tinham no fluxo com rolagem.
- Cada visão passa a ter um orçamento de altura, que limita quantos gráficos ela mostra ao mesmo tempo. As Telas 2, 3 e 4 (#70, #71 e #72) são planejadas com essa restrição.
- A matriz e a tabela tiram a oportunidade e o ranking de vista enquanto estão escolhidas.
- No piso, a coluna da direita fica estreita, e o ranking mostra poucas barras antes de rolar.
