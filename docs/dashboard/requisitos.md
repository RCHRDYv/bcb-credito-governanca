# Requisitos do dashboard

O que o dashboard precisa fazer, para quem, e como se confere que ele faz. Este documento conversa com:
- o contexto de produto, em [`dashboard/PRODUCT.md`](../../dashboard/PRODUCT.md);
- o [design system](design-system.md);
- a [arquitetura](arquitetura.md), que diz como o site, o dataset e o chat se ligam;
- as decisões dos ADRs [0016 a 0021](../adr/0016-site-estatico-no-github-pages-e-chat-no-zerogpu.md).

**Como ler:**
- Cada requisito tem um identificador:
  - `RF` é requisito funcional e `RNF` é requisito não funcional;
  - o grupo vem depois: `G` para os gerais, o número da visão (1 a 4) e `C` para o chat.
- **Meta proposta** marca um número que ainda vai ser medido. A medida real sai da issue indicada, e a meta se ajusta com o que a medida mostrar.

## O problema

> Uma financeira quer crescer em crédito para pessoa jurídica. Em quais modalidades e em quais estados vale entrar ou aumentar exposição, e onde o risco está piorando rápido demais para isso?

O dashboard responde com três visões de evidência e uma de recomendação. Cada uma responde a uma pergunta pré-registrada do projeto ou à regra de decisão:

| Visão | Pergunta que responde | Origem | Versão | Issue |
|---|---|---|---|---|
| 1. Onde está o crédito PJ, e onde ele é escasso por empresa | Onde há espaço para crescer | Q14 | v0.1 | #69 |
| 2. Onde o risco está piorando | Onde a inadimplência sobe mais que no país | Q07 | v0.1 | #70 |
| 3. Para onde a carteira aponta | Como a carteira deve evoluir nos próximos três meses | Q27 | v0.2 | #72 |
| 4. A recomendação | Onde entrar, observar, manter ou não entrar | [ADR 0014](../adr/0014-matriz-de-decisao-espaco-contra-risco.md) | v0.1 | #71 |

## Quem usa

| Persona | Situação | Precisa conseguir | Sabemos que funcionou quando |
|---|---|---|---|
| **Executivo de financeira, banco ou fintech** | Tem poucos minutos, entre reuniões, e usa a resposta para decidir ou para defender uma decisão | Saber onde crescer e onde o risco pesa, e por quê | Diz, sem ajuda, onde a financeira deveria entrar e o que o dado não permite afirmar |
| **Gestor de RevOps e estratégia comercial** | Monta metas e planos por região e produto | Ver o detalhe por UF e modalidade e levar os números para o plano | Encontra os números de uma UF e de uma modalidade e os leva para uma tabela |
| **Avaliador técnico** (recrutador, gestor ou entrevistador) | Chega pelo GitHub ou pelo LinkedIn e explora por alguns minutos no computador | Ver método, proveniência e acabamento | Encontra de onde vem um número: a definição, a fonte e, no chat, o SQL |

Os dois primeiros formam o público que o produto serve. O terceiro é quem abre o link hoje. Os dois grupos têm o mesmo peso, e o dashboard precisa funcionar na tela de quem avalia e na reunião do executivo, projetado ou em PDF.

## Requisitos funcionais

### Gerais, para todas as visões

