---
name: entregar-issue
description: Fecha uma issue do bcb-credito-governanca, da verificação final até a PR, com os textos de review e de merge em primeira pessoa. Use quando o Yuri aprovar a entrega e pedir commit, push e PR.
disable-model-invocation: true
---

# Entregar a issue $ARGUMENTS

Só comece depois da aprovação explícita do Yuri. Em entrega visual, a aprovação é da tela renderizada.

Antes da aprovação vem o `/code-review` no diff da branch (`docs/fluxo-de-trabalho.md`, passo 4). Se ele não rodou nesta sessão, ou se um achado que afeta correção ou o escopo da issue ficou sem resposta, pare e diga isso ao Yuri antes do commit.

## 1. Conferir antes do commit
- `git status` e `git diff --stat`. Confira que nada fora do escopo da issue entrou: capturas, páginas de revisão, `data/`.
- Rode os validadores do CI listados no `CLAUDE.md`. Se a entrega mexe em dados, rode também o `dbt build` da seleção afetada e o QA de `scripts/analises/` correspondente.
- Se mexe no dashboard, rode em `dashboard/`: `npm run lint`, `typecheck`, `test`, `build` e `budget`, e o `test:e2e` no Chromium e no WebKit.
- Mostre ao Yuri a evidência (saída dos comandos), sem afirmar que passou sem mostrar.

## 2. Commit
- Mensagem: título curto do que a entrega é, corpo com o que mudou e por quê, `Closes #n` e a linha de coautoria.
- Se o hook `mixed-line-ending` reprovar, rode `git add` de novo e repita o commit.

## 3. Push e PR
- `git push -u origin <branch>` e `gh pr create --base main` com:
  - **O que muda:** em primeira pessoa;
  - **Como conferi:** os comandos e os números;
  - `Closes #n`.
- Ligue a correção automática do CI pela ferramenta do app (`ccd_pr`). Não faça polling de CI.

## 4. Textos para o Yuri colar
Mande dois textos em primeira pessoa, no tom dele, sem travessão e sem falar dele na terceira pessoa:
- **Comentário de review:** o que revisei, como conferi e o que a entrega destrava.
- **Merge commit:** título com `(#PR)` e corpo curto com `Closes #n`.

## 5. Depois
- Atualize a memória do projeto com o estado da cadeia de issues.
- Diga qual é a próxima etapa sugerida. Não comece sem o Yuri pedir.
