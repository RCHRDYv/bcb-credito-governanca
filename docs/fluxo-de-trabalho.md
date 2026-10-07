# Fluxo de trabalho com o Claude Code

PT: O passo a passo para tocar uma issue deste projeto com o Claude Code, da sessão nova até o merge. O processo de ponta a ponta, com os erros da IA e como foram pegos, está em [Desenvolvimento com IA](desenvolvimento-com-ia.md).

EN: Step by step for working an issue in this project with Claude Code, from a new session to the merge.

## Resumo

1. Uma sessão nova por issue, aberta na pasta do projeto.
2. `/iniciar-issue <n>`: leitura da issue, entrevista sobre as decisões e plano.
3. A execução e a sua revisão.
4. `/entregar-issue <n>`: commit, PR e os textos de review e merge.
5. Merge no GitHub e fim da sessão.

## 1. Abrir a sessão

1. Na aba Code do app, clique em **Novo**.
2. Clique no botão de pasta e escolha a pasta do projeto, `bcb-credito-governanca`.
   - Deve sobrar **um botão só** de pasta, sem ×.
   - O botão com "+" adiciona uma pasta extra, e o `CLAUDE.md` dela não é carregado.
3. Confira se a branch é **main** e deixe **worktree** desmarcado.
4. Ajuste o modelo e o modo:

| Tipo de issue | Modelo | Esforço | Modo |
|---|---|---|---|
| Decisão de método, arquitetura, dado novo | Opus | Alto | Plano |
| Tela ou componente do dashboard | Opus | Alto | Plano |
| Ajuste mecânico (CI, docs, final de linha, texto) | Sonnet | Médio | Automático |

## 2. Começar a issue

```
/iniciar-issue <n>
```

A skill confere o que carregou e a branch, lê a issue, acha uma entrega parecida para servir de padrão, te entrevista sobre as decisões e escreve o plano.

Quando você já sabe restrições ou o padrão a seguir, diga logo na mesma mensagem. Restrição que só aparece na rejeição do plano custa uma rodada inteira.

```
/iniciar-issue <n>
Siga o padrão de <issue, arquivo ou ADR>.
Restrições: <escopo, janela, o que não fazer>.
Pronto quando: <comando, teste ou número que prova>.
```

Exemplo real, a #47:

```
/iniciar-issue 47
Siga o padrão de proteção dos enunciados em scripts/validar_perguntas.py e as regras dos ADRs 0012, 0013 e 0015.
Restrições: PR própria, só com o registro. Nada de executar o experimento. Não mexa em enunciado nem em resposta do gabarito.
Pronto quando: o validador reprova uma cópia alterada das hipóteses e do gabarito, todos os validadores passam e o CI fica verde.
```

## 3. Durante a execução

- **Entrevista:** responda às perguntas. A opção recomendada vem primeiro, com o motivo, e a decisão é sua.
- **Plano:** leia antes de aprovar. Se algo estiver errado, rejeite e diga o que mudar.
- **Entrega visual:** só aprove depois de ver renderizado nos dois temas.

## 4. Revisar antes de aprovar

```
Roda o /code-review no diff e reporte só o que afeta correção ou o escopo da issue.
```

Confira também o resumo final da sessão: arquivos, comandos que passaram e pontos em aberto. Ponto em aberto se resolve antes de aprovar.

## 5. Entregar

```
/entregar-issue <n>
```

A skill faz o commit, o push e a PR, liga a correção automática do CI e te manda os textos de review e de merge. Ela só roda quando você digita.

No GitHub:
1. Cole o texto de review.
2. Espere o CI ficar verde.
3. Faça o merge com o texto de merge commit.
4. Encerre a sessão.

## Frases úteis

| Situação | O que escrever |
|---|---|
| Conferir se a sessão carregou as instruções | `Quais instruções e memórias você carregou nesta sessão?` |
| Pergunta lateral, sem desviar a tarefa | `/btw <pergunta>` |
| Correção que deve valer sempre | `Isso vale sempre: põe no CLAUDE.md do projeto.` |
| O Claude errou duas vezes no mesmo ponto | `/clear` e o pedido de novo, já com o que você aprendeu |
| Sessão longa, ainda na mesma issue | `/compact preserve as decisões da #<n> e o que falta` |
| Ver o que pesa no contexto | `/context` |
| Revisão independente do diff | `/code-review` |
| Ver os atritos que se repetem nas sessões | `/insights` |

## Por que assim

- **Uma sessão por issue:** cada mensagem reenvia todo o histórico da sessão. Uma sessão curta gasta menos e erra menos.
- **O que vale sempre fica escrito:**
  - as regras fixas no `CLAUDE.md`;
  - os fluxos repetidos em skills, que só carregam quando chamadas;
  - as decisões em ADRs e nos comentários das issues.
- **Commit e PR só por ordem sua:** a `entregar-issue` não dispara sozinha.

Referências: [boas práticas do Claude Code](https://code.claude.com/docs/en/best-practices) e [custos e contexto](https://code.claude.com/docs/en/costs).