| ID | Requisito | Como verificar | Origem |
|---|---|---|---|
| RF-G01 | A navegação mostra as visões disponíveis e marca a atual | Teste de ponta a ponta percorre as visões pela navegação | Design system, modelos de página |
| RF-G02 | A visão abre nos filtros e na visualização, sem bloco de título-conclusão no topo | Inspeção de cada visão contra o modelo de página escolhido | Decisão de 2026-09-26 |
| RF-G03 | Cada gráfico tem um cabeçalho com título descritivo e a data-base com a fonte, sem conclusão escrita. Quem quiser tirar uma conclusão pergunta ao chat, nas visões que o têm | Inspeção de cada gráfico contra o padrão do cabeçalho | Design system, cabeçalho do gráfico; decisão de 2026-09-26 |
| RF-G04 | Os filtros ficam numa linha, acima do conteúdo, e filtrar nunca muda a cor de uma categoria | Teste de ponta a ponta aplica um filtro e compara as cores antes e depois | Design system, barra de filtros |
| RF-G05 | Clicar num elemento abre o detalhe num painel ao lado, sem janela por cima do conteúdo | Teste de ponta a ponta | Design system, painel de detalhe |
| RF-G06 | Toda visão com gráfico tem uma tabela com os mesmos números | Teste compara os totais do gráfico e da tabela | Design system; WCAG 2.2 |
| RF-G07 | Cada métrica exibida tem a definição da ontologia e a fonte normativa, acessíveis a partir do próprio número | Cada métrica da tela aponta para um conceito de `ontology/` | #17; `dashboard/PRODUCT.md` |
| RF-G08 | O que o dado não permite afirmar aparece junto da recomendação e ao lado de cada número que pede ressalva | Inspeção da visão 4 e dos números com ressalva | [ADR 0005](../adr/0005-projeto-termina-em-recomendacao.md); especificação |
| RF-G09 | A visão imprime e vira PDF sem vidro, com superfícies sólidas e sem perder informação | Prévia de impressão comparada com a tela | Design system; `dashboard/PRODUCT.md` |
| RF-G10 | Números no formato brasileiro (R$ 485,5 bi, 0,93%, +0,15 p.p., jul/2026) e nomes de modalidade iguais aos do BCB | Teste unitário da formatação | Design system, conteúdo |
| RF-G11 | Toda visão tem os estados carregando, vazio e erro. O vazio e o erro dizem como sair deles | Teste de ponta a ponta com dado vazio e com falha de carga | Design system, estados |

### Visão 1: onde está o crédito PJ, e onde ele é escasso por empresa

| ID | Requisito | Como verificar | Origem |
|---|---|---|---|
| RF-101 | Mostra, por UF, a carteira PJ e a carteira por empresa ativa de natureza empresarial, sem MEI, comparada à mediana das UFs na mesma modalidade | Os valores batem com o mart de origem | Q14; ADR 0014, decisão 1 |
| RF-102 | Filtra por modalidade, com a seleção sincronizada entre a visualização por UF e o ranking | Teste de ponta a ponta | #69 |
| RF-103 | Os estados pequenos continuam legíveis, com o cartograma de grade como alternativa ao mapa | Inspeção nas larguras de 360 e 1440 px | #69; #63 |
| RF-104 | Avisa que a UF é a da sede da empresa, e não onde o crédito foi usado | O aviso aparece junto da visualização | `dim_uf`, na ontologia |

### Visão 2: onde o risco está piorando

| ID | Requisito | Como verificar | Origem |
|---|---|---|---|
| RF-201 | Mostra a variação da taxa de inadimplência em seis meses por UF e modalidade, contra a da mesma modalidade no país. Toda taxa é razão de somas | Os valores batem com o mart de origem | Q07; ADR 0014, decisão 3; [ADR 0007](../adr/0007-gold-estrela-para-perguntas-apresentacao-para-dashboard.md) |
| RF-202 | Distingue carteira inadimplida de ativo problemático e marca o alerta antecipado | Inspeção; os alertas batem com o mart | ADR 0014, decisão 6 |
| RF-203 | Mostra a ressalva da mudança de critério do ativo problemático de jan/2025 sempre que a janela a cruza | Teste com uma janela que cruza jan/2025 | Especificação; `docs/cadeia-normativa.md` |

### Visão 3: para onde a carteira aponta (v0.2)

| ID | Requisito | Como verificar | Origem |
|---|---|---|---|
| RF-301 | Mostra a projeção de três meses com intervalo, com o realizado sólido e a projeção hachurada | Inspeção contra o design system | Q27; #27; #72 |
| RF-302 | Mostra o erro do backtest e a comparação com o modelo ingênuo | Os números batem com os da #27 | #27 |

### Visão 4: a recomendação

