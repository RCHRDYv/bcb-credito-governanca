# ADR 0020: O design system oficial é o Carbon com uma camada Liquid Glass

**Status:** Aceito
**Data:** 2026-09-26

## Contexto

O [ADR 0018](0018-design-system-por-tokens-dtcg.md) decidiu como o design system é construído: tokens no formato W3C DTCG, gerados para CSS pelo Style Dictionary, com tema claro por padrão, WCAG 2.2 AA e a estrutura do IBM Carbon como referência. Faltava decidir qual design system, de fato, a interface segue.

Em 2026-09-26 surgiram dois requisitos que puxam em direções diferentes:

- **Documentação completa,** que dê para citar e defender numa entrevista: cada cor, tamanho e regra com uma fonte oficial por trás.
- **Uma interface bonita e atual,** alinhada com os melhores dashboards de hoje, com vidro (glassmorphism), compromisso visual registrado em `dashboard/PRODUCT.md`.

Nenhuma base pública entrega as duas coisas sozinha. O Carbon tem o guia de dados e de dashboards mais completo, mas foi desenhado para superfícies sólidas e cantos retos. O Liquid Glass, lançado pela Apple em 2025, é o vidro mais atual, mas a Apple publica só diretrizes, sem tokens nem componentes para a web.

Para decidir, os candidatos foram montados lado a lado num protótipo de design system, em [`dashboard/prototipo-design-system/`](../../dashboard/prototipo-design-system/index.html), todos no mesmo formato: fundações, paletas de gráfico, componentes com estados, padrões de uso e modelos de página.

## Decisões

### 1. As fundações são o Carbon oficial

Cor (tema g10), paletas de gráfico, tipografia IBM Plex com a escala produtiva, espaçamento e o grid 2x vêm do Carbon sem alteração. Os valores foram conferidos em 2026-09-26 no código publicado dos pacotes `@carbon/themes` 11.82.0, `@carbon/colors` 11.59.0, `@carbon/type` 11.68.0, `@carbon/layout` 11.60.0 e `@carbon/grid` 11.63.0.

Essa conferência corrigiu dois erros do primeiro protótipo:
- o grid do Carbon tem 16 colunas a partir de 1056 px, e não 12;
- os títulos grandes (42 e 54 px) usam peso 300.

### 2. Material, forma, movimento e componentes são uma camada Liquid Glass, documentada por nós

A camada cobre:
- os materiais de vidro: vidro claro, vidro regular e escurecimento;
- os raios de 8, 12, 20 e 28 px, mais a cápsula;
- a elevação em dois níveis, com brilho na borda;
- o movimento de mola, em 200, 350 e 500 ms;
- os componentes: controles, dados e avisos, chat e estados;
- os padrões de uso.

São interpretação nossa das diretrizes da Apple, e a documentação deles é o [guia do design system](../dashboard/design-system.md).

### 3. O vidro flutua, e o dado fica firme

O vidro claro vai no que flutua sobre o conteúdo: navegação, filtros e o botão do chat. Tabelas, dicas e painéis usam vidro regular, quase opaco. Com isso, o texto de ajuda do Carbon (#6f6f6f) mantém 4,86:1 de contraste sobre o vidro, acima do 4,5:1 da WCAG. O desfoque nunca é animado, e sem suporte a `backdrop-filter` a superfície vira sólida.

### 4. Os componentes são nossos

A interface não usa os componentes web do Carbon. Os componentes são construídos em JavaScript sem framework ([ADR 0017](0017-interface-em-javascript-sem-framework.md)), com os tokens do Carbon e a camada nova. A consequência é assumida: para as fundações, a referência é a documentação oficial do Carbon; para os componentes, é o nosso guia.

### 5. Os modelos de página usam o grid do Carbon e cobrem variações

São seis modelos genéricos, e cada visão do dashboard escolhe o seu pela pergunta que responde. O chat é opcional por visão. Se as visões terão um bloco de título-conclusão e apoio ainda está em aberto: os modelos reservam o lugar dele, sem torná-lo regra.

### O que continua valendo do ADR 0018

Tokens em DTCG com três camadas, geração pelo Style Dictionary, tema claro por padrão com o escuro derivado, WCAG 2.2 AA, paleta de risco separada da categórica e quadrantes sempre com ícone e rótulo.

## Alternativas descartadas

Todas as quatro foram montadas no mesmo protótipo e comparadas no mesmo formato.

**Fluent 2, da Microsoft.** É o único com vidro oficial (Acrylic, Mica e Smoke). Foi descartado por três motivos:
- a paleta oficial de gráficos falha na validação de daltonismo;
- a fonte Segoe UI não pode ser embutida, então a tela muda fora do Windows;
- o visual lembra ferramenta de escritório.

**Carbon com vidro só nas superfícies.** Mantinha os componentes do Carbon, com cantos retos, e punha vidro só nos cartões. O vidro ficava parecendo um enxerto, e os controles não ganhavam o visual atual.

**Liquid Glass puro, interpretado para a web.** Tem o visual mais atual. Foi descartado por três motivos:
- não teria nenhuma fundação oficial para citar;
- corre o risco de parecer imitação de produto Apple;
- a fonte SF não pode ser usada fora dos aparelhos Apple.

**Design system próprio, tirado do Dribbble.** O mais livre dos quatro. Foi descartado porque não tem nada para citar, tende a envelhecer rápido, e três cores da paleta de gráfico ficavam abaixo de 3:1.

## Consequências

**Positivas.**
- Cor, tipo, espaço e grid têm fonte oficial, conferida no código do Carbon.
- O visual atual aparece onde o usuário mais sente: controles, chat, painéis e movimento.
- A camada nova é pequena, e toda ela fica documentada num guia só.

**Negativas, e são reais.**
- **Documentação própria:** a dos componentes deixa de ser a do Carbon e passa a ser mantida por nós.
- **Carbon AI Chat:** não pode ser usado como vem, porque o chat segue a nossa camada.
- **Custo do vidro:** o `backdrop-filter` pesa em aparelhos fracos e não imprime. O guia define a superfície sólida como alternativa, e a impressão sem vidro.
- **Duas linguagens juntas:** IBM Plex com formas arredondadas pede cuidado para não parecer duas linguagens coladas.
- **Paleta categórica:** a oficial do Carbon falha na validação, porque um tom quase preto sai da faixa de luminosidade e um verde-escuro tem pouca saturação. O ajuste é decidido na #63.
- **Valores interpretados:** transparências, desfoque e curvas de mola da camada Liquid Glass são interpretação nossa, e precisam ser conferidos em Safari e Firefox na implementação (#62 a #64).
