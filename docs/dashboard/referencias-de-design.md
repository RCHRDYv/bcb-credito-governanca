# Referências de design do dashboard

O que foi pesquisado antes de desenhar o dashboard, o que se aproveitou de cada referência e o que ficou de fora, com a fonte de cada afirmação. O resultado de tudo isso está no [design system](design-system.md) e no [ADR 0020](../adr/0020-design-system-carbon-com-camada-liquid-glass.md).

## Como a pesquisa foi feita

- **2026-09-25:** pesquisa de tendências de interface para produtos de dados e para IA sobre dados, de produtos de referência e de design systems públicos com guia de visualização de dados. A mesma rodada pesquisou stack e hospedagem, que viraram os ADRs [0016](../adr/0016-site-estatico-no-github-pages-e-chat-no-zerogpu.md) e [0017](../adr/0017-interface-em-javascript-sem-framework.md).
- **2026-09-26:**
  - busca de dashboards de vidro no Dribbble;
  - leitura do guia de glassmorphism da UX Pilot;
  - a demonstração pública da Mercury;
  - comparação de cinco design systems num [protótipo navegável](../../dashboard/prototipo-design-system/index.html), todos no mesmo formato.

Cada fonte tem link e data de acesso, no fim do documento. Análises de terceiros sobre um produto ficam marcadas como **fonte secundária**, porque não vêm do próprio produto.

## Tendências que se sustentam