| ID | Requisito | Como verificar | Origem |
|---|---|---|---|
| RF-401 | Mostra a matriz espaço contra risco com os quatro quadrantes para as células acima do corte de materialidade | Teste compara cada célula com `docs/recomendacao.md`, que sai do mesmo mart | ADR 0014 |
| RF-402 | Mostra o custo de errar nas duas direções, em reais, com a ressalva de que é ordem de grandeza e não perda | Os valores batem com `docs/recomendacao.md` | ADR 0014, decisão 5 |
| RF-403 | Mostra quantas células ficaram fora da matriz, quanto somam e por quê | Os valores batem com `docs/recomendacao.md` | ADR 0014, decisões 2 e 7 |
| RF-404 | Todo quadrante aparece com ícone e rótulo, e nunca só com a cor | Inspeção; axe | Design system; ADR 0018 |

### Chat (v0.3)

| ID | Requisito | Como verificar | Origem |
|---|---|---|---|
| RF-C01 | O chat aparece só nas visões que o preveem. Na v0.1 nenhuma visão tem chat, e quais visões o terão se decide na #51 | Inspeção | [ADR 0020](../adr/0020-design-system-carbon-com-camada-liquid-glass.md); #51 |
| RF-C02 | O chat consulta só o esquema estrela, com a ontologia como contexto, e não tem acesso a nada do experimento | O teste de empacotamento do Space reprova qualquer arquivo de `evaluation/` | [ADR 0019](../adr/0019-chat-consulta-so-o-esquema-estrela.md) |
| RF-C03 | Toda resposta traz o número tirado do dado pela execução do SQL, uma frase curta, a ressalva e o SQL recolhido. Quando o dado não permite responder, o chat diz isso e diz o que faltaria | Perguntas de teste da #74, incluindo perguntas impossíveis | ADR 0019 |
| RF-C04 | O SQL passa por quatro travas antes de rodar: um comando só, só tabelas do esquema estrela, limite de linhas e limite de tempo | Teste com SQL que tenta escrever, ler arquivo ou rodar sem fim | ADR 0019 |
| RF-C05 | O chat mostra em que estado está: acordando, cota do visitante esgotada ou erro | Teste de ponta a ponta simulando cada estado | [ADR 0016](../adr/0016-site-estatico-no-github-pages-e-chat-no-zerogpu.md), decisão 4 |
| RF-C06 | O chat avisa que é um modelo aberto leve, que pode errar, e que por isso mostra o SQL | Inspeção | ADR 0019, decisão 7 |

## Requisitos não funcionais

