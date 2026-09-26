# ADR 0018: O design system nasce de tokens no formato DTCG

**Status:** Aceito
**Data:** 2026-09-25

## Contexto

O dashboard terá um design system completo antes de qualquer tela ser desenhada. Assim cada tela usa peças já decididas, em vez de cada uma inventar as suas cores, espaçamentos e componentes.

Faltava decidir três coisas:
- **Onde o visual é definido,** e como ele chega ao CSS e aos gráficos sem ser copiado à mão em vários lugares.
- **Em que design system de referência se apoiar,** porque criar tudo do zero seria reinventar trabalho que empresas grandes já publicaram e testaram.
- **Que exigência de acessibilidade vale,** principalmente nas cores dos gráficos, que carregam significado.

A pesquisa de referências foi feita em 2026-09-25 e fica registrada no documento de referências de design (#58).

## Decisões

### 1. O visual é definido em tokens, no formato W3C DTCG

Cor, tipografia, espaçamento, raio, elevação e movimento são tokens num arquivo JSON, no formato do [Design Tokens Community Group](https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/), cuja primeira versão estável, 2025.10, saiu em 28/10/2025. É um padrão aberto, e não o formato de uma ferramenta.

Os tokens têm três camadas:

| Camada | Exemplo | Para que serve |
|---|---|---|
| Primitivo | `color.blue.60` | A paleta crua, sem significado |
| Semântico | `color.text.primary`, `color.risk.high` | O papel da cor na interface |
| Componente | `kpi.value.font-size` | O ajuste de uma peça específica |

Componente só usa token semântico, e semântico só usa primitivo. Trocar uma cor primitiva muda a interface inteira sem editar o CSS de nenhum componente.

### 2. O Style Dictionary gera o CSS

O [Style Dictionary](https://styledictionary.com/info/dtcg/), versão 5.5.5 no npm em 2026-09-26, lê o JSON e gera as variáveis CSS. O CSS gerado nunca é editado à mão, e o CI reprova quando ele diverge do JSON (#62). Os gráficos leem as mesmas variáveis pelo módulo de tema do ECharts (#63).

### 3. Tema claro por padrão, e o escuro derivado dos mesmos tokens

O executivo de crédito imprime, projeta em reunião e manda a tela em PDF. O claro é o padrão, e o escuro sai dos mesmos tokens semânticos, sem uma segunda paleta mantida à parte.

### 4. A estrutura segue o IBM Carbon, e os nomes seguem o Atlassian

- **[IBM Carbon](https://carbondesignsystem.com/data-visualization/color-palettes/):** ativo, e com o guia de visualização de dados mais completo entre os design systems públicos. Tem paletas categórica, monocromática e divergente com ordem definida, e status mostrado com forma e cor juntos.
- **[Atlassian Design System](https://atlassian.design/foundations/color/data-visualization-color):** tem a nomenclatura de tokens de gráfico mais clara, como `color.chart.categorical.1` a `8`, e o limite de cinco a seis cores por gráfico.

O Carbon MCP oficial serve de ferramenta de consulta durante o desenho. O acesso exige IBMid, e o token fica só na configuração local, nunca num arquivo do repositório ([ADR 0016](0016-site-estatico-no-github-pages-e-chat-no-zerogpu.md), decisão 5).

### 5. A acessibilidade exigida é a WCAG 2.2 AA

- **Contraste:** 4,5:1 para texto e 3:1 para elemento gráfico, conferidos por teste automatizado.
- **Daltonismo:** cada paleta de dados é simulada para deuteranopia, protanopia e tritanopia, e o resultado fica registrado no design system.
- **APCA** entra só como checagem extra. Ele ainda é método candidato e não faz parte do texto normativo da WCAG 3 ([situação em abril de 2026](http://adrianroselli.com/2026/04/wcag3-contrast-as-of-april-2026.html), acessado em 2026-09-25).

### 6. Cor de risco é separada da cor de categoria, e nunca aparece sozinha

A paleta de risco e a dos quatro quadrantes (entrar, observar, manter, não entrar) são tokens próprios, separados da paleta categórica das modalidades. Todo quadrante leva ícone e rótulo além da cor, para quem não distingue as cores e para quem imprime em preto e branco.

## Alternativas descartadas

**Tailwind ou Open Props como fonte do visual.** Trariam um sistema de tokens pronto, mas o projeto teria dois: o deles e o do design system.

**Material 3.** O guia de visualização de dados completo é do Material 2, que é legado. O Material 3 tem só um texto de blog sobre o assunto.

**Shopify Polaris Viz.** O repositório foi [arquivado em 06/06/2025](https://github.com/Shopify/polaris-viz).

**Tema escuro como padrão.** É tendência em produto de dados, mas atrapalha quem imprime ou projeta, que é o uso real do público.

**CSS escrito à mão, sem tokens.** Funciona no começo, e depois cada cor passa a existir em vários lugares, com pequenas diferenças entre eles.

## Consequências

**Positivas.**
- Uma mudança de visual acontece num lugar só, e vale para a interface e para os gráficos.
- O formato DTCG é aberto: qualquer ferramenta que siga o padrão lê os tokens, sem depender do Style Dictionary.
- O design system fica documentado com as referências de onde veio cada escolha.

**Negativas, e são reais.**
- **Um passo de build a mais:** o CSS precisa ser gerado antes de o site rodar.
- **O design system precisa estar pronto antes da primeira tela,** o que adia a primeira entrega visível.
- **O acesso ao Carbon MCP depende de aprovação da IBM** para quem não é funcionário. Enquanto isso, a consulta é feita pelo `llms.txt` público do Carbon.