| Tendência | O que é | O que virou no design system |
|---|---|---|
| Menos cor, hierarquia calma | A Linear deixou a interface mais neutra em mar/2026 [1]. A Mercury usa um acento só sobre neutros [2, fonte secundária] | Princípio "cor só onde há significado": neutros do Carbon, o azul para ação e as cores dos quadrantes só onde há decisão |
| Números tabulares | Algarismos de largura igual em tabelas e painéis, para alinharem em coluna [3] | Toda tabela, painel e rótulo com número usa algarismos tabulares |
| Conclusão escrita junto do dado | A The Economist trata o título do gráfico como a mensagem [4], e o Tableau Pulse resume cada métrica em linguagem natural [5] | Não foi aproveitada. Em 2026-09-26 ficou decidido, para controlar o escopo, que os gráficos não trazem conclusão escrita: o cabeçalho tem o título e a data-base com a fonte, e quem quiser uma conclusão pergunta ao chat |
| Notação padronizada para projeção | A notação IBCS diferencia realizado, plano e projeção. Um fabricante afirma que ela virou a norma ISO 24896 [6, fonte secundária, não conferida na ISO] | A série com projeção usa realizado sólido e projeção hachurada (#63) |
| IA sobre dados que mostra a conta | O botão para ver o SQL no Databricks Genie [7], o raciocínio visível no Hex [8], as respostas verificadas no Power BI [9] e a citação ligada a cada afirmação [10] | O chat mostra o número tirado do dado, a ressalva e o SQL, e se abstém quando o dado não permite responder ([ADR 0019](../adr/0019-chat-consulta-so-o-esquema-estrela.md)). O selo de resposta verificada foi descartado |
| Acessibilidade de verdade | WCAG 2.2 AA continua sendo a exigência. O APCA ainda é candidato e não está no texto normativo da WCAG 3 [11] | Contraste medido de cada cor, daltonismo validado e nenhum significado só por cor. APCA fica como checagem extra |
| Vidro com função | A Apple lançou o Liquid Glass em 2025 como material translúcido para controles e navegação, que flutuam sobre o conteúdo [12] | A camada Liquid Glass: vidro no que flutua, dado sobre vidro quase opaco |

## Modismos a evitar

| Modismo | Por que evitar | O que o design system faz |
|---|---|---|
| Vidro em toda superfície e gradiente decorativo | O guia de glassmorphism da UX Pilot desaconselha espalhar vidro pela tela inteira [13], e o gradiente saturado briga com as cores dos quadrantes | Vidro só no que flutua. O campo de luz é discreto e usa as próprias cores do Carbon |
| Chat em tela cheia como interface principal | O executivo quer a resposta pronta, e não uma conversa | O chat é opcional por visão, num trilho lateral ou num botão |
| Raciocínio da IA aparecendo enquanto é gerado | Distrai quem só quer o número | A resposta traz o número, a frase, a ressalva e o SQL recolhido |
| Tema escuro como padrão | Executivo imprime, projeta e manda PDF | O escuro não é o padrão: o site segue o sistema do visitante, abre claro quando o sistema não indica preferência e imprime sempre claro, com o escuro derivado dos mesmos tokens ([ADR 0018](../adr/0018-design-system-por-tokens-dtcg.md), revisto em 2026-09-27) |
| Animação decorativa | Não comunica nada e cansa | Movimento só para mudança de estado, e nenhum com movimento reduzido ligado |

## Referências de produto

| Referência | O que se aproveitou | O que não serve |
|---|---|---|
| The Economist, guia de gráficos [4] | Título que diz o que o gráfico mostra, rótulo direto na linha e uma cor de destaque | Nada relevante. O guia é de 2017, e a cópia consultada é hospedada por terceiros |
| Financial Times, Visual Vocabulary [14] | Escolher o gráfico pela relação que ele mostra: desvio, ranking ou espaço | Nada relevante |
| Our World in Data [15] | Fonte visível em cada gráfico e mapa com a mesma escala da linha | A quantidade de controles, demais para um executivo |
| Stripe Sigma [16] | IA que escreve o SQL ao lado da resposta, e formatação monetária cuidadosa | O foco em pagamentos |
| Databricks Genie [7, 17] | Mostrar o SQL e testar a IA com perguntas de resposta conhecida | O selo de resposta confiável, descartado no ADR 0019 |
| Hex [8] | SQL e raciocínio visíveis | O público, que é o analista |
| Power BI Copilot [9, 18] | A ideia de separar resposta verificada de resposta gerada | O selo, descartado no ADR 0019 |
| Tableau Pulse [5] | Nada, depois da decisão de 2026-09-26 | O resumo escrito por métrica: os gráficos não trazem conclusão escrita, e quem quiser uma conclusão pergunta ao chat |
| Mercury, demonstração pública [19] | Contenção de cor, número em destaque e cápsulas | Fontes proprietárias. As análises do visual são fontes secundárias [2] |
| Linear [1] | Hierarquia sóbria, tema gerado por poucos tokens | É ferramenta de uso diário, e o executivo abre o dashboard de vez em quando |
| Bloomberg Terminal [20] | Esquema alternativo de cor para quem tem daltonismo | A densidade de terminal. O material é de 2021 |
| Portais do BIS e do BCB [21, 22] | Metadados junto do dado e data-base explícita | O visual institucional datado |
| Busca no Dribbble [23] | A tendência mais vista: fundo claro com gradiente suave e cartões de vidro fosco | São conceitos, e não produtos em uso. O gradiente roxo saturado brigaria com os quadrantes |
| Julius AI [24] | Nada | Carregar planilha e perguntar, sem nenhuma governança do dado |
| ThoughtSpot Spotter [25] | Nada | O material é mais de marketing do que de padrão de interface |

## Design systems comparados

Em 2026-09-26, cinco candidatos foram montados no mesmo protótipo, com fundações, paletas de gráfico, componentes, padrões e modelos de página. A decisão e as alternativas estão no ADR 0020.

| Candidato | O que trouxe | Por que não foi o escolhido |
|---|---|---|
| Fluent 2, da Microsoft [26, 27] | O único com vidro oficial: Acrylic, Mica e Smoke | A paleta oficial de gráficos falha na validação de daltonismo, a fonte Segoe UI não pode ser embutida, e o visual lembra ferramenta de escritório |
| IBM Carbon com vidro só nas superfícies [28, 29] | O guia de gráficos, dashboards e acessibilidade mais completo | O vidro parecia enxertado, e os controles de cantos retos não ganhavam o visual atual |
| Liquid Glass, interpretado para a web [12, 30] | O visual de vidro mais atual | Não haveria nenhuma fundação oficial para citar, e a fonte SF não pode ser usada fora dos aparelhos Apple |
| Próprio, tirado do Dribbble [23] | O mais livre | Nada para citar, envelhece rápido, e três cores de gráfico ficavam abaixo de 3:1 |
| **Carbon com a camada Liquid Glass** | Fundações oficiais do Carbon e o vidro nos componentes | **Escolhido** |

Outros design systems estudados, que não viraram candidatos:
- **Atlassian:** a nomenclatura dos tokens de gráfico foi adotada no ADR 0018 [31].
- **Adobe Spectrum:** tem a paleta de gráfico revisada para daltonismo [32].
- **Salesforce SLDS 2:** tem guia de gráficos com tema seguro para daltonismo [33].
- **Government Analysis Function, do Reino Unido:** tem paletas acessíveis, com código [34].
- **Material 3:** o guia completo de visualização de dados é o do Material 2, que é legado [35].
- **Shopify Polaris Viz:** o repositório está arquivado desde 06/06/2025 [36].

## Glassmorphism: o que o guia ensinou e o que virou regra

O guia de glassmorphism da UX Pilot [13] foi a referência para as regras do vidro.

| O guia recomenda | O design system faz |
|---|---|
| Desfoque entre 10 e 30 px, conforme o fundo | Vidro claro com 10 px e vidro regular com 26 px |
| Painéis com 20% a 30% de opacidade | O vidro claro fica em 22%. O vidro regular sobe para 62%, de propósito, porque carrega dado e precisa manter o texto de ajuda acima de 4,5:1 |
| Contraste de 4,5:1 no texto e de 3:1 no texto grande | Contraste medido de cada cor sobre o fundo e sobre o vidro |
| Vidro só nas superfícies importantes | Vidro claro só no que flutua, e no máximo duas camadas empilhadas |
| Não animar elementos com desfoque | O desfoque nunca é animado |
| Estilo alternativo quando o navegador não suporta o efeito | Sem `backdrop-filter`, a superfície vira sólida. Na impressão, não há vidro |

## O que não serve para executivo de crédito

- **Densidade de terminal.** O executivo abre o dashboard de vez em quando e quer poucos números por visão, com a resposta clara.
- **Tema escuro como padrão.** Atrapalha na impressão, na projeção e no PDF.
- **Conversa com a IA como tela principal.** A decisão está nas visões, que funcionam sem o chat.
- **Cores saturadas e brilho neon.** Brigam com as cores que carregam significado, as dos quadrantes.
- **Números no formato americano.** O público é brasileiro: R$ 485,5 bi, 0,93%, jul/2026.
- **Data-base escondida.** O SCR.data é mensal e chega com defasagem, então a data-base de cada número precisa estar sempre visível [22].

## Fontes

Acessadas em 2026-09-25, na primeira pesquisa: 1 a 11, 14 a 18, 20 a 22, 24, 25, 28 e 31 a 36. Acessadas em 2026-09-26, na escolha do design system: 12, 13, 19, 23, 26, 27, 29 e 30.

1. Linear, "Behind the latest design refresh", 12/03/2026. https://linear.app/now/behind-the-latest-design-refresh
2. Análise do design da Mercury, fonte secundária. https://blakecrosley.com/guides/design/mercury
3. Vercel, fonte Geist. https://vercel.com/font
4. The Economist, guia de estilo de gráficos, 2017, cópia hospedada pelo IPAA. https://sa.ipaa.org.au/wp-content/uploads/2026/02/Economist-CHARTstyleguide_20170505.pdf
5. Tableau Pulse, tipos de insight. https://help.tableau.com/current/online/en-us/pulse_insights_platform_insight_types.htm
6. Zebra BI, sobre IBCS e ISO, fonte secundária. https://zebrabi.com/zbi_blog/ibcs-iso-standards/
7. Databricks, Genie trusted assets. https://docs.databricks.com/aws/en/genie/trusted-assets
8. Hex, "Introducing Threads", 01/10/2025. https://hex.tech/blog/introducing-threads/
9. Microsoft, respostas verificadas no Copilot do Power BI. https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-prepare-data-ai-verified-answers
10. Shape of AI, padrão de citações. https://www.shapeof.ai/patterns/citations
11. Adrian Roselli, contraste na WCAG 3, abril de 2026. http://adrianroselli.com/2026/04/wcag3-contrast-as-of-april-2026.html
12. Apple, "Apple introduces a delightful and elegant new software design", 09/06/2025. https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/
13. UX Pilot, guia de glassmorphism. https://uxpilot.ai/blogs/glassmorphism-ui
14. Financial Times, Visual Vocabulary. https://github.com/Financial-Times/chart-doctor/tree/main/visual-vocabulary
15. Our World in Data, redesenho das visualizações interativas. https://ourworldindata.org/redesigning-our-interactive-data-visualizations
16. Stripe Sigma. https://stripe.com/sigma
17. Databricks, notas de versão de 2026 do AI/BI. https://docs.databricks.com/aws/en/ai-bi/release-notes/2026
18. Microsoft, introdução ao Copilot no Power BI. https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-introduction
19. Mercury, demonstração pública. https://demo.mercury.com/dashboard
20. Bloomberg, cor acessível no terminal, 14/10/2021. https://www.bloomberg.com/ux/2021/10/14/designing-the-terminal-for-color-accessibility/
21. BIS, painéis de crédito total. https://data.bis.org/topics/TOTAL_CREDIT/tables-and-dashboards
22. Banco Central do Brasil, SCR.data. https://dadosabertos.bcb.gov.br/dataset/scr_data
23. Dribbble, busca "glassmorphism dashboard". https://dribbble.com/search/glassmorphism-dashboard
24. DataCamp, guia do Julius AI. https://www.datacamp.com/tutorial/julius-ai-guide
25. ThoughtSpot, lançamento do Spotter for Industries, 18/03/2026. https://www.globenewswire.com/news-release/2026/03/18/3258096/0/en/thoughtspot-launches-spotter-for-industries-purpose-built-agents-transform-complex-industry-context-into-trusted-actionable-insights.html
26. Microsoft, Fluent 2. https://fluent2.microsoft.design/
27. Microsoft, materiais do Fluent 2. https://fluent2.microsoft.design/material
28. IBM, paletas de visualização de dados do Carbon. https://carbondesignsystem.com/data-visualization/color-palettes/
29. IBM, Carbon Design System e o guia de dashboards. https://carbondesignsystem.com/data-visualization/dashboards/
30. Apple, materiais nas diretrizes de interface. https://developer.apple.com/design/human-interface-guidelines/materials
31. Atlassian, cor para visualização de dados. https://atlassian.design/foundations/color/data-visualization-color
32. Adobe Spectrum, cor para visualização de dados. https://spectrum.adobe.com/page/color-for-data-visualization/
33. Salesforce Lightning Design System, gráficos. https://www.lightningdesignsystem.com/2e1ef8501/p/7139a1-charts
34. Government Analysis Function, cores em gráficos. https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-colours-in-charts/
35. Material Design, acessibilidade em visualização de dados. https://m3.material.io/blog/data-visualization-accessibility
36. Shopify, Polaris Viz, repositório arquivado. https://github.com/Shopify/polaris-viz
