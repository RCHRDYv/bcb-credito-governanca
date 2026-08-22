# ADR 0001: Credenciais e dado bruto ficam fora do repositório

**Status:** Aceito
**Data:** 2026-08-20

## Contexto

Este é um repositório público, e repositório público tem duas propriedades que mudam o cálculo de risco: qualquer pessoa lê, e **o histórico do git é permanente**. Apagar um segredo do arquivo não o remove do histórico. Corrigir de verdade exige reescrever o histórico e rotacionar a credencial exposta.

O projeto conecta a um workspace Databricks e consome arquivos de dado com cerca de 97 MB cada, o que cria dois vetores distintos de problema: vazamento de credencial e inchaço permanente do repositório.

## Decisão

**1. Nenhuma credencial em arquivo versionado.**

A autenticação no Databricks usa OAuth via `databricks auth login`, então **nenhum token é gerado nem escrito em disco pelo usuário**. O `profiles.yml` real do dbt vive em `~/.dbt/`, fora do repositório, e contém apenas host e HTTP path, que são identificadores e não segredos. O repositório publica somente `profiles.yml.example`, com placeholders.

**2. Nenhum dado bruto versionado.**

O pipeline baixa os arquivos da fonte oficial do Banco Central a cada execução. A única exceção é `dbt/seeds/`, que contém tabelas de referência pequenas geradas a partir da ontologia e que precisam ser versionadas para o modelo ser reprodutível.

**3. Três camadas de defesa, não uma.**

Confiar só no `.gitignore` é frágil, porque ele é contornável por engano (`git add -f`) e depende de configuração local que um clone pode alterar.

| Camada | O que faz |
|---|---|
| `.gitignore` | Primeira barreira, cobre o caso normal |
| Hooks de pre-commit | `gitleaks` para segredo, `detect-private-key`, `check-added-large-files`, e um verificador próprio que bloqueia dado bruto |
| Verificação em CI | O mesmo verificador roda no GitHub Actions, onde não depende da máquina de ninguém |

## Alternativas descartadas

**Token de acesso pessoal (PAT) para o Databricks.** Descartado porque cria um segredo em texto puro no disco do desenvolvedor, que precisa ser rotacionado manualmente e pode vazar por backup, sincronização de pasta ou processo malicioso. OAuth entrega o mesmo acesso sem esse artefato.

**Versionar uma amostra do dado bruto para facilitar quem clona.** Descartado porque cria duas fontes de verdade e mascara a reprodutibilidade real. Se o pipeline não consegue baixar da origem, isso é um defeito a corrigir, não algo a contornar com cópia versionada.

**Confiar apenas no `.gitignore`.** Descartado pelo motivo da seção anterior: uma única camada, contornável, e o custo do erro é permanente.

## Consequências

**Positivas.** Não existe segredo a rotacionar se o repositório for clonado ou tornado público por engano. O repositório permanece pequeno e clonável. A reprodutibilidade é a partir da fonte oficial, o que é auditável por terceiros.

**Negativas, e são reais.** Quem clonar precisa configurar o próprio acesso ao Databricks antes de rodar qualquer coisa, o que aumenta o atrito de entrada. E a execução depende da disponibilidade do portal do Banco Central, que é uma dependência externa fora do nosso controle.

**Aceitamos essas duas negativas** porque o custo de um segredo vazado em repositório público é assimétrico: irreversível de um lado, e apenas inconveniente do outro.
