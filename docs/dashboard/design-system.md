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

Itens marcados **em aberto** ainda não foram decididos e não são regra.

## Princípios

1. **Cor só onde há significado.** Neutros na maior parte da tela, o azul do Carbon para ação e seleção, e as cores dos quadrantes só onde há decisão.
2. **Todo número mostra de onde veio.** Data-base e fonte sempre visíveis e, no chat, o SQL que gerou o número.
3. **O vidro flutua, e o dado fica firme.** Vidro nos controles e nas superfícies que flutuam; tabela, gráfico e texto com contraste medido.
4. **Nenhum significado só por cor.** Quadrante, estado e alerta levam ícone e rótulo junto da cor.
5. **Movimento comunica mudança de estado,** e some quando o sistema pede movimento reduzido.

## Fundações

### Cor · Carbon

Tema **g10** do Carbon. O contraste foi medido contra o fundo (#f4f4f4) e contra o vidro regular sobre o fundo (#fbfbfb).

**Neutros e ação**

| Uso | Token do Carbon | Valor | Contraste no fundo | No vidro |
|---|---|---|---|---|
| Fundo da página | `background` | #f4f4f4 | | |
| Camada sólida | `layer-01` | #ffffff | | |
| Borda sutil | `border-subtle-01` | #e0e0e0 | | |
| Borda sutil em camada | `border-subtle-00` | #c6c6c6 | | |
| Borda forte | `border-strong-01` | #8d8d8d | 3,02:1 | 3,21:1 |
| Texto principal | `text-primary` | #161616 | 16,45:1 | 17,49:1 |
| Texto secundário | `text-secondary` | #525252 | 7,10:1 | 7,55:1 |
| Texto de ajuda | `text-helper` | #6f6f6f | 4,57:1 | 4,86:1 |
| Texto de exemplo nos campos | `text-placeholder` | `rgba(22, 22, 22, 0.4)` | | |
| Ação e foco | `interactive`, `focus` | #0f62fe (azul 60) | 4,55:1 | 4,83:1 |
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
- uma escolha manual pelo atributo `data-tema` já funciona, mas o botão de troca **está em aberto** e, se entrar, entra na #64.

**Neutros e ação.** O contraste é medido contra o fundo (#161616) e contra o vidro regular sobre o fundo (#222222).

| Uso | Token do Carbon | Valor | Contraste no fundo | No vidro |
|---|---|---|---|---|
| Fundo da página | `background` | #161616 (cinza 100) | | |
| Camada sólida | `layer-01` | #262626 (cinza 90) | | |
| Borda sutil | `border-subtle-01` | #525252 | | |
| Borda sutil em camada | `border-subtle-00` | #393939 | | |
| Borda forte | `border-strong-01` | #6f6f6f | 3,60:1 | 3,17:1 |
| Texto principal | `text-primary` | #f4f4f4 | 16,45:1 | 14,47:1 |
| Texto secundário | `text-secondary` | #c6c6c6 | 10,59:1 | 9,31:1 |
| Texto de ajuda | `text-helper` | #a8a8a8 | 7,61:1 | 6,69:1 |
| Texto de exemplo nos campos | `text-placeholder` | `rgba(244, 244, 244, 0.4)` | 3,60:1 | |
| Ação | `interactive` | #4589ff (azul 50) | 5,41:1 | 4,75:1 |
| Link | `link-primary` | #78a9ff (azul 40) | 7,68:1 | 6,76:1 |
| Foco | `focus` | #ffffff | 18,10:1 | 15,91:1 |
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

- **Categórica,** para identidade, como modalidades: a paleta categórica oficial do Carbon, em ordem fixa (#6929c4, #1192e8, #005d5d, #9f1853, #fa4d56, #570408).
  - Até seis séries. A partir da sétima, as menores viram "Outros". Uma cor nova nunca é gerada.
  - A cor segue a série, e não a posição: um filtro que tira séries não repinta as que ficam.
  - **Pendente:** na validação, o #570408 sai da faixa de luminosidade e o #005d5d fica sem saturação. O ajuste é decidido na #63.
- **Sequencial,** para magnitude: uma matiz só, do claro ao escuro.
- **Divergente,** para desvio contra o país: duas matizes, com cinza no ponto neutro, que é a variação do país.
- **Qual paleta sequencial e qual divergente:** as duas são escolhidas entre as oficiais do Carbon e validadas na #63.

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
| Vidro claro | branco a 22% | 10 px, saturação 180% | O que flutua sobre o conteúdo: navegação, filtros, botão do chat |
| Vidro regular | branco a 62% | 26 px, saturação 180% | Tabelas, dicas, painéis de detalhe e bolhas do chat |
| Escurecimento | #161616 a 28% | nenhum | Por trás de uma superfície que pede foco, como o chat aberto no celular |

Toda superfície de vidro tem borda branca a 78% e o brilho na borda da elevação. No escuro, o preenchimento é o cinza 90 (#262626), a 40% no vidro claro e a 72% no regular, a borda é branca a 12%, e o escurecimento é preto a 50%.

**Campo de luz.** O vidro precisa de algo atrás para parecer vidro. O fundo da página leva manchas suaves com as próprias cores do Carbon, sobre o cinza 10: azul 30 (#a6c8ff), roxo 30 (#d4bbff) e verde-azulado 20 (#9ef0f0), de 30% a 50% de opacidade. No escuro, as manchas usam o azul 80 (#002d9c), o roxo 80 (#491d8b) e o verde-azulado 80 (#004144), com a mesma opacidade.

**Regras do vidro:**
- **Onde vai cada vidro:** o claro só no que flutua, e o regular em tudo que tem dado ou texto. O texto de ajuda mantém 4,86:1 sobre o vidro regular.
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

Todo componente tem os estados normal, com o mouse em cima, com foco, pressionado e desativado. Quando fazem sentido, também carregando e erro. O foco é sempre visível: anel de 2 px em #0f62fe.

**Botões.** Cápsulas de 40 px de altura.
- **Primário:** azul 60 com brilho na borda.
- **Secundário:** vidro regular.
- **Sutil:** só texto em azul.
- **Comportamento:** sobem 1 px com o mouse em cima, encolhem para 96% com a mola média ao serem pressionados, e ficam a 40% de opacidade quando desativados.
- **Carregando:** mostra um indicador girando e mantém a largura, para a tela não pular.
- **Não usar:** mais de um primário na mesma área, nem botão para trocar de visão, que é papel das abas e do controle segmentado.

**Controle segmentado.**
- **Trilho:** em vidro claro.
- **Opção escolhida:** é uma gota de vidro que desliza até ela com a mola longa.
- **Teclado:** as setas trocam a opção.
- **Uso:** trocar de visão ou de recorte, com até cinco opções.
- **Não usar:** com mais de cinco opções, nem para filtros que se combinam, que é papel dos chips.

**Chips de filtro.**
- **Forma:** cápsulas de vidro.
- **Selecionado:** fundo azul translúcido, borda azul, texto azul 70 (#0043ce, 7,09:1 sobre o azul 10) e ícone de confirmação.
- **Uso:** filtros que se combinam entre si.
- **Não usar:** para disparar ações, que é papel dos botões, nem para opções exclusivas, que é papel do controle segmentado.

**Campos de texto.**
- **Forma:** 40 px de altura, raio de controle, em vidro.
- **Foco:** borda azul e anel azul suave de 4 px.
- **Erro:** borda vermelha e uma mensagem que diz o problema e como resolver, com ícone.
- **Desativado:** a 50% de opacidade.
- **Rótulo:** sempre fora do campo, em `label-01`.
- **Não usar:** o texto de exemplo no lugar do rótulo, porque ele some quando a pessoa começa a digitar.

**Etiqueta de quadrante.** Cápsula com o ponto na cor do quadrante, o ícone, o nome e o texto no tom escuro:
- Entrar: seta para cima e para a direita;
- Observar: olho;
- Não entrar: sinal de proibido;
- Manter: sinal de igual.

Não usar: as cores dos quadrantes com outro significado na mesma tela, nem o nome do quadrante sem o ícone.

**Etiqueta de alerta antecipado.** Cápsula em amarelo 10 com texto amarelo 80 e ícone de sino.
Não usar: o amarelo de atenção para qualquer outra coisa na mesma tela.

**Tabela.**
- **Superfície:** vidro regular, com raio de cartão.
- **Cabeçalho:** translúcido, em `heading-compact-01`.
- **Números:** à direita, tabulares e com unidade.
- **Linha com o mouse em cima:** fundo azul a 6%.
- **Não usar:** cor de fundo para destacar linhas por valor. O destaque vem da ordenação e do filtro.

**Dica flutuante.** Vidro regular, raio de controle e elevação 2. Traz o nome do item e os números dele, e nunca esconde informação que não esteja também na tela ou na tabela.

**Avisos.** Vidro levemente tingido pela cor do estado, com o ícone num círculo.
- **Informação e erro:** a cor do estado vai no ícone.
- **Atenção:** o círculo é amarelo #f1c21b e o glifo é #161616.
- **Texto:** diz o problema e a saída, e nunca só "algo deu errado".
- **Não usar:** mais de dois avisos empilhados, nem aviso para o que cabe num rótulo.

**Chat.**
- **Pergunta:** numa bolha azul 60.
- **Resposta:** em vidro regular, nesta ordem:
  1. o número, em tamanho grande;
  2. a frase curta;
  3. a ressalva, num aviso de informação;
  4. o SQL, recolhido atrás de "Ver o SQL", em `code-01`.
- **Quando o dado não permite responder:** a resposta diz isso e diz o que faltaria.
- **Entrada:** uma cápsula de vidro com botão circular de enviar.
- **Não usar:** número na resposta sem o SQL recolhido junto.

**Estados de carregamento e de exceção.**
- **Carregando:** barras em cápsula com brilho passando, no lugar do conteúdo. Nunca um indicador girando no meio da tela.
- **Vazio:** explica por que está vazio e como sair disso. Por exemplo: "Nenhuma combinação passa no corte de R$ 1 bi com esse filtro. Tire um dos filtros para ver mais."
- **Erro:** diz o problema e oferece a ação de tentar de novo.
- **Chat acordando:** um orbe de vidro que respira devagar, com o aviso de que as outras telas continuam funcionando.

## Padrões de uso · Liquid Glass

**Cabeçalho do gráfico, sem bloco de título na visão e sem conclusão escrita.** Decidido em 2026-09-26: as visões não têm bloco de título-conclusão no topo, e os gráficos não trazem conclusão escrita, para controlar o escopo. A visão abre nos filtros e na visualização, e cada gráfico traz um cabeçalho com duas partes:
- **Título do gráfico,** em `heading-02`, dizendo o que o gráfico mostra, como "Espaço contra risco, por estado e modalidade".
- **Data-base e fonte,** em `label-01`, sempre.

Quem quiser tirar uma conclusão pergunta ao chat, nas visões que o têm.

Não usar: rótulo genérico como "Gráfico 1", nem frase de conclusão no gráfico, digitada à mão ou gerada do dado.

**Barra de filtros.** Numa linha só, acima do conteúdo. Controle segmentado para opções exclusivas, chips para filtros que se combinam. Filtrar nunca repinta as cores.

**Painel de detalhe.** Lista de chave e valor, com números à direita e com unidade. Abre ao lado do conteúdo, sem janela por cima.

**Fronteira do dado.** O que o dado não permite afirmar fica junto da recomendação, nunca no rodapé nem escondido em nota ([ADR 0005](../adr/0005-projeto-termina-em-recomendacao.md)).

**Alternativa em tabela.** Toda visão com gráfico tem uma tabela com os mesmos números, para quem não lê cor ou prefere números.

## Modelos de página · grid do Carbon, modelos nossos

Esqueletos genéricos, sem dado e sem ligação com uma visão específica. Cada visão escolhe o modelo que serve à pergunta dela, e visões diferentes podem usar grids diferentes. O protótipo desenha os seis.

| Modelo | Colunas, no grid de 16 | Chat | Quando usar |
|---|---|---|---|
| Visualização em largura total | Visualização 16, apoio 8 + 8 | Não | Uma visualização domina a visão, como um mapa ou uma série no tempo |
| Visualização com painel de detalhe | Visualização 11, detalhe 5 | Não | Clicar num elemento abre o detalhe ao lado |
| Com trilho do chat | Conteúdo 12, chat 4 | Sim | Visões em que perguntar aos dados ajuda a explorar |
| Visual em tela cheia com painéis de vidro | Visual 16, painéis flutuantes de 4 | Opcional, num botão | Visuais espaciais, como um mapa, em que o contexto importa mais que a moldura |
| Tabela ou lista densa | Tabela 16, calha condensada | Não | Ranking e consulta de muitas linhas |
| Celular | 4 colunas, tudo empilhado | Com ou sem | O detalhe abre numa folha que sobe de baixo; o chat vira um botão |

**Regras dos modelos:**
- **O chat é opcional por visão.** Quando existe, fica num trilho de 4 colunas à direita no desktop, ou num botão flutuante nos modelos de tela cheia e no celular. Nunca cobre o conteúdo no desktop.
- **Nenhuma visão tem bloco de título no topo.** A visão abre nos filtros e na visualização, e o cabeçalho de cada gráfico tem só o título e a data-base com a fonte.
- **Toda visão tem a alternativa em tabela.**

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
- **Onde moram:** `dashboard/tokens/`, em três pastas, `primitivos/`, `semanticos/` e `componentes/`. O `scripts/gerar-tokens.js` gera o `src/estilos/tokens.css` e o `tokens.json`, que nunca são editados à mão, e o CI reprova quando eles divergem dos tokens.
- **Formato:** DTCG 2025.10, com a cor no formato novo, de espaço de cor e componentes. A mola é uma função `linear()` do CSS, que o DTCG não descreve; ela fica em `$extensions`, com a curva do Carbon como valor de reserva.
- **Catálogo:** o [catálogo](../../dashboard/catalogo.html) mostra as fundações nos dois temas, lidas dos tokens, e o teste de contraste confere os pares de cor nos dois temas.
- **Mudança em fundação** (cor, tipo, espaço, grid) só com ADR, porque muda a relação com o Carbon oficial.
- **Componente novo ou alterado** entra por PR que atualiza este guia e o protótipo no mesmo commit.
- **Paleta nova ou alterada** passa pela validação de contraste e de daltonismo antes de entrar. O teste automatizado nasce na #63.

## Pendências

| Pendência | Onde se resolve |
|---|---|
| Paleta categórica oficial do Carbon falha na validação | #63 |
| Escolher as paletas sequencial e divergente do Carbon e validá-las | #63 |
| Texto de exemplo nos campos: o valor oficial do Carbon fica em 2,53:1 no claro e 3,60:1 no escuro, abaixo dos 4,5:1 de texto | #64, ao construir os campos |
| Conferir a camada Liquid Glass em Safari e Firefox, e a alternativa sem `backdrop-filter` | #62 a #64 |
| Nome e identidade visual do produto | Em aberto |

## Fontes

Todas acessadas em 2026-09-26.

- [Carbon Design System](https://carbondesignsystem.com/) e [paletas de visualização de dados do Carbon](https://carbondesignsystem.com/data-visualization/color-palettes/).
- Código publicado dos pacotes `@carbon/themes` 11.82.0, `@carbon/colors` 11.59.0, `@carbon/type` 11.68.0, `@carbon/layout` 11.60.0 e `@carbon/grid` 11.63.0, de onde saíram os valores de cor, tipo, espaço e grid.
- [Materiais, nas diretrizes de interface da Apple](https://developer.apple.com/design/human-interface-guidelines/materials), e o [anúncio do novo design da Apple](https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/), de 2025.
- [Guia de glassmorphism da UX Pilot](https://uxpilot.ai/blogs/glassmorphism-ui), para as faixas de desfoque e de transparência e as regras de contraste sobre vidro.
