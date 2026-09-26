# ADR 0001: Credenciais e dado bruto ficam fora do repositório

**Status:** Aceito. Ampliado pelo [ADR 0016](0016-site-estatico-no-github-pages-e-chat-no-zerogpu.md) em 2026-09-25: a regra vale para toda credencial pessoal, de qualquer serviço.
**Data:** 2026-08-20

## Contexto

Este é um repositório público, e isso muda o cálculo de risco por dois motivos: qualquer pessoa lê o conteúdo, e **o histórico do git é permanente**. Apagar um segredo do arquivo não o remove do histórico. Corrigir de verdade exige reescrever o histórico e rotacionar a credencial exposta.

O projeto conecta a um workspace Databricks e consome arquivos de dado grandes, o que cria dois problemas de naturezas diferentes: vazamento de credencial e inchaço permanente do repositório.

**Nota de 2026-09-21:** na data deste ADR, o volume conhecido era de cerca de 97 MB por arquivo mensal. A ingestão mediu o volume real: 100 MB por mês na V2 e 300 MB na V1, somando 12,7 GB no recorte do projeto.

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

**Positivas.** Não existe segredo a rotacionar se o repositório for clonado ou tornado público por engano. O repositório permanece pequeno e clonável. A reprodução parte da fonte oficial, o que qualquer pessoa pode auditar.

**Negativas, e são reais.** Quem clonar precisa configurar o próprio acesso ao Databricks antes de rodar qualquer coisa, o que aumenta o atrito de entrada. A execução também depende da disponibilidade do portal do Banco Central, uma dependência externa.

**As duas negativas são aceitas** porque o custo de um segredo vazado em repositório público é assimétrico: irreversível de um lado, apenas inconveniente do outro.
