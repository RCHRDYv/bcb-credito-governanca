# Design system do dashboard

O guia visual do dashboard de crédito PJ: as cores, os tipos, os espaços, os materiais, o movimento, os componentes, os padrões de uso e os modelos de página que toda visão segue.

- **Situação:** oficial desde 2026-09-26 ([ADR 0020](../adr/0020-design-system-carbon-com-camada-liquid-glass.md)).
- **Protótipo navegável:** [`dashboard/prototipo-design-system/`](../../dashboard/prototipo-design-system/index.html). Abra no navegador e escolha "Carbon + Liquid Glass" no topo. Os outros quatro candidatos ficam lá como registro da comparação.
- **Como é construído:** tokens no formato W3C DTCG, gerados para CSS pelo Style Dictionary ([ADR 0018](../adr/0018-design-system-por-tokens-dtcg.md)). Os tokens moram em `dashboard/tokens/`, e o [catálogo](../../dashboard/catalogo.html) mostra as fundações nos dois temas, lidas dos próprios tokens.

## De onde vem cada regra

O design system junta duas fontes, e cada seção deste guia diz de qual delas vem:

| Origem | Cobre | Referência |
|---|---|---|
| **Carbon, oficial** | Cor, paletas de gráfico, tipografia, espaçamento e grid | Documentação e pacotes do Carbon, conferidos em 2026-09-26 |
| **Camada Liquid Glass, nossa** | Materiais de vidro, raio, elevação, movimento, componentes, padrões de uso e modelos de página | Este guia, a partir das diretrizes de materiais da Apple |
| **Componentes de gráfico, nossos** | Tema dos gráficos, mapa, cartograma, matriz, série temporal, ranking e número de destaque, sobre o ECharts | Este guia e o catálogo |

Itens marcados **em aberto** ainda não foram decididos e não são regra.

## Princípios

1. **Cor só onde há significado.** Neutros na maior parte da tela, o azul do Carbon para ação e seleção, e as cores dos quadrantes só onde há decisão.
2. **Todo número mostra de onde veio.** Data-base e fonte sempre visíveis e, no chat, o SQL que gerou o número.
3. **O vidro flutua, e o dado fica firme.** Vidro nos controles e nas superfícies que flutuam; tabela, gráfico e texto com contraste medido.
4. **Nenhum significado só por cor.** Quadrante, estado e alerta levam ícone e rótulo junto da cor.
5. **Movimento comunica mudança de estado,** e some quando o sistema pede movimento reduzido.

## Fundações

### Cor · Carbon

