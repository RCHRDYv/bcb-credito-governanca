---
name: iniciar-issue
description: Começa uma issue do bcb-credito-governanca numa sessão nova, da leitura da issue até a entrevista sobre as decisões e o plano. Use quando o Yuri abrir uma sessão para uma issue e chamar /iniciar-issue com o número.
disable-model-invocation: true
---

# Iniciar a issue $ARGUMENTS

O guia completo do fluxo está em `docs/fluxo-de-trabalho.md`. Esta skill cobre do começo até o plano aprovado. O fechamento fica com `/entregar-issue`.

## 1. Conferir a sessão
- Diga quais instruções e memórias carregou: o `~/.claude/CLAUDE.md`, o `CLAUDE.md` do projeto e a memória do projeto. Se faltar algum, avise antes de seguir, porque a pasta da sessão pode estar errada.
- `git status` e `git branch --show-current`. A branch tem que ser a `main`, limpa e atualizada (`git pull`). Se não for, pare e pergunte.
- Se o modo não for Plano e a issue tiver decisão de método ou de desenho, sugira trocar antes de seguir.

## 2. Ler a issue e o contexto
- `gh issue view $ARGUMENTS --comments`: contexto, o que fazer, pronto quando, dependências.
- Confira na memória do projeto se a issue é mesmo a próxima da cadeia. Se não for, diga qual seria e pergunte.
- Ache uma entrega parecida que já existe (issue fechada, ADR, script) para servir de padrão. Prefira um subagente de exploração para não encher o contexto.
- Leia só os ADRs e arquivos que a issue cita ou que o padrão usa.

## 3. Entrevistar o Yuri antes do plano
- Liste as decisões que são dele: método, escopo, desenho, nomes públicos, tudo que mude o resultado ou fique público.
- Pergunte com AskUserQuestion, em rodadas de até quatro perguntas. Cada pergunta traz opções concretas, com a recomendada primeiro e o motivo.
- Não pergunte o que o código, os ADRs ou as convenções já respondem.
- Registre as decisões, com a data, num comentário da issue antes do código.

## 4. Plano
- Escreva o plano com:
  - contexto;
  - decisões tomadas;
  - arquivos a criar e a mudar;
  - o que se reaproveita;
  - verificação ponta a ponta;
  - fora do escopo.
- O "pronto quando" do plano só traz o que se verifica no repositório ou no CI.
- Peça a aprovação do plano.
- Depois da aprovação, crie a branch (`feat/`, `ci/` ou `chore/` mais o número e um nome curto) e execute.

## 5. Ao terminar a execução
- Mostre a evidência: comandos que passaram, números e arquivos novos e alterados.
- Liste os pontos em aberto, um por linha.
- Diga que o próximo passo é o Yuri revisar e digitar `/entregar-issue $ARGUMENTS`. Não faça commit.
