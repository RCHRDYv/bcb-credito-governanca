# Site do dashboard

Site estático do dashboard de crédito PJ, publicado no GitHub Pages. É JavaScript sem framework, com Vite ([ADR 0017](../docs/adr/0017-interface-em-javascript-sem-framework.md)). Por enquanto tem o esqueleto da #65, com lint, tipos, testes e medidas de desempenho funcionando antes da primeira visão, os tokens do design system da #62, com os dois temas e o catálogo das fundações, os gráficos da #63 (o tema do ECharts, as paletas validadas e os componentes de gráfico), os componentes de interface da #64, todos no catálogo, os dados das visões, exportados dos marts na #66, e a malha das UFs da #67, que o mapa usa.

Para entender o projeto antes do código:
- [arquitetura](../docs/dashboard/arquitetura.md): como o site, o dataset e o chat se ligam;
- [requisitos](../docs/dashboard/requisitos.md): o que o dashboard precisa fazer e como se confere;
- [design system](../docs/dashboard/design-system.md): como a interface se parece;
- [contrato dos dados](contrato-dos-dados.yml): o que cada arquivo que o site lê traz.

## Como rodar

Precisa do Node 24, a versão do [`.nvmrc`](.nvmrc).

```bash
npm ci
```

```bash
npm run dev
```

O segundo comando abre o site em modo de desenvolvimento, com recarga automática. O catálogo do design system fica em `/catalogo.html`.

Para rodar tudo o que o CI confere, na mesma ordem:

```bash
npm run check
```

Na primeira vez, os testes de ponta a ponta pedem os navegadores do Playwright:

```bash
npx playwright install chromium firefox webkit
```

## Scripts

| Script | O que faz | Requisito |
|---|---|---|
| `dev` | Site em modo de desenvolvimento | |
| `tokens` | Gera o `tokens.css` e o `tokens.json` a partir de `tokens/` | ADR 0018 |
| `tokens:check` | Falha se o CSS gerado estiver diferente dos tokens | ADR 0018 |
| `build` | Gera o site estático em `dist/` | |
| `preview` | Serve o `dist/` na porta 4173 | |
| `lint` | Lint e formatação pelo Biome | ADR 0017 |
| `format` | Corrige a formatação | |
| `typecheck` | Checa os tipos pelo JSDoc, com o TypeScript, sem gerar arquivo | ADR 0017 |
| `test` | Testes unitários, com o Vitest | |
| `test:e2e` | Testes de ponta a ponta com axe, no Chromium, no Firefox e no WebKit | RNF-04, RNF-05 e RNF-06 |
| `budget` | Orçamento de carga do `dist/`, comprimido com gzip, com os dados somados por visão | RNF-03 |
| `lighthouse` | Lighthouse no celular e no computador, contra as metas | RNF-01 e RNF-02 |
| `check` | Todos acima, na ordem do CI | |

Os scripts `budget`, `test:e2e` e `lighthouse` rodam sobre o site construído, e não sobre o modo de desenvolvimento, porque é o build que vai para o Pages.

**No Windows,** alguns navegadores que o Playwright baixa não são assinados digitalmente, e o Windows pode bloquear programa sem assinatura. Na máquina em que o esqueleto foi feito, o Firefox foi bloqueado. Nesse caso, rode os testes de ponta a ponta só nos outros dois motores, e o CI, em Linux, confere os três:

```bash
npx playwright test --project=chromium --project=webkit
```

O Lighthouse usa o Google Chrome instalado quando existe, pelo mesmo motivo.

## Dados

Os JSON de `public/data/` saem dos marts de apresentação, pela exportação da #66, e o [contrato](contrato-dos-dados.yml) diz o que cada um traz. Eles são gerados, e nunca editados à mão. Por isso ficam fora do Biome: quem confere o formato é a validação, contra o contrato.

A exportação roda na raiz do repositório, na máquina com acesso ao Databricks, pelo login OAuth do perfil do CLI:

```bash
uv run python -m scripts.exportar_dados_do_dashboard
```