Tema **g10** do Carbon. O contraste foi medido contra o fundo (#f4f4f4) e contra o vidro regular sobre o fundo (#fdfdfd, com o vidro a 82% desde a #64).

**Neutros e ação**

| Uso | Token do Carbon | Valor | Contraste no fundo | No vidro |
|---|---|---|---|---|
| Fundo da página | `background` | #f4f4f4 | | |
| Camada sólida | `layer-01` | #ffffff | | |
| Borda sutil | `border-subtle-01` | #e0e0e0 | | |
| Borda sutil em camada | `border-subtle-00` | #c6c6c6 | | |
| Borda forte | `border-strong-01` | #8d8d8d | 3,02:1 | 3,26:1 |
| Texto principal | `text-primary` | #161616 | 16,45:1 | 17,79:1 |
| Texto secundário | `text-secondary` | #525252 | 7,10:1 | 7,68:1 |
| Texto de ajuda | `text-helper` | #6f6f6f | 4,57:1 | 4,94:1 |
| Texto de exemplo nos campos | o mesmo cinza do texto de ajuda, decidido na #64 | #6f6f6f (cinza 60) | 4,57:1 | 4,94:1 |
| Ação e foco | `interactive`, `focus` | #0f62fe (azul 60) | 4,55:1 | 4,92:1 |
| Ação ao passar o mouse | `button-primary-hover` | #0050e6 | | |
| Ação pressionada | `button-primary-active` | #002d9c | | |
| Fundo de seleção | azul 10 | #edf5ff | | |

**Estado**

| Estado | Token do Carbon | Valor | Contraste no fundo | Como usar |
|---|---|---|---|---|
| Informação | `support-info` | #0043ce | 7,09:1 | Ícone e texto |
| Sucesso | `support-success` | #24a148 | 3,05:1 | Só ícone e marca, nunca texto |
| Erro | `support-error` | #da1e28 | 4,55:1 | Ícone, borda e texto |
| Atenção | `support-warning` | #f1c21b | 1,53:1 | Só preenchimento de ícone, com o glifo em #161616 (10,75:1), como faz o Carbon |

**Quadrantes da recomendação**

A cor do quadrante marca pontos, faixas e o ponto da etiqueta. O texto usa o tom escuro da mesma cor, também da paleta do Carbon.

| Quadrante | Marca | Contraste no fundo | Texto | Contraste do texto |
|---|---|---|---|---|
| Entrar | verde-azulado 50, #009d9a | 3,04:1 | verde-azulado 70, #005d5d | 7,01:1 |
| Observar | amarelo 50, #b28600 | 3,03:1 | amarelo 80, #483700 | 10,48:1 |
| Não entrar | vermelho 60, #da1e28 | 4,55:1 | vermelho 70, #a2191f | 7,08:1 |
| Manter | roxo 70, #6929c4 | 7,03:1 | roxo 70, #6929c4 | 7,03:1 |

Validação de daltonismo em 2026-09-26: a paleta passa em todos os critérios. Há um único alerta: para deuteranopia, vermelho e amarelo ficam próximos (distância de 7,0). Isso é aceitável porque o quadrante nunca aparece só pela cor: ícone, rótulo e posição na matriz o identificam.

O **alerta antecipado** usa o par do Carbon para atenção: fundo amarelo 10 (#fcf4d6) e texto amarelo 80 (#483700), com 10,46:1.

### Tema escuro · Carbon g100

O escuro é o tema **g100** do Carbon, conferido no `@carbon/themes` 11.82.0 em 2026-09-27. Não é uma segunda paleta mantida à parte: cada cor semântica guarda o valor claro e o escuro, e o CSS escreve os dois com `light-dark()` ([ADR 0018](../adr/0018-design-system-por-tokens-dtcg.md)).

**Como o tema é escolhido,** decidido em 2026-09-27:
- o site segue o sistema do visitante: abre escuro para quem usa o modo escuro, e claro para os outros;
- quando o sistema não indica preferência, o site abre claro;
- a impressão e o PDF saem sempre claros;
- desde a #64, o visitante pode escolher no topo entre claro, escuro e automático, que é o padrão e segue o sistema. A escolha fica guardada no navegador, e um script pequeno no `<head>` a aplica antes da pintura, para a página não piscar no tema errado.

**Neutros e ação.** O contraste é medido contra o fundo (#161616) e contra o vidro regular sobre o fundo (#242424, com o vidro a 88% desde a #64).

| Uso | Token do Carbon | Valor | Contraste no fundo | No vidro |
|---|---|---|---|---|
| Fundo da página | `background` | #161616 (cinza 100) | | |
| Camada sólida | `layer-01` | #262626 (cinza 90) | | |
| Borda sutil | `border-subtle-01` | #525252 | | |
| Borda sutil em camada | `border-subtle-00` | #393939 | | |
| Borda forte | `border-strong-01` | #6f6f6f | 3,60:1 | 3,09:1 |
| Texto principal | `text-primary` | #f4f4f4 | 16,45:1 | 14,11:1 |
| Texto secundário | `text-secondary` | #c6c6c6 | 10,59:1 | 9,09:1 |
| Texto de ajuda | `text-helper` | #a8a8a8 | 7,61:1 | 6,53:1 |
| Texto de exemplo nos campos | o mesmo cinza do texto de ajuda, decidido na #64 | #a8a8a8 (cinza 40) | 7,61:1 | 6,53:1 |
| Ação | `interactive` | #4589ff (azul 50) | 5,41:1 | 4,64:1 |
| Link | `link-primary` | #78a9ff (azul 40) | 7,68:1 | 6,59:1 |
| Foco | `focus` | #ffffff | 18,10:1 | 15,52:1 |
| Botão primário | `button-primary` | #0f62fe, igual ao claro, com o texto branco a 5,00:1 | | |
| Fundo de seleção | azul 90 | #001d6c | | |

**Estado**

| Estado | Token do Carbon | Valor | Contraste no fundo | Como usar |
|---|---|---|---|---|
| Informação | `support-info` | #4589ff | 5,41:1 | Ícone e texto |
| Sucesso | `support-success` | #42be65 | 7,57:1 | Só ícone e marca, como no claro |
| Erro | `support-error` | #fa4d56 | 5,40:1 | Ícone, borda e texto |
| Atenção | `support-warning` | #f1c21b | 10,75:1 | Só preenchimento de ícone, com o glifo em #161616, como no claro |

**Quadrantes da recomendação.** O Carbon não tem estes tokens, e o escuro foi proposto na #62. As marcas ficam nos mesmos degraus do claro, menos o roxo, que sobe para o 50 para ter contraste. Os textos usam degraus claros da mesma família.

| Quadrante | Marca | Contraste no fundo | Texto | Contraste do texto |
|---|---|---|---|---|
| Entrar | verde-azulado 50, #009d9a | 5,42:1 | verde-azulado 30, #3ddbd9 | 10,63:1 |
| Observar | amarelo 50, #b28600 | 5,43:1 | amarelo 20, #fddc69 | 13,46:1 |
| Não entrar | vermelho 60, #da1e28 | 3,62:1 | vermelho 30, #ffb3b8 | 10,68:1 |
| Manter | roxo 50, #a56eff | 5,41:1 | roxo 30, #d4bbff | 10,64:1 |

Validação de daltonismo em 2026-09-27, com todos os pares: as marcas do escuro passam em todos os critérios, com o mesmo alerta do claro, vermelho e amarelo a 7,0 para deuteranopia, aceito pelo mesmo motivo. Uma primeira proposta, com o verde-azulado 40 e o amarelo 40, reprovou por ficar clara demais para a faixa de luminosidade do tema escuro.

O **alerta antecipado** usa fundo amarelo 90 (#302400) e texto amarelo 20 (#fddc69), com 11,33:1.

### Paletas de gráfico · Carbon

As duas paletas saem das rampas oficiais do Carbon e foram escolhidas na revisão visual de 2026-09-27 ([ADR 0021](../adr/0021-paletas-de-grafico-do-carbon-validadas.md)). Uma terceira, a divergente roxo e verde-azulado, saiu na revisão da Tela 1, em 2026-10-05: toda intensidade usa a sequencial roxa. Os tokens são `color.chart.categorical.1` a `6`, `color.chart.sequential.1` a `5` e `color.chart.other`, e o [catálogo](../../dashboard/catalogo.html) mostra cada paleta nos dois temas, com a simulação de daltonismo.

**Categórica,** para identidade, como modalidades. É a oficial do Carbon com a menor troca que passa nos dois temas: o verde-azulado, sem croma, vira laranja 50, o vermelho 90, quase preto, sai, e o azul 50 entra.

| Posição | Claro | Escuro |
|---|---|---|
| 1 | roxo 70, #6929c4 | roxo 60, #8a3ffc |
| 2 | ciano 50, #1192e8 | ciano 50, #1192e8 |
| 3 | laranja 50, #eb6200 | laranja 50, #eb6200 |
| 4 | magenta 70, #9f1853 | magenta 50, #ee5396 |
| 5 | azul 50, #4589ff | azul 50, #4589ff |
| 6 | vermelho 50, #fa4d56 | vermelho 50, #fa4d56 |
| Outros | cinza 50, #8d8d8d | cinza 60, #6f6f6f |

- **Ordem fixa, e a cor segue a série.** Um filtro que tira séries não repinta as que ficam. Uma cor nova nunca é gerada.
- **Até seis séries com cor** em barras e linhas. A partir da sétima, as menores somam "Outros", em cinza.
- **Até quatro séries com cor em dispersão, mapa e pequenos múltiplos,** em que qualquer par de cores pode se encostar. O ciano 50 e o azul 50 ficam próximos demais quando se encostam.
- **Uma série só usa a primeira cor,** como o ranking e a série temporal. Pintar cada barra de uma cor gastaria a cor para repetir o que o comprimento já mostra.

**Sequencial,** para intensidade, como carteira por empresa. É a rampa roxa do Carbon, em cinco degraus, sem o branco, que some no vidro, e a única rampa do design system.

| Degrau | 1, valor baixo | 2 | 3 | 4 | 5, valor alto |
|---|---|---|---|---|---|
| Claro | roxo 40, #be95ff | roxo 50, #a56eff | roxo 60, #8a3ffc | roxo 70, #6929c4 | roxo 80, #491d8b |
| Escuro | roxo 70, #6929c4 | roxo 60, #8a3ffc | roxo 50, #a56eff | roxo 40, #be95ff | roxo 30, #d4bbff |

No escuro a ordem se inverte, porque o valor baixo é o que se aproxima do fundo.

**Distância até uma referência, na mesma rampa.** Quando o número é a distância até uma referência, como a mediana das UFs ou a taxa do país, ele é dividido em cinco faixas simétricas em torno dela, uma por degrau da rampa: o meio e duas de cada lado (`classesEmCincoFaixas`, decidido em 2026-10-05).
- **O roxo mais forte fica no lado que quer dizer mais** para a pergunta da visão. Na Tela 1, abaixo da mediana, onde há mais espaço; no desvio da inadimplência contra o país, acima, onde o risco sobe mais.
- **A legenda diz o sentido de cada faixa em palavras,** como "Mais espaço: mais de 30% abaixo da mediana". A cor diz quanto, e não para que lado.
- **Não usar duas matizes para uma intensidade.** Uma divergente de duas cores pede a legenda para saber qual lado é qual, e foi o que confundiu a leitura da Tela 1 (ADR 0021, decisão 3).

**Validação e simulação de daltonismo.** O contraste é medido contra o cartão sólido onde os gráficos são desenhados, o token `color.chart.surface` (#ffffff no claro e #161616 no escuro, desde a #64), e a distância entre cores em OKLab, multiplicada por 100, com a simulação de Machado, Oliveira e Fernandes (2009). Para a categórica, o alvo é 8 com daltonismo e 15 sem; para as rampas, o que importa é cada degrau continuar distinto do vizinho.

| Paleta | Tema | Contraste | Sem daltonismo | Protanopia | Deuteranopia | Tritanopia |
|---|---|---|---|---|---|---|
| Categórica, pior par vizinho | Claro | 3,33:1 | 23,8 | 20,6 | 15,9 | 19,0 |
| Categórica, pior par vizinho | Escuro | 3,62:1 | 15,8 | 13,2 | 8,4 | 3,1 |
| Sequencial, menor passo | Claro | 2,35:1 na ponta | 10,2 | 7,3 | 8,6 | 9,1 |
| Sequencial, menor passo | Escuro | 2,34:1 na ponta | 10,2 | 7,3 | 8,6 | 9,0 |

A tritanopia aparece nos números, mas não reprova, porque é rara e o modelo é menos preciso para ela. No escuro, o roxo 60 e o ciano 50 ficam a 3,1 para quem tem tritanopia, e a legenda e o rótulo identificam essas duas séries. A exceção de 1,96:1 da ponta das rampas no escuro, aceita no ADR 0021, deixou de existir na #64, com o cartão sólido.

**Cores que já têm outro significado.** O roxo 70 é também a marca de Manter, o quadrante de espaço baixo, e na Tela 1 o roxo mais forte quer dizer mais espaço. Por isso vale a regra da etiqueta de quadrante: numa tela com a matriz ou com etiquetas de quadrante, essas paletas não entram com outro significado.

### Tipografia · Carbon

IBM Plex Sans para a interface e IBM Plex Mono para SQL e código, as duas com licença aberta (OFL). Escala produtiva do Carbon:

| Token | Tamanho e altura de linha | Peso | Uso |
|---|---|---|---|
| `heading-07` | 54/64 | 300 | Número de destaque, raro |
| `heading-06` | 42/50 | 300 | Título de página grande |
| `heading-05` | 32/40 | 400 | Título de página |
| `heading-04` | 28/36 | 400 | Número em painel |
| `heading-03` | 20/28 | 400 | Título de seção |
| `heading-02` | 16/24 | 600 | Título de painel |
| `heading-compact-01` | 14/18 | 600 | Rótulo forte, cabeçalho de tabela |
| `body-01` | 14/20 | 400 | Texto corrido |
| `body-compact-01` | 14/18 | 400 | Texto de componente |
| `label-01` | 12/16 | 400 | Rótulo e texto de ajuda |
| `code-01` | 12/16, mono | 400 | SQL e código |

Números em tabelas, painéis e rótulos usam algarismos tabulares, para alinharem em coluna.

As fontes são servidas pelo próprio site, dos pacotes oficiais `@ibm/plex-sans` 1.1.0 e `@ibm/plex-mono` 2.5.0. Entram só os pesos da escala (300, 400 e 600 no Sans, 400 no Mono) e só o arquivo Latin1, que cobre o português: 83 KB no total. Nos tokens, a altura de linha é a razão oficial do Carbon; no `heading-07` e no `heading-06`, a razão 1,199 dá cerca de 65 e 50 px, que a tabela arredonda.

### Espaçamento · Carbon

| Token | spacing-01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Valor (px) | 2 | 4 | 8 | 12 | 16 | 24 | 32 | 40 | 48 | 64 | 80 | 96 | 160 |

- De 2 a 16 px dentro de componentes.
- De 24 a 48 px entre blocos.
- De 64 px para cima, entre seções.
- Na tela única (ADR 0022), 16 px entre os blocos e em volta da visão, para a altura sobrar para o conteúdo.
- Sempre mais espaço acima de um título do que abaixo dele.

### Grid · Carbon

O grid 2x do Carbon:

| Ponto de quebra | A partir de | Colunas | Margem |
|---|---|---|---|
| sm, celular | 320 px | 4 | 0 |
| md, tablet | 672 px | 8 | 16 px |
| lg, notebook | 1056 px | 16 | 16 px |
| xlg, desktop | 1312 px | 16 | 16 px |
| max, tela grande | 1584 px | 16 | 24 px |

Calhas: **larga, 32 px** (o padrão), **estreita, 16 px** (painéis e conteúdo mais junto) e **condensada, 1 px** (tabelas e listas densas).

As visões usam a largura toda da janela, sem o limite do ponto de quebra max, porque na tela única a largura é o que sobra para os gráficos ([ADR 0022](../adr/0022-visoes-em-tela-unica-no-computador.md), decisão 4).

### Raio · Liquid Glass

| Nome | Valor | Onde |
|---|---|---|
| Pequeno | 8 px | Etiquetas pequenas e miniaturas |
| Controle | 12 px | Campos, avisos e dicas flutuantes |
| Cartão | 20 px | Painéis, tabelas e bolhas do chat |
| Painel | 28 px | Superfícies grandes |
| Cápsula | 999 px | Botões, controle segmentado, chips e a entrada do chat |

### Elevação · Liquid Glass

| Nível | Sombra | Onde |
|---|---|---|
| 1 | `0 1px 3px rgba(0,0,0,.08), 0 6px 16px rgba(0,0,0,.06)` | Painéis, tabelas e cartões |
| 2 | `0 10px 34px rgba(0,0,0,.14)` | O que flutua: dicas e a entrada do chat |
| Brilho na borda | `inset 0 1px 1px rgba(255,255,255,.95), inset 0 -1px 1px rgba(0,0,0,.05), inset 0 0 20px rgba(255,255,255,.35)` | Toda superfície de vidro |

No escuro, a sombra precisa ser mais forte para aparecer, e o brilho mais fraco para não parecer uma borda acesa: o nível 1 usa preto a 40% e a 30%, o nível 2 usa preto a 50%, e o brilho usa branco a 14% no topo, preto a 30% na base e branco a 4% por dentro. As cores das sombras e do brilho são tokens semânticos, então a elevação muda de tema sem um valor próprio.

### Materiais de vidro · Liquid Glass

| Material | Preenchimento | Desfoque | Onde |
|---|---|---|---|
| Vidro claro | branco a 22% | 10 px, saturação 180% | O que flutua sobre o conteúdo: a barra de topo, o controle segmentado, os chips de filtro e o botão do chat |
| Vidro regular | branco a 82%, revisto na #64 | 26 px, saturação 180% | Tudo que tem dado ou texto: tabelas, dicas, avisos, campos, estados, botão secundário e bolhas do chat |
| Escurecimento | #161616 a 28% | nenhum | Por trás de uma superfície que pede foco, como o chat aberto no celular |

Toda superfície de vidro tem borda branca a 78% e o brilho na borda da elevação. No escuro, o preenchimento é o cinza 90 (#262626), a 40% no vidro claro e a 88% no regular, a borda é branca a 12%, e o escurecimento é preto a 50%.

**Campo de luz.** O vidro precisa de algo atrás para parecer vidro. O fundo da página leva manchas com as próprias cores do Carbon, sobre o cinza 10: azul 30 (#a6c8ff), roxo 30 (#d4bbff) e verde-azulado 20 (#9ef0f0). No escuro, as manchas usam o azul 80 (#002d9c), o roxo 80 (#491d8b) e o verde-azulado 80 (#004144).
- **Intensidade:** a cor cheia, como no painel de vidro do protótipo, decidida em 2026-09-27, na #64, depois de comparar 30%, 45% e a cor cheia com os mesmos componentes ([ADR 0020](../adr/0020-design-system-carbon-com-camada-liquid-glass.md), revisão de 2026-09-27).
- **Onde fica:** atrás da página inteira, parado em relação à janela, para sempre haver cor atrás do vidro em qualquer ponto da rolagem. É a variável `--campo-de-luz`, do `base.css`.
- **Na impressão:** some, e o fundo fica liso.

**Regras do vidro:**
- **Onde vai cada vidro:** o claro só no que flutua, e o regular em tudo que tem dado ou texto.
- **O contraste é medido no pior ponto:** o centro de uma mancha, atrás do vidro. Ali, o texto de ajuda fica em 4,59:1 e o link em 4,57:1 no claro, acima dos 4,5:1, e o teste `campo-de-luz.test.js` confere todos os textos que ficam sobre vidro.
- **O vermelho de erro sobre vidro é só para ícone.** Como texto, ele ficaria abaixo de 4,5:1 no escuro. A mensagem de erro do campo fica sobre o fundo da página.
- **Os gráficos não ficam no vidro,** e sim num cartão sólido, para as cores dos gráficos não dependerem do que está atrás.
- **Camadas:** no máximo duas camadas de vidro empilhadas.
- **Animação:** o desfoque nunca é animado, porque pesa na placa de vídeo.
- **Sem suporte a `backdrop-filter`:** a superfície vira sólida, na camada `layer-01` (#ffffff).
- **Na impressão e em PDF:** não há vidro, e as superfícies são sólidas.
- **Com alto contraste do sistema ligado:** as bordas passam a ser as do sistema.

### Movimento · Liquid Glass

| Nome | Duração | Onde |
|---|---|---|
| Mola curta | 200 ms | Passar o mouse |
| Mola média | 350 ms | Pressionar botão e chip, trocar de estado |
| Mola longa | 500 ms | A gota do controle segmentado e painéis que entram |

- **Mola suave para posição e escala:** a curva é uma função `linear()` do CSS, que passa uns 4% do ponto final antes de assentar.
- **Onde a curva não é suportada:** a curva produtiva do Carbon, `cubic-bezier(.2, 0, .38, .9)`, entra no lugar.
- **Cor e opacidade:** usam a curva do Carbon, sem mola.
- **Movimento reduzido:** com essa preferência ligada no sistema, toda animação e transição desliga.

## Componentes · Liquid Glass

Os componentes moram em `dashboard/src/componentes/`, um módulo por componente, e aparecem no [catálogo](../../dashboard/catalogo.html) nos dois temas, sobre o campo de luz, como ficam na página. Cada um tem teste unitário em `dashboard/tests/unit/componentes/`.

**Comum a todos.**
- **Estados:** normal, com o mouse em cima, com foco, pressionado e desativado. Quando fazem sentido, também carregando e erro.
- **Foco:** sempre visível, com anel de 2 px na cor de foco do tema.
- **Ícones:** os do Tabler Icons, os mesmos do protótipo, do pacote `@tabler/icons` 3.48.0 (MIT), citados pelo nome. O build junta só os ícones usados, e nenhum é buscado fora do site, como pede a política de segurança. O ícone é decorativo: o texto ao lado é o que se lê.
- **Textos:** todos no arquivo de tradução, pelo `t()`.

**Botões.** Cápsulas de 40 px de altura.
- **O que é:**
  - o primário, em azul 60 com brilho na borda, para a ação principal da área;
  - o secundário, em vidro regular, para ações de apoio;
  - o sutil, só texto em azul, para ações de pouco peso, como "Ver o SQL".
- **Comportamento:** sobem 1 px com o mouse em cima, encolhem para 96% com a mola média ao serem pressionados, e ficam a 40% de opacidade quando desativados. Carregando, mostram um indicador girando no lugar do texto, que fica transparente mas segura a largura, para a tela não pular.
- **Quando usar:** para disparar uma ação.
- **Quando não usar:** mais de um primário na mesma área, nem botão para trocar de visão, que é papel das abas e do controle segmentado.
- **Acessibilidade:** `<button>` nativo. Carregando, o botão fica ocupado (`aria-busy`) e ignora o clique, mas continua com o nome, porque o texto só fica transparente.

**Controle segmentado.** Opções exclusivas lado a lado, num trilho de vidro claro. A opção escolhida é uma gota de vidro que desliza até ela com a mola longa.
- **Quando usar:** para trocar de visão, de recorte ou de tema, com até cinco opções.
- **Quando não usar:** com mais de cinco opções, nem para filtros que se combinam, que é papel dos chips.
- **Acessibilidade:** segue o padrão de grupo de rádio da WAI-ARIA.
  - O Tab entra só na opção escolhida.
  - As setas trocam a opção e levam o foco junto, e Home e End vão para a primeira e a última.
  - Em tela estreita, as opções não quebram linha: o controle rola na horizontal, e a opção escolhida fica sempre à vista.

**Chips de filtro.** Cápsulas de vidro claro que se ligam e se desligam.
- **Selecionado:** fundo azul translúcido, borda azul, texto azul 70 no claro (azul 30 no escuro) e o ícone de confirmação.
- **Quando usar:** para filtros que se combinam entre si, como várias modalidades.
- **Quando não usar:** para disparar ações, que é papel dos botões, nem para opções exclusivas, que é papel do controle segmentado.
- **Acessibilidade:** botões com `aria-pressed`, num grupo com nome. A seleção aparece pelo ícone de confirmação, e não só pela cor.

**Campos de texto.** 40 px de altura, raio de controle, em vidro regular, com a borda forte, que tem 3:1 contra o vidro.
- **Foco:** borda azul e anel azul suave de 4 px.
- **Erro:** borda vermelha e uma mensagem que diz o problema e como resolver, com ícone. A mensagem fica sobre o fundo da página, embaixo do campo.
- **Desativado:** a 50% de opacidade.
- **Texto de exemplo:** o mesmo cinza do texto de ajuda, com 4,94:1 sobre o vidro. O valor do Carbon, preto a 40%, ficava em 2,69:1 (decidido em 2026-09-27, na #64).
- **Quando não usar:** o texto de exemplo no lugar do rótulo, porque ele some quando a pessoa começa a digitar.
- **Acessibilidade:** o rótulo fica sempre fora do campo, em `label-01`, ligado a ele. A ajuda e o erro ficam ligados ao campo por `aria-describedby`, e o erro marca o campo com `aria-invalid`.

**Etiqueta de quadrante.** Cápsula com o ponto na cor do quadrante, o ícone, o nome e o texto no tom escuro:
- Entrar: seta para cima e para a direita;
- Observar: olho;
- Não entrar: sinal de proibido;
- Manter: sinal de igual.

A matriz de espaço contra risco usa esta etiqueta nos cantos.
- **Quando não usar:** as cores dos quadrantes com outro significado na mesma tela, nem o nome do quadrante sem o ícone.
- **Acessibilidade:** o nome vai sempre junto do ícone, e o quadrante nunca aparece só pela cor.

**Etiqueta de alerta antecipado.** Cápsula em amarelo 10, com texto amarelo 80 e o ícone de sino.
- **Quando usar:** na célula em que a distância entre ativo problemático e carteira inadimplida abriu mais que a do país.
- **Quando não usar:** o amarelo de atenção para qualquer outra coisa na mesma tela.
- **Dentro de um gráfico,** onde a etiqueta não cabe, o alerta vira o marcador de alerta antecipado, nas mesmas cores (veja os componentes de gráfico).

**Tabela.** Vidro regular, com raio de cartão.
- **O que é:**
  - cabeçalho translúcido, em `heading-compact-01`;
  - números à direita, tabulares e com unidade;
  - linha com o mouse em cima em azul a 6%.
- **Quando usar:** em toda visão com gráfico, com os mesmos números (RF-G06), e para consultar muitas linhas.
- **Quando não usar:** cor de fundo para destacar linhas por valor. O destaque vem da ordenação e do filtro.
- **Acessibilidade:** legenda (`<caption>`) e cabeçalhos de coluna e de linha marcados. Em tela estreita, a tabela rola na horizontal dentro de uma região com nome, que recebe foco pelo teclado.

**Dica flutuante.** Vidro regular, raio de controle e elevação 2.
- **O que é:** o nome do item e os números dele. Nunca esconde informação que não esteja também na tela ou na tabela.
- **Quando usar:** para os números de um item, sem abrir o painel de detalhe. Os gráficos usam a dica do próprio ECharts, com o mesmo visual.
- **Acessibilidade:** segue a WCAG 2.2, critério 1.4.13.
  - Abre com o mouse e com o foco do teclado.
  - Dá para passar o mouse sobre ela sem que suma.
  - Fecha com o Esc, sem mover o foco.

**Avisos.** Vidro levemente tingido pela cor do estado, com o ícone num círculo.
- **Em linha** (decidido em 2026-10-05): o ícone menor e o texto em `label-01`, sem a caixa de vidro, para a ressalva dentro de um cartão. Existe para a tela única, em que a ressalva não pode ocupar um bloco, mas também não pode sumir atrás de um ícone ([ADR 0022](../adr/0022-visoes-em-tela-unica-no-computador.md), decisão 6).
- **Informação e erro:** a cor do estado vai no ícone.
- **Atenção:** o círculo é o amarelo de atenção, e o glifo fica escuro nos dois temas, como faz o Carbon.
- **Texto:** diz o problema e a saída, e nunca só "algo deu errado".
- **Quando não usar:** mais de dois avisos empilhados, nem aviso para o que cabe num rótulo.
- **Acessibilidade:** um aviso que aparece depois que a página abriu é anunciado a leitores de tela: o de erro com urgência, os outros com calma.

**Campo de seleção.** Um `<select>` nativo com o visual do campo de texto, para escolher uma entre muitas opções, como as 13 modalidades (#69).
- **Quando usar:** a partir de seis opções exclusivas, onde o controle segmentado não cabe.
- **Quando não usar:** com até cinco opções, que é papel do controle segmentado.
- **Acessibilidade:** o rótulo fica ligado ao campo, e a lista é a do navegador, que funciona pelo teclado e pelo leitor de tela sem nada a mais. Em tela estreita, o texto escolhido termina em reticências em vez de alargar a página.

**Definição do número** (RF-G07, #69). Um botão de informação junto do rótulo do número, que abre um popover nativo com o que a ontologia diz: a explicação em palavras comuns, a definição da fonte, a fonte e a confiança. Quando a regra é do próprio projeto, o popover aponta o ADR.
- **Quando usar:** ao lado de toda métrica que a tela mostra, no resumo e no painel de detalhe.
- **Quando não usar:** em rótulos que não são números da ontologia.
- **Acessibilidade:** o botão tem nome ("O que é Carteira PJ?"), o popover fecha com o Esc e com um clique fora, e o foco volta ao botão.

**Chat.**
- **Pergunta:** numa bolha azul 60.
- **Resposta:** em vidro regular, nesta ordem:
  1. o número, em tamanho grande;
  2. a frase curta;
  3. a ressalva, num aviso de informação;
  4. o SQL, recolhido atrás de "Ver o SQL", em `code-01`.
- **Quando o dado não permite responder:** a resposta diz isso e diz o que faltaria.
- **Entrada:** uma cápsula de vidro com botão circular de enviar.
- **Quando não usar:** número na resposta sem o SQL recolhido junto.
- **Acessibilidade:** a conversa é um registro que leitores de tela acompanham com calma. A entrada tem rótulo, e o botão de enviar tem nome.
- **O que fica para depois:** o destaque de cor do SQL entra com o cliente do chat, na #51. No catálogo, o exemplo é marcado como ilustrativo, porque o chat só existe na v0.3.

**Estados de carregamento e de exceção.**
- **Carregando:** barras em cápsula com brilho passando, no lugar do conteúdo. Nunca um indicador girando no meio da tela.
- **Vazio:** explica por que está vazio e como sair disso. Por exemplo: "Nenhuma combinação passa no corte de R$ 1 bi com esse filtro. Tire um dos filtros para ver mais."
- **Erro:** diz o problema e oferece a ação de tentar de novo.
- **Chat acordando:** um orbe de vidro que respira devagar, com o aviso de que as outras telas continuam funcionando.
- **Acessibilidade:** carregando é um status ocupado, com o texto só para leitores de tela, e o erro é anunciado com urgência. Com movimento reduzido, o brilho e a respiração param.

**Controle de tema.** O controle segmentado com claro, escuro e automático, na barra de topo (decidido em 2026-09-27, na #64).
- **O que faz:** automático é o padrão, e segue o sistema. Claro e escuro fixam o tema pelo atributo `data-tema`, e a escolha fica guardada no navegador do visitante.
- **Sem piscar:** o `public/tema-inicial.js`, um script pequeno e síncrono no `<head>`, servido pelo próprio site, aplica a escolha guardada antes da pintura.
- **Na impressão:** sai sempre claro, qualquer que seja a escolha.

**Barra de topo.** Em vidro claro, com o nome do produto, a navegação entre as visões e o controle de tema. A visão aberta fica marcada pela cor, pelo peso e pelo `aria-current` (RF-G01, desde a #69).

**Painel de detalhe** (RF-G05, #69). Em vidro regular, com o título do elemento escolhido, o recorte, a lista de chave e valor, um complemento opcional, como as modalidades de uma UF, e a nota de ressalva.
- **Sem elemento escolhido:** diz como escolher um.
- **No computador:** fica ao lado do conteúdo, sem janela por cima, e rola por dentro quando o conteúdo passa da altura. Na Tela 1, toma o lugar do ranking enquanto uma UF está escolhida, e fechar traz o ranking de volta.
- **No celular:** vira a folha que sobe de baixo, e o botão de fechar a recolhe.
- **Acessibilidade:** a troca de conteúdo é anunciada com calma, e o botão de fechar tem nome.

## Componentes de gráfico · nossos, sobre o ECharts

Os gráficos usam o ECharts ([ADR 0017](../adr/0017-interface-em-javascript-sem-framework.md)), com o tema montado a partir dos tokens, e moram em `dashboard/src/graficos/`. Todos aparecem no [catálogo](../../dashboard/catalogo.html), nos dois temas e com dado real do projeto. As decisões de 2026-09-27 saíram da revisão visual da #63.

**Tema e comportamento, comuns a todos.**
- **Cores dos tokens.** O ECharts não lê variáveis CSS, então o tema é montado em JavaScript por `tema.js`, com cada cor tirada do `tokens.json`. Nenhum hex é escrito à mão.
- **Tema do lugar.** Cada gráfico usa o tema do lugar onde está: o do sistema, o do atributo `data-tema` ou o do painel do catálogo. Na impressão, é sempre o claro.
- **Troca de tema sem recriar.** Quando o tema muda, a mesma instância recebe o tema novo e as cores novas. O gráfico não é destruído nem criado de novo, e um teste de ponta a ponta confere isso.
- **Fonte e tamanho.** O desenho espera a IBM Plex carregar, porque o ECharts mede o texto ao desenhar, e acompanha o tamanho do elemento.
- **Tela estreita.** Abaixo de 480 px de largura, o gráfico entra no modo estreito: nomes de eixo curtos, menos marcas e legendas abaixo do desenho.
- **Movimento reduzido.** Com a preferência do sistema ligada, não há animação.
- **Renderizador SVG.** As texturas saem como padrão vetorial, sem imagem embutida, o que respeita a política de segurança do site.

**Cartão de gráfico.** Um cartão sólido, e não de vidro, desde a #64: o token `color.chart.surface`, branco no claro e cinza 100 no escuro. O dado fica firme, e as cores dos gráficos não dependem do campo de luz atrás. Traz o cabeçalho do padrão de uso: título em `heading-02` e data-base com a fonte em `label-01`.
- **Quando usar:** em todo gráfico e número de destaque.
- **Quando não usar:** com frase de conclusão no cabeçalho, que o padrão proíbe.
- **Acessibilidade:** o título dá nome à região do cartão, e a data-base e a fonte são texto.
- **Cartão que preenche** (`cartao-grafico--preenche`): na tela única, o cartão ocupa a altura que a visão dá a ele, e o corpo fica com o que sobra do cabeçalho, rolando por dentro se passar. É o caso do ranking da Tela 1.

**Mapa por UF.** Pinta cada UF pela classe do valor, com a malha do IBGE, e a legenda fica em HTML, logo depois do mapa. A legenda é trocável: a lista de classes, por padrão, ou a legenda em escala.
- **O que é:** um mapa coroplético na rampa roxa, com cinco classes em quintis, ou em cinco faixas em torno de uma referência.
- **Quando usar:** quando a pergunta é onde, no território, um número é alto ou baixo.
- **Quando não usar:** quando os estados pequenos precisam ser lidos, porque o DF e Sergipe quase somem. Nesse caso, o cartograma. Também não serve para mostrar valor exato: o mapa mostra a classe, e o número fica na dica e na tabela.
- **Acessibilidade:** a legenda é texto, e as fronteiras na cor do fundo separam vizinhas de cores próximas. Sem a malha, o cartão mostra o estado de erro e diz que o cartograma e a tabela continuam funcionando.
- **A malha,** versionada desde a #67 em `public/geo/ufs.json`: a malha territorial de 2022 do IBGE, na qualidade mínima, com a geometria sem alteração. Essa qualidade não traz as ilhas oceânicas, então Fernando de Noronha, de PE, e Trindade e Martim Vaz, do ES, não aparecem no mapa.

**Cartograma de grade.** Cada UF vira um quadrado do mesmo tamanho, com a sigla, numa grade que preserva a posição aproximada no mapa, com as mesmas classes do mapa.
- **Quando usar:** como alternativa ao mapa quando os estados pequenos importam (RF-103), e sempre que a malha não carregar, porque o cartograma não depende dela.
- **Quando não usar:** quando a área ou o formato do território fazem parte da leitura.
- **Acessibilidade:** a sigla usa o texto que mais contrasta com o preenchimento.
- **A grade,** revisada em 2026-09-27, em `ufs.js`: cada UF fica perto do centroide dela na malha do IBGE, e todo par de UFs vizinhas na grade aponta a menos de 60 graus da direção real. O teste `ufs.test.js` confere isso.

**Matriz 2x2.** A matriz de espaço contra risco do [ADR 0014](../adr/0014-matriz-de-decisao-espaco-contra-risco.md).
- **O que é:** cada ponto é uma célula de UF e modalidade.
  - O eixo horizontal é a carteira por empresa em vezes a mediana das UFs, em escala de base 2.
  - O eixo vertical é a variação da inadimplência além da do país, em pontos percentuais.
  - As linhas de corte ficam no 1 e no zero, e os pontos usam a marca do quadrante.
- **Eixos invertidos** (decidido em 2026-09-27): Entrar fica no canto superior direito, Não entrar no inferior esquerdo, Manter no superior esquerdo e Observar no inferior direito.
- **Quando usar:** na recomendação, para mostrar a regra de decisão e onde cada célula caiu.
- **Quando não usar:** para comparar valores exatos entre células, que é papel do ranking e da tabela.
- **Acessibilidade:** o quadrante aparece por três caminhos, e nunca só pela cor: a posição em relação às linhas de corte, a etiqueta com ícone e nome em cada canto, e a dica de cada ponto. Em tela estreita, as etiquetas descem para baixo do gráfico.

**Série temporal com projeção.** Linha no tempo, na notação IBCS.
- **O que é:** o realizado é uma linha sólida. A projeção é uma linha tracejada, com o intervalo hachurado em volta, e a legenda mostra as duas formas.
- **Cor e espessura** (decidido em 2026-09-27): a primeira cor categórica, a mesma do ranking, com linha de 3 px.
- **Quando usar:** para evolução mensal e para a projeção de três meses (RF-301).
- **Quando não usar:** com mais de uma unidade no mesmo gráfico. Dois eixos verticais nunca: medidas diferentes vão em gráficos separados.
- **Acessibilidade:** realizado e projeção se distinguem pela forma, sólida ou tracejada, e não pela cor. O intervalo aparece na dica de cada mês projetado.
- **No catálogo,** a projeção é ilustrativa: repete o último mês, com um intervalo de dois desvios das variações mensais. A projeção do modelo chega com a #27.

**Ranking.** Barras horizontais, da maior para a menor, com o valor na ponta de cada uma e uma linha de referência opcional, como a mediana das UFs.
- **Quando usar:** para ordenar UFs ou modalidades por um número, e para achar um item pelo nome.
- **Quando não usar:** com dezenas de itens, que é papel da tabela, nem com cor diferente por barra.
- **Acessibilidade:** o valor fica escrito na ponta de cada barra, e o nome de cada item é texto no eixo.

**Série com duas medidas** (#70). Duas linhas no tempo, na mesma unidade, para o leitor ver as duas andarem juntas ou se afastarem, com um marco e uma janela opcionais.
- **O que é:** a medida principal é uma linha sólida, na primeira cor categórica, e a de comparação é tracejada, no cinza do texto secundário. As duas têm legenda e o último valor escrito na ponta, na cor da linha.
- **Marco:** uma linha vertical num mês, com um rótulo curto, como a mudança de critério do ativo problemático em jan/2025.
- **Janela:** uma faixa clara entre dois meses, como os 6 meses que a decisão compara.
- **Na Tela 2:** no painel da UF, a taxa de inadimplência e a de ativo problemático, mês a mês.
- **Quando usar:** para duas medidas da mesma unidade cuja distância importa.
- **Quando não usar:** com unidades diferentes, que vão em gráficos separados, nunca em dois eixos; nem com mais de duas linhas.
- **Acessibilidade:** as duas linhas se distinguem pela forma, sólida ou tracejada, além da cor, e a dica de cada mês traz os dois valores.

**Marcador de alerta antecipado** (#70). Um anel pequeno, com o fundo e a borda nas cores da etiqueta de alerta antecipado, desenhado em texto rico do ECharts, sem imagem.
- **Onde vai:** no centro da UF, no mapa; ao lado da sigla, na grade; depois do valor, no ranking. A legenda em escala ganha o item "Alerta antecipado" quando o desenho usa o marcador.
- **Quando usar:** para marcar o alerta antecipado dentro de um gráfico, onde a etiqueta, com sino e texto, não cabe. Fora dos gráficos, como no painel e na tabela, vai a etiqueta.
- **Quando não usar:** para qualquer outra marca: ele nunca muda a cor da área nem o quadrante (ADR 0014, decisão 6).
- **Acessibilidade:** a dica da UF diz "alerta antecipado", e a tabela traz a etiqueta com o texto.

**Número de destaque.** Um número só, em `heading-07`, com o rótulo do que ele mede, numa frase que uma pessoa diria. É HTML, e não gráfico.
- **Quando usar:** quando a resposta é um número, como a carteira onde a regra recomenda entrar.
- **Quando não usar:** para vários números lado a lado, que é papel da tabela ou do painel de detalhe.
- **Acessibilidade:** é lido como texto. Em tela estreita, desce para o `heading-05`, sem quebrar a unidade.

**Matriz de calor** (#69). Uma linha por item e uma coluna por categoria, com cada célula pintada pela classe do valor, nas mesmas classes do mapa, para os dois se lerem igual.
- **O que é na Tela 1:** a distância até a mediana em cada UF e modalidade. No computador fica deitada, com as modalidades nas linhas e as UFs nas colunas; no celular, de pé.
- **Células:** a que fica fora da comparação leva a textura listrada; a que não existe fica vazia. A célula escolhida ganha o destaque, e o rótulo da linha e o da coluna dela ficam em negrito.
- **Rótulos das colunas:** siglas ficam retas enquanto cada coluna tiver pelo menos 20 px; abaixo disso, e com nomes longos, giram.
- **Quando usar:** para ver de uma vez em quais itens e em quais categorias um número está alto ou baixo.
- **Quando não usar:** para comparar o tamanho de uma oportunidade, porque a célula mostra a classe, e não quanto; isso é papel do ranking.
- **Acessibilidade:** cada célula tem a dica com a UF, a modalidade e a posição, e os números estão na tabela.

**Legenda em escala** (revisão da Tela 1, em 2026-10-05). Uma barra compacta em degradê contínuo, com as pontas em cápsula, o que ela mede em cima, as divisas das classes marcadas embaixo e o sentido de cada ponta.
- **O degradê passa pela cor de cada classe no meio da faixa dela,** e as marcas mostram onde uma classe termina e a outra começa, porque o mapa pinta por classe.
- **Na Tela 1:** vai de "Menos espaço", à esquerda, a "Mais espaço", à direita, com as divisas em +30%, +10%, −10% e −30% da mediana. Fica no canto inferior direito do palco, sobre o mar, no mapa e na grade; embaixo, à direita, na matriz.
- **Na Tela 2:** vai de "Melhor que o país", à esquerda, a "Pior que o país", à direita, com as divisas em −0,5, −0,1, +0,1 e +0,5 ponto percentual, no mesmo lugar da Tela 1.
- **Quando usar:** para faixas ordenadas em torno de uma referência, em que o leitor precisa ver a direção.
- **Quando não usar:** para categorias sem ordem, que é papel da lista de classes.
- **Acessibilidade:** a barra e as marcas ficam fora da leitura, e cada classe vem por extenso numa lista para leitores de tela. A amostra listrada de quem fica sem comparação vem logo abaixo.

## Padrões de uso · Liquid Glass

**Cabeçalho do gráfico, sem bloco de título na visão e sem conclusão escrita.** Decidido em 2026-09-26: as visões não têm bloco de título-conclusão no topo, e os gráficos não trazem conclusão escrita, para controlar o escopo. A visão abre nos filtros e na visualização, e cada gráfico traz um cabeçalho com duas partes:
- **Título do gráfico,** em `heading-02`, dizendo o que o gráfico mostra, como "Espaço contra risco, por estado e modalidade".
- **Data-base e fonte,** em `label-01`, sempre.

Quem quiser tirar uma conclusão pergunta ao chat, nas visões que o têm.

Não usar: rótulo genérico como "Gráfico 1", nem frase de conclusão no gráfico, digitada à mão ou gerada do dado.

**Barra de filtros.** Numa linha só, acima do conteúdo. Campo de seleção para muitas opções, controle segmentado para opções exclusivas, chips para filtros que se combinam. Filtrar nunca repinta as cores. A forma de ver uma visualização, como "Mapa | Grade | Matriz | Tabela", também fica na barra, junto dos filtros.

**Painel de detalhe.** Lista de chave e valor, com números à direita e com unidade. Abre ao lado do conteúdo, sem janela por cima, e rola por dentro.

**Fronteira do dado.** O que o dado não permite afirmar fica junto da recomendação, nunca no rodapé nem escondido em nota ([ADR 0005](../adr/0005-projeto-termina-em-recomendacao.md)).

**Alternativa em tabela.** Toda visão com gráfico tem uma tabela com os mesmos números, para quem não lê cor ou prefere números. Desde a #69, ela é uma das formas de ver o cartão, e não um bloco embaixo da página, com o download em CSV junto dela ([ADR 0022](../adr/0022-visoes-em-tela-unica-no-computador.md), decisão 5).

## Modelos de página · grid do Carbon, modelos nossos

Esqueletos genéricos, sem dado e sem ligação com uma visão específica. Cada visão escolhe o modelo que serve à pergunta dela, e visões diferentes podem usar grids diferentes. O protótipo desenha os sete.

| Modelo | Colunas, no grid de 16 | Chat | Quando usar |
|---|---|---|---|
| Visualização em largura total | Visualização 16, apoio 8 + 8 | Não | Uma visualização domina a visão, como um mapa ou uma série no tempo |
| Visualização com painel de detalhe | Visualização 11, detalhe 5 | Não | Clicar num elemento abre o detalhe ao lado |
| Com trilho do chat | Conteúdo 12, chat 4 | Sim | Visões em que perguntar aos dados ajuda a explorar |
| Visual em tela cheia com painéis de vidro | Visual 16, painéis flutuantes de 4 | Opcional, num botão | Visuais espaciais, como um mapa, em que o contexto importa mais que a moldura |
| Tabela ou lista densa | Tabela 16, calha condensada | Não | Ranking e consulta de muitas linhas |
| Palco em tela única | Painéis dos lados, 1 fração cada; palco no centro, 2 frações | Não | Um visual espacial domina a visão, sem rolagem da página, como o mapa da Tela 1 ([ADR 0022](../adr/0022-visoes-em-tela-unica-no-computador.md)) |
| Celular | 4 colunas, tudo empilhado | Com ou sem | O detalhe abre numa folha que sobe de baixo; o chat vira um botão |

**Regras dos modelos:**
- **O chat é opcional por visão.** Quando existe, fica num trilho de 4 colunas à direita no desktop, ou num botão flutuante nos modelos de tela cheia e no celular. Nunca cobre o conteúdo no desktop.
- **Nenhuma visão tem bloco de título no topo.** A visão abre nos filtros e na visualização, e o cabeçalho de cada gráfico tem só o título e a data-base com a fonte.
- **Toda visão tem a alternativa em tabela.**
- **Tela única** ([ADR 0022](../adr/0022-visoes-em-tela-unica-no-computador.md)): a partir de uma janela de 1280×720 px, toda visão cabe sem rolagem da página, e o que passa da altura de um cartão rola dentro dele. Abaixo disso, a página rola, sem nada cortado.
- **No palco em tela única,** o visual fica num cartão sólido grande, na altura toda, com o campo de luz aparecendo em volta. À esquerda ficam os filtros e o que o visual mostra (título, fonte, resumo e ressalvas); à direita, os números e o detalhe. Formas que pedem largura, como uma matriz ou uma tabela, ocupam também a coluna da direita. Empilhado, o visual vem logo depois dos filtros. O modelo mora em `dashboard/src/visoes/palco.css`, e a visão que o usa leva a classe `visao--palco`.
- **Painel inteiro** (`visao--painel-inteiro`, Tela 2): quando o painel da UF leva um gráfico, como a série mensal, ele toma a coluna da direita inteira, também o lugar do número de destaque. Sem essa classe, como na Tela 1, o painel toma só o lugar do ranking.

## Conteúdo

- **Números no formato brasileiro,** como no quadro abaixo.
- **Modalidades com o nome do BCB.** A abreviação ("Fin. rurais") só entra onde falta espaço, com o nome completo na dica flutuante.
- **Terminologia fixa:** Entrar, Observar, Manter e Não entrar; custo de errar; fronteira do dado; alerta antecipado ([ADR 0014](../adr/0014-matriz-de-decisao-espaco-contra-risco.md)).
- **Frases que uma pessoa diria,** com a condição antes da consequência e sem jargão de dado na interface principal.
- **Erros e estados vazios dizem o problema e a saída.**

| O quê | Formato |
|---|---|
| Reais | R$ 485,5 bi · R$ 61,6 mil |
| Taxa | 0,93% |
| Variação de taxa | +0,15 p.p. |
| Data-base | jul/2026 |

## Acessibilidade

- **Critério:** WCAG 2.2 AA. Texto a partir de 4,5:1, elemento gráfico a partir de 3:1, com os contrastes medidos nas tabelas acima.
- **Nenhum significado só por cor:** ícone e rótulo junto de cada cor.
- **Foco sempre visível,** e todo controle funciona pelo teclado.
- **Área de toque:** 40 px, acima do mínimo de 24 px da WCAG 2.2.
- **Movimento reduzido respeitado,** alto contraste do sistema respeitado, e alternativa em tabela em toda visão.
- **Idioma:** página marcada como português do Brasil.

## Tokens e governança

- **Nomes dos tokens:** seguem o Atlassian (ADR 0018), com a referência ao token do Carbon de onde vêm. Por exemplo, `color.text.secondary` vem de `text-secondary` (#525252), e `color.chart.categorical.1` é a primeira cor categórica.
- **Tokens da camada Liquid Glass:** nomes próprios, como `material.vidro.regular`, `radius.capsula` e `motion.mola.media`.
- **Tokens de componente:** em `tokens/componentes/`, como `botao.primario.fundo`, `segmentado.gota` e `aviso.atencao.glifo`, sempre apontando para cores semânticas ou primitivas.
- **Onde moram:** `dashboard/tokens/`, em três pastas, `primitivos/`, `semanticos/` e `componentes/`. O `scripts/gerar-tokens.js` gera o `src/estilos/tokens.css` e o `tokens.json`, que nunca são editados à mão, e o CI reprova quando eles divergem dos tokens.
- **Formato:** DTCG 2025.10, com a cor no formato novo, de espaço de cor e componentes. A mola é uma função `linear()` do CSS, que o DTCG não descreve; ela fica em `$extensions`, com a curva do Carbon como valor de reserva.
- **Catálogo:** o [catálogo](../../dashboard/catalogo.html) mostra as fundações, os componentes, as paletas e os gráficos nos dois temas, lidos dos tokens. O teste de contraste confere os pares de cor nos dois temas, e o do campo de luz, o texto sobre o vidro no pior ponto.
- **Mudança em fundação** (cor, tipo, espaço, grid) só com ADR, porque muda a relação com o Carbon oficial.
- **Componente novo ou alterado** entra por PR que atualiza este guia e o protótipo no mesmo commit.
- **Paleta nova ou alterada** passa pela validação de contraste e de daltonismo antes de entrar. O teste automatizado, `dashboard/tests/unit/paletas.test.js`, lê as paletas dos tokens e reprova a que ficar fora dos critérios do [ADR 0021](../adr/0021-paletas-de-grafico-do-carbon-validadas.md).

## Pendências

| Pendência | Onde se resolve |
|---|---|
| Conferir o vidro no Firefox a olho. O WebKit, motor do Safari, foi conferido na #64, e o Firefox roda os testes de ponta a ponta e o axe no CI, mas não abre na máquina de desenvolvimento | No site publicado, depois da #69 |
| Nome e identidade visual do produto | Em aberto |

## Fontes

Acessadas em 2026-09-26, menos as marcadas com outra data.

- [Carbon Design System](https://carbondesignsystem.com/) e [paletas de visualização de dados do Carbon](https://carbondesignsystem.com/data-visualization/color-palettes/).
- Código publicado dos pacotes `@carbon/themes` 11.82.0, `@carbon/colors` 11.59.0, `@carbon/type` 11.68.0, `@carbon/layout` 11.60.0 e `@carbon/grid` 11.63.0, de onde saíram os valores de cor, tipo, espaço e grid.
- [Materiais, nas diretrizes de interface da Apple](https://developer.apple.com/design/human-interface-guidelines/materials), e o [anúncio do novo design da Apple](https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/), de 2025.
- Código publicado do `@carbon/charts` 1.27.20, `scss/_color-palette.scss`, de onde saíram as paletas categóricas, monocromáticas e divergentes oficiais. Acessado em 2026-09-27.
- G. M. Machado, M. M. Oliveira e L. A. F. Fernandes, ["A Physiologically-based Model for Simulation of Color Vision Deficiency"](https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html), IEEE TVCG 15(6), 2009, para a simulação de daltonismo. Acessado em 2026-09-27.
- [OKLab, de Björn Ottosson](https://bottosson.github.io/posts/oklab/), para a luminosidade, o croma e a distância entre cores. Acessado em 2026-09-27.
- [API de malhas do IBGE](https://servicodados.ibge.gov.br/api/docs/malhas), para os centroides que conferem a grade do cartograma, e a grade `br_states_grid1` do [geofacet](https://github.com/hafen/grid-designer), ponto de partida da grade. Acessados em 2026-09-27.
- [Guia de glassmorphism da UX Pilot](https://uxpilot.ai/blogs/glassmorphism-ui), para as faixas de desfoque e de transparência e as regras de contraste sobre vidro.
