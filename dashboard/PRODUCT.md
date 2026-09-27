# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Site estático, em JavaScript com ES modules, Vite e ECharts, sem framework, publicado no GitHub Pages. O chat chama um Space ZeroGPU do Hugging Face pelo `@gradio/client`. Decidido nos ADRs 0016 e 0017 (`docs/adr/`).

## Users

O dashboard tem dois públicos com o mesmo peso, confirmado em 2026-09-26:

- **Executivos e gestores de financeiras, bancos e fintechs, e líderes de RevOps e estratégia comercial.** São a persona que o produto serve. Querem saber onde crescer em crédito para empresas e onde o risco está piorando, e usam a resposta em reunião: na tela, projetada ou exportada.
- **Quem avalia o trabalho do autor:** recrutadores, gestores e entrevistadores que chegam pelo GitHub ou pelo LinkedIn e exploram o dashboard por alguns minutos no computador. Querem ver método, clareza e acabamento.

## Product Purpose

Responder a uma pergunta de negócio com dado público do Banco Central: uma financeira quer crescer em crédito para pessoa jurídica. Em quais modalidades e estados vale aumentar a exposição, e onde o risco está piorando rápido demais para isso?

Sucesso é um leitor que não conhece o projeto entender a recomendação sem ajuda, e conseguir conferir de onde vem cada número.

## Positioning

Dois diferenciais, com o mesmo peso (confirmado em 2026-09-26):

- **A decisão vem com a prova.** O dashboard não mostra uma galeria de indicadores: diz onde entrar, observar, manter ou não entrar, com o custo de errar em reais nas duas direções, a fronteira do que o dado não permite afirmar e, no chat, o SQL por trás de cada número.
- **A ontologia explica cada número.** Cada definição vem da norma oficial do BCB, com a fonte citada e as armadilhas do dado declaradas, e isso aparece na tela.

## Operating Context

- Várias visões, cada uma respondendo a uma pergunta: onde está o crédito PJ, onde o risco piora, para onde a carteira aponta (v0.2) e a recomendação. As visões podem ter grids diferentes, e nem todas terão o chat.
- O dado é mensal e agregado (SCR.data). A data-base atual é jul/2026, e cada número mostra a sua.
- O dashboard precisa funcionar na tela de quem avalia e na reunião do executivo, projetado ou exportado.
- O chat, na v0.3, é um modelo aberto leve que consulta o esquema estrela. Ele pode estar dormindo ou sem cota, e as telas não dependem dele.

## Capabilities and Constraints

- Custo zero e nenhuma credencial pessoal exposta, de nenhum serviço (ADR 0016).
- As telas leem só os marts de apresentação exportados. O chat consulta só o esquema estrela, com a ontologia como contexto, e não vê nada do experimento de IA (ADR 0019).
- Interface em português, com os textos num arquivo de tradução para o inglês entrar depois.
- Formatação brasileira: R$ 1,2 bi, 3,4 p.p., set/26. Nomes de modalidade iguais aos do BCB.
- Terminologia fixa: os quatro quadrantes são Entrar, Observar, Manter e Não entrar. "Custo de errar", "fronteira do dado" e "alerta antecipado" têm definição no ADR 0014.
- Em aberto: o nome do produto. As telas usam "Crédito PJ" como nome provisório.
- Decidido em 2026-09-26: as visões não têm bloco de título-conclusão. A visão abre nos filtros e na visualização, e a conclusão, quando houver, fica no cabeçalho do gráfico, gerada do dado.

## Brand Commitments

- **Glassmorphism**, pedido em 2026-09-26 como compromisso visual: a interface deve ser bonita, moderna e alinhada com os melhores dashboards atuais, com superfícies de vidro. Referências citadas: buscas de dashboard no Dribbble e o guia de glassmorphism da UX Pilot.
- **Design system oficial:** o Carbon nas fundações e uma camada Liquid Glass nossa no material, na forma, no movimento e nos componentes, aprovado em 2026-09-26 (ADR 0020, guia em `docs/dashboard/design-system.md`).
- Nome do produto ainda não decidido.

## Evidence on Hand

- Dado real: a matriz de decisão em `docs/recomendacao.md`, gerada do `mrt_decisao`, com data-base jul/2026 (147 células avaliadas, 35 em Entrar, R$ 485,5 bi em carteira PJ onde entrar).
- Os marts de apresentação em `dbt/models/marts/` e a ontologia em `ontology/`.
- A fronteira do dado, escrita em `docs/recomendacao.md` e em `docs/especificacao.md`.
- Não existem: usuários reais, clientes, depoimentos, métricas de uso nem medida de acurácia do chat. Nada disso pode ser inventado em tela.

## Product Principles

1. Cada visão responde a uma pergunta, e o que está na tela prova a resposta.
2. Todo número mostra de onde veio: data-base, fonte e, no chat, o SQL.
3. O que o dado não permite afirmar aparece junto da recomendação, e não escondido no fim.
4. Quem avalia e quem decide leem a mesma tela: nada exige conhecer o projeto para entender.
5. O chat ajuda a explorar, mas a decisão está nas telas, que funcionam sem ele.

## Accessibility & Inclusion

WCAG 2.2 AA (ADR 0018): contraste de 4,5:1 para texto e 3:1 para elemento gráfico, paletas de dados validadas para daltonismo, e nenhum significado transmitido só por cor.