A validação é a mesma que o CI roda, sem credencial:

```bash
uv run python -m scripts.validar_dados_do_dashboard
```

Quando só a ontologia muda, o `ontologia.json` e o `manifesto.json` se refazem sem o Databricks, a partir dos arquivos já exportados:

```bash
uv run python -m scripts.exportar_dados_do_dashboard --sem-databricks
```

### Malha das UFs

O `public/geo/ufs.json` é a malha territorial de 2022 do IBGE, na qualidade mínima, com a geometria sem alteração, a sigla de cada UF e a fonte e a licença no topo. Também é gerado, e nunca editado à mão, e por isso fica fora do Biome, como os dados. Só precisa ser refeito quando o IBGE publicar outra malha, e as duas etapas rodam na raiz do repositório, sem credencial:

```bash
uv run python -m ingestion.baixar_malha
```

```bash
uv run python -m scripts.gerar_malha_do_dashboard
```

A primeira baixa a malha e registra o sha256 no manifesto da ingestão. A segunda grava o arquivo do site e confere que a geometria saiu igual à baixada. A validação dos dados, a mesma do CI, confere também a malha. O porquê de não simplificar está na [arquitetura](../docs/dashboard/arquitetura.md#malha-das-ufs).

## Estrutura

| Pasta ou arquivo | O que guarda |
|---|---|
| `index.html` | A página inicial, sem script nem estilo embutido |
| `catalogo.html` | O catálogo do design system, com as fundações, as paletas e os gráficos nos dois temas |
| `tokens/` | Os tokens no formato DTCG, em três camadas: `primitivos/`, `semanticos/` e `componentes/` |
| `src/main.js` | O ponto de entrada |
| `src/textos/` | Os textos da interface, em pt-BR, e a função `t()` |
| `src/estilos/` | O CSS: fontes, base e o `tokens.css` gerado, que nunca é editado à mão |
| `src/catalogo/` | As seções do catálogo, e o `exemplos.json` com os dados reais dos gráficos, gerado por `scripts/gerar_exemplos_do_catalogo.py`, na raiz do repositório |
| `src/cor/` | O contraste pela WCAG, o OKLab, a simulação de daltonismo e a validação das paletas (ADR 0021) |
| `src/componentes/` | Os componentes de interface, um por módulo, com os ícones do Tabler e o controle de tema |
| `src/graficos/` | O ECharts importado por partes, o tema montado dos tokens e os componentes de gráfico |
| `src/dados/` | O carregador dos arquivos do contrato, que busca cada arquivo uma vez só e transforma a falha no motivo que a visão mostra |
| `src/formatos.js` | Números e datas no padrão brasileiro |
| `src/tokens.js` | A lista de tokens gerada, com tipo, para o JavaScript |
| `src/dom.js` | Monta HTML sem `innerHTML` |
| `public/` | Arquivos servidos como estão, como o `tema-inicial.js`, que aplica o tema escolhido antes da pintura |
| `public/data/` | Os JSON do contrato, exportados dos marts, com o `ontologia.json` e o `manifesto.json` |
| `public/geo/` | A malha das UFs do IBGE, que o mapa por UF desenha |
| `tests/unit/` | Testes unitários |
| `tests/e2e/` | Testes de ponta a ponta |
| `scripts/` | O gerador dos tokens, o orçamento de carga e o Lighthouse |
| `prototipo-design-system/` | O protótipo aprovado no ADR 0020, fora do build |

A estrutura completa, com o que cada issue acrescenta, está na [arquitetura](../docs/dashboard/arquitetura.md#estrutura-de-pastas).

Dois arquivos de configuração valem saber:
- **`.npmrc`** desliga os scripts de instalação dos pacotes. Os pacotes do IBM Plex tentam rodar telemetria da IBM na instalação, e nenhum pacote do site precisa de script.
- **`.gitattributes`** fixa o fim de linha em LF nesta pasta, também no Windows, para o Biome e o Git concordarem.