| ID | Requisito | Meta | Como medir | Situação |
|---|---|---|---|---|
| RNF-01 | Desempenho percebido | Core Web Vitals no nível "bom", no 75º percentil, no celular e no computador: LCP de até 2,5 s, INP de até 200 ms e CLS de até 0,1 [1] | Lighthouse no CI, como aproximação de laboratório. O INP só se mede em uso real, e no laboratório o tempo de bloqueio faz o papel dele | Limites oficiais. Medido no CI desde a #65: na página vazia, com as fontes da #62, LCP de 1,4 s no celular e 0,3 s no computador, CLS 0 e tempo de bloqueio 0. A medida com as visões vem com elas e com a #68 |
| RNF-02 | Nota do Lighthouse | Desempenho de pelo menos 90 no computador e 80 no celular, acessibilidade 100, boas práticas de pelo menos 95 | Lighthouse no CI | Meta proposta, conferida no CI desde a #65, que falha abaixo dela. Na página vazia, 100 nas três notas, no celular e no computador |
| RNF-03 | Orçamento de carga da primeira visão | JavaScript de até 350 KB e dados de até 300 KB, comprimidos. Malha das UFs de até 100 KB. Fontes só com os pesos usados | Relatório do build | Meta proposta. O limite de JavaScript é conferido no CI desde a #65, com 0,8 KB na página vazia. Os de dados e de malha entram na #66 e na #67. As fontes entram no relatório desde a #62, com 83 KB nos quatro arquivos usados. O ECharts importado por partes foi medido na #63: 227,8 KB, e o JavaScript do site soma 251 KB com o catálogo |
| RNF-04 | Acessibilidade | WCAG 2.2 AA; axe sem violação nos dois temas; tudo operável pelo teclado; área de toque de pelo menos 24 px | Playwright com axe no CI | Definido no ADR 0018. O axe roda no CI desde a #65, nos dois temas desde a #62, e com os gráficos desenhados desde a #63. Desde a #64, cada componente tem teste unitário com o jsdom, e um teste confere o texto sobre o vidro no pior ponto do campo de luz. O teste de contraste confere os pares de cor nos dois temas, e o de paletas, as cores de gráfico (ADR 0021) |
| RNF-05 | Telas | De 360 a 1920 px, com os pontos de quebra do Carbon e sem rolagem horizontal | Teste de ponta a ponta em 360, 672, 1056, 1312 e 1920 px | Conferido no CI desde a #65 |
| RNF-06 | Navegadores | As duas últimas versões estáveis do Chrome, do Edge, do Firefox e do Safari, no computador e no celular. O `backdrop-filter` funciona nos quatro desde set/2024, e a curva `linear()` desde dez/2023 [2, 3]. Sem suporte, o vidro vira superfície sólida e a mola vira a curva do Carbon | Playwright com Chromium, Firefox e WebKit | Os três motores são testados no CI desde a #65 |
| RNF-07 | Independência do chat | Com o Space fora do ar, todas as visões abrem e funcionam | Teste de ponta a ponta com a chamada ao Space bloqueada | Definido no ADR 0016 |
| RNF-08 | Custo | Zero: todos os serviços em plano gratuito | Conferência dos planos a cada publicação | Definido nos ADRs 0012 e 0016 |
| RNF-09 | Credenciais | Nenhuma credencial pessoal, de nenhum serviço, no repositório, no CI, na página ou no Space | gitleaks no pre-commit e no CI; nenhuma chave no JavaScript publicado | Definido no ADR 0016 |
| RNF-10 | Experimento protegido | O dashboard não tem acesso ao gabarito nem às perguntas do experimento | Teste de empacotamento do Space; os arquivos do site vêm só dos marts de apresentação | Definido no ADR 0019 |
| RNF-11 | Segurança do conteúdo | Política de segurança de conteúdo sem `unsafe-inline` em script e em folha de estilo. A única exceção é o estilo em atributo, que o ECharts exige ([arquitetura](arquitetura.md#política-de-segurança-de-conteúdo)). Texto do modelo sempre sanitizado antes de entrar na página, sem atributo de estilo | Inspeção da política publicada; teste com texto malicioso | Definido nos ADRs 0016 e 0017 e na arquitetura; verificação na #68 |
| RNF-12 | Atualização do dado | Mensal, pela exportação feita na máquina local, com a data-base visível em cada número | A data-base da tela bate com a do mart | Definido no ADR 0016 |
| RNF-13 | Idioma | Português do Brasil, com os textos num arquivo de tradução para o inglês entrar depois | Nenhum texto fixo nos componentes | Definido no ADR 0017 |
| RNF-14 | Movimento | Nenhuma animação quando o sistema pede movimento reduzido | Teste com a preferência ligada | Definido no design system |

## Fora de escopo

- Dado em tempo real ou atualização automática. O dado é mensal e a exportação é feita na máquina local.
- Login, perfis de usuário e dados privados.
- Qualquer coisa que o SCR.data não sustenta: instituição específica, cliente, safra, rentabilidade, spread e custo de captação ([fronteira do dado](../especificacao.md)).
- Interface em inglês na v0.1.
- Projeção antes da v0.2 e chat antes da v0.3.

## Critério de pronto do dashboard na v0.1

As três visões da v0.1 publicadas, com os requisitos gerais e os de cada visão atendidos.

## Riscos

| Risco | Efeito | Como se reduz | Onde |
|---|---|---|---|
| O Hugging Face muda de novo as regras do ZeroGPU | O chat fica indisponível | As visões não dependem do chat, e as alternativas estão registradas no ADR 0016 | ADR 0016 |
| A cota de GPU do visitante acaba (2 minutos por dia sem login) | O chat para de responder naquele dia | Estado de cota esgotada e um modelo leve, que gasta menos por pergunta | #73 e #74 |
| O vidro pesa em aparelhos fracos | A tela fica lenta | Vidro só no que flutua, desfoque nunca animado, alternativa sólida e meta de 80 no celular | Design system; #65 |
| A exportação do dado é manual | A data-base envelhece | A data-base aparece em cada número; o roteiro de atualização entra na v0.2 | Especificação, runbook |
| A paleta categórica oficial do Carbon falha na validação | Confusão para quem tem daltonismo | Resolvido: a categórica foi ajustada, e um teste automatizado reprova paleta fora dos critérios | ADR 0021 |
| O ECharts estoura o orçamento de carga | A primeira visão demora | Import por partes e medida no build. Medido na #63: 227,8 KB, dentro do limite | #65 e #63 |

## Decisões

| Data | Decisão | Registro |
|---|---|---|
| 2026-09-24 | A projeção de três meses vai para a v0.2 | #27; especificação |
| 2026-09-25 | Site estático no GitHub Pages, e o chat num Space ZeroGPU | ADR 0016 |
| 2026-09-25 | Nenhuma credencial pessoal exposta, de nenhum serviço | ADR 0016 |
| 2026-09-25 | Interface em JavaScript sem framework, com Vite e ECharts | ADR 0017 |
| 2026-09-25 | Design system em tokens DTCG, com tema claro por padrão | ADR 0018 |
| 2026-09-25 | Interface em português, com o inglês preparado | ADR 0017; `dashboard/PRODUCT.md` |
| 2026-09-25 | O chat consulta só o esquema estrela e não é o experimento | ADR 0019 |
| 2026-09-26 | O chat usa só a ontologia como contexto, sem busca nos documentos | ADR 0019 |
| 2026-09-26 | Público com dois grupos de mesmo peso, e os dois diferenciais do produto | `dashboard/PRODUCT.md` |
| 2026-09-26 | Design system oficial: o Carbon com uma camada Liquid Glass | ADR 0020 |
| 2026-09-26 | As visões não têm bloco de título-conclusão | Este documento; design system; ADR 0020 |
| 2026-09-26 | Os gráficos não trazem conclusão escrita, para controlar o escopo; quem quiser uma conclusão pergunta ao chat | Este documento; design system; ADR 0020 |
| 2026-09-27 | O tema escuro é o g100 do Carbon | Design system; ADR 0018 |
| 2026-09-27 | O site segue o tema do sistema do visitante, e a impressão sai sempre clara | Design system; ADR 0018 |
| 2026-09-27 | Paletas de gráfico: a categórica do Carbon ajustada, a sequencial roxa e a divergente roxo e verde-azulado, com teste automatizado | ADR 0021 |
| 2026-09-27 | Matriz com os eixos invertidos, com Entrar no canto superior direito; série temporal na primeira cor categórica, com linha de 3 px; cartograma com a grade conferida contra os centroides do IBGE | Design system |
| 2026-09-27 | Ícones do Tabler pelo pacote, citados pelo nome, sem fonte nem CDN | Design system; ADR 0017 |
| 2026-09-27 | Controle de tema no topo, com claro, escuro e automático, e a escolha guardada no navegador | Design system; ADR 0018 |
| 2026-09-27 | Texto de exemplo nos campos no cinza do texto de ajuda, e não no valor do Carbon, que fica abaixo de 4,5:1 | Design system |
| 2026-09-27 | Campo de luz na cor cheia, vidro regular a 82% (88% no escuro) e gráficos em cartão sólido | ADR 0020, revisão de 2026-09-27; ADR 0021 |
| Em aberto | O nome do produto | `dashboard/PRODUCT.md` |
| Em aberto | Quais visões terão o chat | #51 |

## Onde cada grupo é construído

| Grupo | Issues |
|---|---|
| Requisitos gerais | #62 a #68 e as issues de cada visão |
| Visões 1, 2, 3 e 4 | #69, #70, #72 e #71 |
| Chat | #51, #73 e #74 |
| Requisitos não funcionais | #65 (esqueleto e CI), #66 (exportação), #67 (malha das UFs) e #68 (publicação) |

## Fontes

1. web.dev, "Web Vitals", acessado em 2026-09-26: LCP de até 2,5 s, INP de até 200 ms e CLS de até 0,1, no 75º percentil. https://web.dev/articles/vitals
2. MDN, `backdrop-filter`, acessado em 2026-09-26: Baseline 2024, disponível nos navegadores atuais desde setembro de 2024. https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/backdrop-filter
3. MDN, função de curva `linear()`, acessado em 2026-09-26: disponível nos navegadores desde dezembro de 2023. https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/easing-function/linear
