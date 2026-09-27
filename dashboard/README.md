# Site do dashboard

Site estático do dashboard de crédito PJ, publicado no GitHub Pages. É JavaScript sem framework, com Vite ([ADR 0017](../docs/adr/0017-interface-em-javascript-sem-framework.md)). Por enquanto é o esqueleto da #65: uma página inicial vazia, com lint, tipos, testes e medidas de desempenho funcionando antes da primeira visão.

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

O segundo comando abre o site em modo de desenvolvimento, com recarga automática.

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
| `build` | Gera o site estático em `dist/` | |
| `preview` | Serve o `dist/` na porta 4173 | |
| `lint` | Lint e formatação pelo Biome | ADR 0017 |
| `format` | Corrige a formatação | |
| `typecheck` | Checa os tipos pelo JSDoc, com o TypeScript, sem gerar arquivo | ADR 0017 |
| `test` | Testes unitários, com o Vitest | |
| `test:e2e` | Testes de ponta a ponta com axe, no Chromium, no Firefox e no WebKit | RNF-04, RNF-05 e RNF-06 |
| `budget` | Orçamento de carga do `dist/`, comprimido com gzip | RNF-03 |
| `lighthouse` | Lighthouse no celular e no computador, contra as metas | RNF-01 e RNF-02 |
| `check` | Todos acima, na ordem do CI | |

Os scripts `budget`, `test:e2e` e `lighthouse` rodam sobre o site construído, e não sobre o modo de desenvolvimento, porque é o build que vai para o Pages.

**No Windows,** alguns navegadores que o Playwright baixa não são assinados digitalmente, e o Windows pode bloquear programa sem assinatura. Na máquina em que o esqueleto foi feito, o Firefox foi bloqueado. Nesse caso, rode os testes de ponta a ponta só nos outros dois motores, e o CI, em Linux, confere os três:

```bash
npx playwright test --project=chromium --project=webkit
```

O Lighthouse usa o Google Chrome instalado quando existe, pelo mesmo motivo.

## Estrutura

| Pasta ou arquivo | O que guarda |
|---|---|
| `index.html` | A página única, sem script nem estilo embutido |
| `src/main.js` | O ponto de entrada |
| `src/textos/` | Os textos da interface, em pt-BR, e a função `t()` |
| `public/` | Arquivos servidos como estão |
| `tests/unit/` | Testes unitários |
| `tests/e2e/` | Testes de ponta a ponta |
| `scripts/` | O orçamento de carga e o Lighthouse |
| `prototipo-design-system/` | O protótipo aprovado no ADR 0020, fora do build |

A estrutura completa, com o que cada issue acrescenta, está na [arquitetura](../docs/dashboard/arquitetura.md#estrutura-de-pastas).
