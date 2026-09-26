# ADR 0017: A interface é JavaScript sem framework, com Vite e ECharts

**Status:** Aceito
**Data:** 2026-09-25

## Contexto

O dashboard é um site estático ([ADR 0016](0016-site-estatico-no-github-pages-e-chat-no-zerogpu.md)) com poucas telas: onde está o crédito, onde o risco piora, a projeção e a recomendação, mais o chat. As telas precisam de mapa por UF, gráfico de dispersão com quadrantes, série temporal, ranking e cards de indicador.

Três exigências pesaram na escolha:
- **Quem mantém é um analista de dados, e não um desenvolvedor front-end.** Cada ferramenta a mais é mais uma coisa para aprender e atualizar.
- **O código precisa ser modular, conciso e documentado dentro do próprio arquivo.**
- **A interface precisa estar no nível das melhores de hoje:** responsiva, acessível, com tema claro e escuro.

A pesquisa de bibliotecas foi feita em 2026-09-25, e as versões abaixo foram conferidas no npm em 2026-09-26.

## Decisões

### 1. JavaScript com ES modules, empacotado pelo Vite, sem framework

Cada tela é um módulo com uma função `render(el, dados)`. Os filtros de UF, modalidade e mês ficam num objeto simples, e as telas escutam as mudanças por um `EventTarget`. O Vite serve o ambiente de desenvolvimento, gera os arquivos com hash e remove o código que não é usado.

Não existe reatividade automática, compilador próprio nem ciclo de vida de componente para aprender. É a própria plataforma web, que não muda de paradigma a cada versão.

### 2. ECharts para todos os gráficos, importado por partes

Uma biblioteca só cobre as telas: mapa por UF com GeoJSON, dispersão com as áreas dos quadrantes, série temporal, e acessibilidade com descrição automática e padrões de preenchimento para quem não distingue cores. O import é por partes (`echarts/core` mais os gráficos usados e o renderizador SVG), para o site não carregar a biblioteca inteira.

A malha das UFs vem da API de malhas do IBGE, é simplificada uma vez e versionada no repositório (#67). O site nunca busca a malha em tempo de execução.

### 3. CSS moderno, sem framework

Camadas de cascata (`@layer`), container queries, cores em OKLCH e `light-dark()` para os dois temas. As variáveis vêm dos tokens do design system ([ADR 0018](0018-design-system-por-tokens-dtcg.md)). Menus e diálogos usam `<dialog>` e `popover` nativos.

### 4. O chat usa bibliotecas pequenas e com segurança explícita

- O texto do modelo passa pelo marked e depois pelo DOMPurify antes de entrar na página. Texto de modelo nunca entra no HTML sem sanitização.
- O SQL da resposta é destacado pelo highlight.js, registrando só a linguagem SQL.
- A chamada ao Space do chat usa o `@gradio/client`.

### 5. Qualidade verificada no CI

| Ferramenta | Papel |
|---|---|
| Biome | Lint e formatação, com um arquivo de configuração só |
| Vitest | Testes unitários: formatação de número, regras de tela, montagem do tema |
| Playwright com axe | Testes de ponta a ponta e de acessibilidade, nos dois temas |
| `tsc` com `checkJs` | Checagem de tipos a partir do JSDoc, sem escrever TypeScript |

### 6. O código é a documentação

Todo módulo tem JSDoc e comentários em português e em inglês, porque o repositório é público e lido por empresas brasileiras e de fora. Os textos da interface ficam num arquivo de tradução em português, para o inglês entrar depois sem mexer nos componentes.

### Versões conferidas no npm em 2026-09-26

| Pacote | Versão |
|---|---|
| `vite` | 8.3.1 |
| `echarts` | 6.1.0 |
| `marked` | 18.0.14 |
| `dompurify` | 3.4.16 |
| `highlight.js` | 11.12.0 |
| `@gradio/client` | 2.7.0 |
| `@biomejs/biome` | 2.5.14 |
| `vitest` | 5.0.2 |
| `@playwright/test` | 1.63.0 |
| `@axe-core/playwright` | 4.13.0 |
| `typescript` | 7.0.2 |

As versões ficam fixadas no lockfile, e a atualização é feita de propósito, não por acidente.

## Alternativas descartadas

**Svelte, Astro, Lit ou Preact.** Resolvem a reatividade com menos código de ligação, mas cada um traz sintaxe ou compilador próprios, e o Svelte 5 já mudou de paradigma uma vez. O Preact pede o modelo mental do React. Para poucas telas, o ganho não paga o custo de aprender e manter.

**Observable Framework.** A ideia de gerar o site com os dados já carregados é muito boa para este caso, mas a última versão com funcionalidade nova foi a 1.13.0, de novembro de 2024. A mais recente, 1.13.4, só atualiza dependências ([releases](https://github.com/observablehq/framework/releases), acessado em 2026-09-25). Não há anúncio oficial de descontinuação, mas o foco da empresa passou para outro produto, e apostar nele hoje é arriscado.

**Evidence.** Em 26/08/2026 virou o [Evidence Core](https://evidence.dev/blog/evidence-core), com consultas ao vivo contra o banco e um servidor, o que contraria o site estático. A versão antiga, estática, só recebe correção de segurança.

**Observable Plot.** O visual mais elegante e o que melhor herda o CSS, mas continua na versão 0.6.17 e tem menos interação que o ECharts. Fica como plano B.

**D3, Vega-Lite, Chart.js e uPlot.** O D3 dá trabalho demais para manter. O Vega-Lite tem configuração verbosa e tema pior. Chart.js e uPlot não fazem mapa.

**Highcharts.** Exige licença paga.

**Tailwind.** É produtivo, mas cria um segundo sistema de tokens ao lado do design system e enche o HTML de classes.

**DuckDB-WASM no navegador.** Tem 33,5 MB, e é desnecessário com o SQL do chat rodando no Space (ADR 0016). No npm, a versão marcada como mais recente ainda é de desenvolvimento (`1.33.1-dev57.0`).

## Consequências

**Positivas.**
- Poucas dependências de execução: ECharts, o par marked e DOMPurify, highlight.js e o cliente do Gradio.
- O código continua legível para quem conhece JavaScript, sem precisar conhecer um framework.
- Lint, tipos, testes e acessibilidade são conferidos no CI desde o esqueleto (#65).

**Negativas, e são reais.**
- **Sem framework, a ligação entre filtro e tela é escrita à mão.** Com poucas telas é aceitável; se o dashboard crescer muito, o Astro é a primeira alternativa a reavaliar.
- **O tema do ECharts passa por JavaScript,** porque a biblioteca não lê variáveis CSS sozinha. Isso fica isolado num módulo só (#63).
- **O tamanho do ECharts importado por partes ainda não foi medido.** A medida sai do build da #65 e é comparada com o orçamento dos requisitos (#58).
- **O TypeScript atual, 7.0.2, é a versão reescrita em Go.** A #65 confere se a checagem de JSDoc com `checkJs` funciona nele como na versão anterior, antes de adotar.
