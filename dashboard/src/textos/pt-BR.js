/**
 * PT: Todos os textos da interface, em português do Brasil.
 *
 *     Nenhum componente escreve texto fixo: ele pede o texto pela chave, com a
 *     função `t()` de `./index.js`. Quando o inglês entrar, ele vira um arquivo
 *     irmão deste, com as mesmas chaves, sem mexer em componente nenhum
 *     (ADR 0017, decisão 6; requisito RNF-13).
 *
 *     As chaves são planas e agrupadas pelo prefixo, como `produto.`,
 *     `pagina.`, `navegacao.` e `tela1.`. "Crédito PJ" é o nome provisório do produto, até a decisão
 *     registrada em `dashboard/PRODUCT.md`.
 *
 * EN: Every interface text, in Brazilian Portuguese. Components never hold
 *     fixed text; they ask for it by key through `t()`. English will be a
 *     sibling file with the same keys. "Crédito PJ" is a provisional name.
 */

export const ptBR = Object.freeze({
  "produto.nome": "Crédito PJ",
  "pagina.titulo": "Crédito PJ: onde crescer em crédito para empresas",
  "pagina.pular-para-o-conteudo": "Pular para o conteúdo",

  "catalogo.titulo-da-pagina": "Catálogo do design system · Crédito PJ",
  "catalogo.titulo": "Catálogo do design system",
  "catalogo.introducao":
    "As fundações, os componentes e os gráficos do dashboard, lidos direto dos tokens. As seções que mudam com o tema mostram o claro e o escuro lado a lado, e o controle no topo troca o tema da página.",
  "catalogo.guia": "Ler o guia do design system",
  "catalogo.tema-claro": "Tema claro",
  "catalogo.tema-escuro": "Tema escuro",

  "catalogo.cores": "Cores",
  "catalogo.cores-explicacao":
    "O papel de cada cor na interface. O contraste é medido pela WCAG 2.2 contra o fundo em que a cor é usada: a página, ou, no texto sobre cor forte, o botão primário. O mínimo é 4,5:1 para texto e 3:1 para elemento gráfico. As bordas sutis são decorativas e não têm mínimo.",
  "catalogo.coluna-cor": "Cor",
  "catalogo.coluna-token": "Token",
  "catalogo.coluna-valor": "Valor",
  "catalogo.coluna-contraste": "Contraste",
  "catalogo.grupo.fundos": "Fundos",
  "catalogo.grupo.bordas": "Bordas",
  "catalogo.grupo.texto": "Texto",
  "catalogo.grupo.acao": "Ação e foco",
  "catalogo.grupo.estado": "Estado",
  "catalogo.grupo.quadrantes": "Quadrantes da recomendação",
  "catalogo.grupo.alerta": "Alerta antecipado",
  "catalogo.grupo.campo-de-luz": "Campo de luz",

  "catalogo.paleta": "Paleta do Carbon",
  "catalogo.paleta-explicacao":
    "Os primitivos: os degraus oficiais do Carbon que as cores semânticas usam. Não mudam com o tema.",

  "catalogo.tipografia": "Tipografia",
  "catalogo.tipografia-explicacao":
    "A escala produtiva do Carbon, em IBM Plex Sans e IBM Plex Mono.",
  "catalogo.tipografia-exemplo": "Onde crescer em crédito para empresas",
  "catalogo.tipografia-codigo": "select uf, sum(carteira_ativa) from fct_carteira group by uf",

  "catalogo.espacamento": "Espaçamento",
  "catalogo.espacamento-explicacao":
    "A escala do Carbon: de 2 a 16 px dentro de componentes, de 24 a 48 px entre blocos, e de 64 px para cima entre seções.",

  "catalogo.raios": "Raios",
  "catalogo.raios-explicacao": "Os raios da camada Liquid Glass, pelo uso.",

  "catalogo.elevacao": "Elevação",
  "catalogo.elevacao-explicacao":
    "Nível 1 para painéis, tabelas e cartões, e nível 2 para o que flutua. No escuro, a sombra é mais forte para continuar visível.",
  "catalogo.nivel-1": "Nível 1",
  "catalogo.nivel-2": "Nível 2",

  "catalogo.vidro": "Vidro",
  "catalogo.vidro-explicacao":
    "O vidro claro vai no que flutua, e o regular em tudo que tem dado ou texto. Atrás dele fica o campo de luz, com as cores do próprio Carbon.",
  "catalogo.vidro-claro": "Vidro claro",
  "catalogo.vidro-regular": "Vidro regular",
  "catalogo.vidro-texto": "Texto de ajuda sobre o vidro, com o contraste conferido no teste.",

  "catalogo.movimento": "Movimento",
  "catalogo.movimento-explicacao":
    "A mola passa um pouco do ponto final antes de assentar, e vai em posição e escala. Cor e opacidade usam a curva do Carbon. Com movimento reduzido no sistema, nada se move.",
  "catalogo.mola": "Mola",
  "catalogo.produtiva": "Curva produtiva do Carbon",
  "catalogo.mover": "Mover",

  "catalogo.controles": "Controles",
  "catalogo.controles-explicacao":
    "Botões, controle segmentado, chips e campos, com os estados de cada um. O foco do teclado aparece sempre, e cada controle funciona sem mouse.",
  "catalogo.botoes": "Botões: primário, secundário, sutil, desativado e carregando",
  "catalogo.exemplo-aplicar": "Aplicar filtro",
  "catalogo.exemplo-exportar": "Exportar PDF",
  "catalogo.desativado": "Desativado",
  "catalogo.controle-segmentado": "Controle segmentado",
  "catalogo.exemplo-visao": "Visão",
  "catalogo.visao-credito": "Onde está o crédito",
  "catalogo.visao-risco": "Onde o risco piora",
  "catalogo.visao-recomendacao": "Recomendação",
  "catalogo.chips": "Chips de filtro",
  "catalogo.exemplo-modalidades": "Modalidades",
  "catalogo.campos": "Campos: com ajuda, preenchido, com erro e desativado",
  "catalogo.campo-de-selecao": "Campo de seleção",
  "catalogo.definicao": "Definição do número",
  "catalogo.campo-estado": "Estado",
  "catalogo.exemplo-sp": "Ex.: SP",
  "catalogo.ajuda-estado": "A sigla da UF, com duas letras.",
  "catalogo.campo-modalidade": "Modalidade",
  "catalogo.erro-estado": "Não existe UF com essa sigla. Use duas letras, como SP.",
  "catalogo.campo-pergunta": "Pergunta",
  "catalogo.chat-indisponivel": "Chat indisponível",
  "catalogo.dados-e-avisos": "Dados e avisos",
  "catalogo.dados-e-avisos-explicacao":
    "Etiquetas, tabela, dica flutuante e avisos, com os números de jul/2026 da recomendação. Nenhum significado depende só da cor.",
  "catalogo.etiquetas": "Etiquetas de quadrante e alerta antecipado",
  "catalogo.tabela": "Tabela",
  "catalogo.tabela-legenda":
    "As duas combinações de UF e modalidade com mais carteira PJ em cada quadrante, {data}",
  "catalogo.coluna-uf": "UF",
  "catalogo.coluna-modalidade": "Modalidade",
  "catalogo.coluna-carteira": "Carteira PJ",
  "catalogo.coluna-espaco": "Índice de espaço",
  "catalogo.coluna-risco": "Variação além do país",
  "catalogo.coluna-quadrante": "Quadrante",
  "catalogo.coluna-alerta": "Alerta",
  "catalogo.dica": "Dica flutuante",
  "catalogo.dica-nota":
    "A primeira dica aparece aberta, para mostrar o visual. A segunda abre com o mouse ou com o foco do teclado, e fecha com o Esc.",
  "catalogo.avisos": "Avisos: informação, atenção e erro",
  "catalogo.aviso-em-linha": "Aviso em linha, para a ressalva dentro de um cartão",
  "catalogo.painel-de-detalhe": "Painel de detalhe",
  "catalogo.painel-de-detalhe-nota":
    "No computador, fica ao lado do conteúdo e rola por dentro; no celular, vira a folha que sobe de baixo. Aqui, fica no fluxo da página.",
  "catalogo.aviso-uf-da-sede": "A UF é a da sede da empresa, e não onde o crédito foi usado.",
  "catalogo.aviso-quebra": "A série cruza a mudança de critério do ativo problemático de jan/2025.",
  "catalogo.aviso-erro": "Os dados não carregaram. Tente de novo em alguns segundos.",
  "catalogo.chat": "Chat",
  "catalogo.chat-explicacao":
    "A pergunta, a resposta com o número, a frase, a ressalva e o SQL recolhido, a abstenção quando o dado não permite responder, e a entrada.",
  "catalogo.chat-ilustrativo":
    "Exemplo ilustrativo: o chat entra na v0.3 (#51). O número vem do dado do projeto; o SQL é um exemplo e não foi executado.",
  "catalogo.chat-pergunta": "Qual a carteira PJ por empresa ativa em {modalidade} em São Paulo?",
  "catalogo.chat-frase": "em {data}, a maior entre as UFs. A mediana das UFs é {mediana}.",
  "catalogo.chat-sql":
    "select sum(c.carteira_ativa) / sum(e.empresas_ativas)\nfrom fct_carteira c\njoin dim_modalidade m using (codigo_submodalidade)\njoin fct_empresas_ativas e using (data_base, uf)\nwhere c.data_base = '2026-07-31' and c.uf = 'SP'\n  and c.cliente = 'PJ' and m.modalidade = 'Empréstimos'",
  "catalogo.chat-pergunta-sem-dado": "Qual banco mais emprestou para empresas no Rio de Janeiro?",
  "catalogo.chat-motivo": "O SCR.data é agregado por segmento, e não identifica instituições.",
  "catalogo.chat-faltaria":
    "Para responder, seria preciso o dado por instituição, que o SCR.data não publica.",
  "catalogo.estados": "Estados",
  "catalogo.estados-explicacao":
    "Carregando, vazio, erro e o chat acordando. Cada estado diz o que está acontecendo e, quando dá, a saída.",
  "catalogo.estado-carregando": "Carregando",
  "catalogo.estado-vazio": "Vazio",
  "catalogo.estado-erro": "Erro",
  "catalogo.estado-chat-acordando": "Chat acordando",
  "catalogo.vazio-titulo": "Nenhuma combinação neste filtro",
  "catalogo.vazio-texto":
    "Nenhuma combinação passa no corte de R$ 1 bi com esse filtro. Tire um dos filtros para ver mais.",
  "catalogo.erro-titulo": "Os dados não carregaram",
  "catalogo.erro-texto":
    "O arquivo da visão não respondeu. As outras visões continuam funcionando.",

  "catalogo.paletas-de-grafico": "Paletas de gráfico",
  "catalogo.paletas-de-grafico-explicacao":
    "Cada paleta tem um papel. A categórica diz qual série é qual; a sequencial, a única rampa, diz quanto, inclusive a distância até uma referência, em faixas. As faixas de baixo mostram como cada paleta aparece para quem tem daltonismo, pela simulação de Machado, Oliveira e Fernandes (2009).",
  "catalogo.paleta-categorica": "Categórica",
  "catalogo.paleta-sequencial": "Sequencial",
  "catalogo.sem-daltonismo": "Sem daltonismo",
  "catalogo.protanopia": "Protanopia",
  "catalogo.deuteranopia": "Deuteranopia",
  "catalogo.tritanopia": "Tritanopia",

  "catalogo.graficos": "Gráficos",
  "catalogo.graficos-explicacao":
    "Os componentes de gráfico, com dado real do projeto. Cada cartão traz só o título e a data-base com a fonte, sem conclusão escrita. Passe o mouse sobre um elemento para ver os números.",
  "catalogo.fonte-dos-exemplos": "SCR.data, do Banco Central",
  "catalogo.exemplo-mapa": "Carteira PJ por empresa ativa em Empréstimos, por UF",
  "catalogo.exemplo-cartograma-faixas":
    "Variação da inadimplência contra a do país em Empréstimos, por UF",
  "catalogo.exemplo-matriz": "Espaço contra risco, por UF e modalidade",
  "catalogo.escala-do-desvio": "Variação contra a do país, em p.p.",
  "catalogo.exemplo-serie": "Taxa de inadimplência PJ no país",
  "catalogo.exemplo-linhas": "Inadimplência e ativo problemático no Maranhão, em Empréstimos",
  "catalogo.nota-das-linhas":
    "Série com duas medidas, um marco e uma janela, como no painel da UF da Tela 2. Lida do arquivo mensal exportado.",
  "catalogo.exemplo-ranking": "As dez UFs com mais carteira PJ por empresa ativa em Empréstimos",
  "catalogo.exemplo-destaque": "Carteira PJ onde a regra recomenda entrar",
  "catalogo.exemplo-destaque-rotulo":
    "de carteira PJ nas {celulas} combinações de UF e modalidade em que a regra recomenda entrar",
  "catalogo.projecao-ilustrativa": "Projeção ilustrativa",
  "catalogo.nota-da-projecao":
    "A projeção deste exemplo é ilustrativa: repete o último mês, com um intervalo de dois desvios das variações mensais. A projeção do modelo chega com a #27.",
  "catalogo.nota-do-cartograma":
    "O cartograma usa as mesmas classes do mapa, e cada UF tem o mesmo tamanho. É a alternativa quando os estados pequenos precisam ser lidos.",
  "catalogo.mediana-das-ufs": "mediana das UFs",
  "catalogo.troca-de-tema": "Troca de tema no mesmo gráfico",
  "catalogo.troca-de-tema-explicacao":
    "Este gráfico segue o tema da página. O botão troca o atributo data-tema da página, e o gráfico recebe o tema novo sem ser recriado.",
  "catalogo.trocar-tema": "Trocar o tema da página",

  "grafico.sem-dado": "sem dado",
  "grafico.intervalo": "intervalo de {de} a {ate}",
  "grafico.erro-da-malha":
    "O mapa não carregou, porque a malha das UFs não está disponível. O cartograma e a tabela continuam com os mesmos números.",
  "grafico.acima-do-pais-forte": "Acima do país, mais de {b}",
  "grafico.acima-do-pais": "Acima do país, de {a} a {b}",
  "grafico.igual-ao-pais": "Igual ao país, até {a}",
  "grafico.abaixo-do-pais": "Abaixo do país, de {a} a {b}",
  "grafico.abaixo-do-pais-forte": "Abaixo do país, mais de {b}",
  "grafico.abaixo-do-pais-curto": "Abaixo do país",
  "grafico.acima-do-pais-curto": "Acima do país",
  "grafico.matriz-de-calor-aria":
    "Matriz de calor com a distância de cada UF até a mediana, em cada modalidade. Os números estão na tabela.",

  "matriz.eixo-espaco": "Carteira por empresa, em vezes a mediana das UFs",
  "matriz.eixo-espaco-curto": "Carteira por empresa",
  "matriz.eixo-risco": "Variação da inadimplência além da do país (p.p.)",
  "matriz.eixo-risco-curto": "Variação além da do país",
  "matriz.eixo-espaco-estreito": "Carteira por empresa ÷ mediana",
  "matriz.eixo-risco-estreito": "Além do país (p.p.)",

  "alerta-antecipado.nome": "Alerta antecipado",

  "tema.rotulo": "Tema",
  "tema.claro": "Claro",
  "tema.escuro": "Escuro",
  "tema.automatico": "Automático",

  "chat.conversa": "Conversa com o chat",
  "chat.pergunta": "Pergunta",
  "chat.resposta": "Resposta do chat",
  "chat.ver-o-sql": "Ver o SQL",
  "chat.abstencao": "Não dá para responder com este dado.",
  "chat.exemplo": "Pergunte sobre crédito PJ",
  "chat.rotulo-da-entrada": "Sua pergunta sobre crédito PJ",
  "chat.enviar": "Enviar a pergunta",

  "estado.carregando": "Carregando os dados",
  "estado.tentar-de-novo": "Tentar de novo",
  "estado.chat-acordando": "O chat está acordando",
  "estado.chat-acordando-texto":
    "O modelo leva alguns segundos para carregar na primeira pergunta. As outras telas continuam funcionando enquanto isso.",

  "quadrante.entrar": "Entrar",
  "quadrante.observar": "Observar",
  "quadrante.nao-entrar": "Não entrar",
  "quadrante.manter": "Manter",

  "navegacao.rotulo": "Visões do dashboard",
  "navegacao.credito-por-uf": "Onde está o crédito",
  "navegacao.risco-por-uf": "Onde o risco piora",
  "navegacao.projecao": "Para onde a carteira aponta",
  "navegacao.erro-titulo": "Não foi possível abrir esta visão",
  "navegacao.erro-rede": "Os dados não chegaram. Confira a conexão e tente de novo.",
  "navegacao.erro-formato": "Os dados chegaram incompletos. Tente de novo em alguns instantes.",

  "definicao.o-que-e": "O que é {rotulo}",
  "definicao.oficial": "Definição oficial",
  "definicao.sem-definicao-oficial": "O documento oficial não define este termo.",
  "definicao.fonte-da-explicacao": "Explicação do projeto, a partir de: {fonte}",
  "definicao.do-projeto": "A regra deste número foi fixada pelo projeto, no {adr}.",
  "definicao.ler-o-adr": "Ler o registro da decisão",
  "definicao.confianca-verbatim": "transcrita da fonte",
  "definicao.confianca-parafraseado": "redação própria, amparada na fonte",
  "definicao.confianca-inferido": "inferida do contexto",
  "definicao.confianca-lacuna": "sem definição na fonte",

  "detalhe.rotulo": "Detalhe",
  "detalhe.fechar": "Fechar o detalhe",

  "tela1.titulo": "Onde está o crédito PJ, e onde ele é escasso por empresa",
  "tela1.filtro-modalidade": "Modalidade",
  "tela1.todas-as-modalidades": "Todas as modalidades",
  "tela1.todas-no-titulo": "todas as modalidades",
  "tela1.desenho": "Desenho do território",
  "tela1.mapa": "Mapa",
  "tela1.grade": "Grade",
  "tela1.matriz": "Matriz",
  "tela1.tabela": "Tabela",
  "tela1.fonte": "SCR.data, do Banco Central, e CNPJ, da Receita Federal",
  "tela1.fonte-com-malha": "SCR.data, do Banco Central, e CNPJ, da Receita Federal; malha do IBGE",
  "tela1.titulo-territorio": "Carteira PJ por empresa em {recorte}, por UF",
  "tela1.mediana-das-ufs": "Mediana das UFs",
  "tela1.sem-comparacao": "Sem comparação com a mediana",
  "tela1.na-mediana": "na mediana",
  "tela1.abaixo-da-mediana-em": "{valor} abaixo da mediana",
  "tela1.acima-da-mediana-em": "{valor} acima da mediana",
  "tela1.por-empresa": "{valor} por empresa",
  "tela1.motivo-abaixo-do-corte": "Fora da comparação: carteira abaixo de {corte} nesta modalidade",
  "tela1.motivo-poucas-ufs":
    "Fora da comparação: poucas UFs passam do corte de {corte} nesta modalidade",
  "tela1.motivo-sem-carteira": "Sem carteira nesta modalidade",
  "tela1.aviso-sede":
    "A UF é a da sede da empresa que tomou o crédito, e não a do lugar onde o dinheiro foi usado.",
  "tela1.sem-malha":
    "O mapa não carregou. A grade mostra os mesmos números, com cada UF do mesmo tamanho.",
  "tela1.vazio-titulo": "Nenhuma UF entra na comparação nesta modalidade",
  "tela1.vazio-texto":
    "Para comparar com a mediana, a modalidade precisa de pelo menos {minimo} UFs com carteira acima de {corte}. Abaixo disso, a comparação não daria um número estável. A tabela mostra os valores de cada UF.",
  "tela1.detalhe-dica":
    "Escolha uma UF no mapa, na grade, na matriz, na tabela ou no ranking para ver os números dela.",
  "tela1.carteira-pj": "Carteira PJ",
  "tela1.empresas": "Empresas sem MEI",
  "tela1.carteira-por-empresa": "Carteira por empresa",
  "tela1.nota-retrato":
    "O número de empresas é reconstruído do retrato de {mes} do CNPJ, a {meses} meses da data-base.",
  "tela1.legenda-tabela": "Carteira PJ por empresa em {recorte}, por UF, em {data}",
  "tela1.coluna-uf": "UF",
  "tela1.coluna-posicao": "Em relação à mediana",
  "tela1.coluna-participacao": "Participação no país",
  "tela1.coluna-custo": "Crédito que faltaria",
  "tela1.coluna-situacao": "Situação",
  "tela1.indice-csv": "Índice de espaço",
  "tela1.posicao": "Posição na carteira por empresa",
  "tela1.titulo-ranking": "Crédito que faltaria para cada UF chegar à mediana, em {recorte}",
  "tela1.rolagem-do-ranking": "Ranking do crédito que faltaria, com rolagem",
  "tela1.titulo-matriz": "Distância de cada UF até a mediana, por modalidade",
  "tela1.titulo-destaque": "Oportunidade em {recorte}",
  "tela1.destaque-rotulo":
    "de crédito PJ faltariam para as {abaixo} UFs abaixo da mediana chegarem a ela",
  "tela1.resumo-carteira": "Carteira PJ",
  "tela1.resumo-mediana": "Mediana da carteira por empresa",
  "tela1.ressalva-demanda":
    "Pouco crédito por empresa pode ser pouca demanda, e não espaço para crescer. A comparação não desconta o porte das empresas nem a renda de cada UF.",
  "tela1.legenda-forte-abaixo": "Mais espaço: mais de {b} abaixo da mediana",
  "tela1.legenda-abaixo": "Mais espaço: de {a} a {b} abaixo",
  "tela1.legenda-meio": "Perto da mediana: até {a} de diferença",
  "tela1.legenda-acima": "Menos espaço: de {a} a {b} acima",
  "tela1.legenda-forte-acima": "Menos espaço: mais de {b} acima da mediana",
  "tela1.escala-titulo": "Carteira por empresa em relação à mediana das UFs",
  "tela1.escala-mais-espaco": "Mais espaço",
  "tela1.escala-menos-espaco": "Menos espaço",
  "tela1.posicao-entre": "{posicao}ª menor de {de}",
  "tela1.participacao-no-pais": "{valor} da carteira PJ do país",
  "tela1.carteira-na-modalidade": "Carteira PJ nesta modalidade",
  "tela1.carteira-por-empresa-e-posicao": "Carteira por empresa",
  "tela1.custo-da-uf": "Crédito que faltaria para chegar à mediana",
  "tela1.modalidades-da-uf": "Modalidades nesta UF",
  "tela1.fora-da-comparacao": "fora da comparação",
  "tela1.baixar-csv": "Baixar em CSV",
  "tela1.opcao-sem-comparacao": "{nome}, sem UF comparável",
  "tela1.dica-celula": "{uf} em {modalidade}: {posicao}",
  "tela1.dica-celula-fora": "{uf} em {modalidade}: fora da comparação",

  "tela2.titulo": "Onde o risco de crédito PJ está piorando mais que no país",
  "tela2.fonte": "SCR.data, do Banco Central",
  "tela2.fonte-com-malha": "SCR.data, do Banco Central; malha do IBGE",
  "tela2.janela": "{de} a {ate}",
  "tela2.titulo-territorio":
    "Variação da inadimplência em {meses} meses, contra a do país, em {modalidade}",
  "tela2.titulo-matriz": "Variação da inadimplência contra a do país, por UF e modalidade",
  "tela2.resumo-taxa-pais": "Taxa do país",
  "tela2.resumo-variacao-pais": "Variação do país em {meses} meses",
  "tela2.resumo-piorando": "UFs piorando mais que o país",
  "tela2.resumo-alertas": "UFs com alerta antecipado",
  "tela2.de": "{n} de {total}",
  "tela2.dois-numeros": "Dois números de atraso",
  "tela2.inadimplida": "Carteira inadimplida",
  "tela2.inadimplida-texto":
    "o crédito com alguma parcela vencida há mais de 90 dias. É o número que pinta o mapa.",
  "tela2.ativo-problematico": "Ativo problemático",
  "tela2.ativo-problematico-texto":
    "o crédito que a própria instituição classifica como problemático. Pode mostrar a piora antes de ela virar atraso: quando ele se afasta da inadimplida mais que no país, a UF ganha o alerta antecipado.",
  "tela2.quebra-na-janela":
    "A janela de {de} a {ate} cruza a mudança de critério do ativo problemático, em {quebra}. O alerta antecipado compara duas definições.",
  "tela2.quebra-na-serie":
    "Em {quebra}, o ativo problemático mudou de critério, e a linha tracejada não compara os dois lados dessa data.",
  "tela2.quebra-marco": "muda o critério",
  "tela2.janela-rotulo": "{meses} meses",
  "tela2.titulo-destaque": "Custo do risco em {modalidade}",
  "tela2.destaque-rotulo":
    "é a ordem de grandeza do aumento da carteira inadimplida nas {n} UFs onde a taxa subiu mais que no país",
  "tela2.destaque-rotulo-uma":
    "é a ordem de grandeza do aumento da carteira inadimplida na UF onde a taxa subiu mais que no país",
  "tela2.ressalva-perda": "Não é perda: o dado não tem recuperação nem taxa de juros.",
  "tela2.vazio-piora-titulo": "Nenhuma UF piorou mais que o país nesta modalidade",
  "tela2.vazio-piora-texto":
    "Em {meses} meses, a inadimplência de cada UF comparada subiu menos que a do país, ou caiu. A tabela mostra os números de cada UF.",
  "tela2.vazio-titulo": "Nenhuma UF entra na comparação nesta modalidade",
  "tela2.vazio-texto":
    "Para comparar com o país, a modalidade precisa de pelo menos {minimo} UFs com carteira acima de {corte}. Abaixo disso, a comparação não daria um número estável. A tabela mostra os valores de cada UF.",
  "tela2.titulo-ranking": "Quanto a taxa subiu a mais que no país, em {modalidade}",
  "tela2.rolagem-do-ranking": "Ranking da piora contra o país, com rolagem",
  "tela2.nota-ranking": "As UFs que não pioraram mais que o país estão na tabela.",
  "tela2.escala-titulo": "Variação contra a do país, em p.p.",
  "tela2.escala-melhor": "Melhor que o país",
  "tela2.escala-pior": "Pior que o país",
  "tela2.legenda-forte-abaixo": "Melhor que o país, por mais de {b}",
  "tela2.legenda-abaixo": "Melhor que o país, por {a} a {b}",
  "tela2.legenda-meio": "Perto do país: até {a} de diferença",
  "tela2.legenda-acima": "Pior que o país, por {a} a {b}",
  "tela2.legenda-forte-acima": "Pior que o país, por mais de {b}",
  "tela2.sem-comparacao": "Fora da comparação com o país",
  "tela2.contra-o-pais": "{valor} contra o país",
  "tela2.dica-celula": "{uf} em {modalidade}: {valor} contra o país",
  "tela2.legenda-tabela": "Inadimplência em {modalidade}, por UF, de {de} a {ate}",
  "tela2.coluna-taxa": "Taxa de inadimplência",
  "tela2.coluna-taxa-anterior": "Taxa {meses} meses antes",
  "tela2.coluna-variacao": "Variação em {meses} meses",
  "tela2.coluna-variacao-pais": "Variação do país",
  "tela2.coluna-contra-o-pais": "Contra o país",
  "tela2.coluna-alerta": "Alerta antecipado",
  "tela2.coluna-quadrante": "Quadrante",
  "tela2.coluna-custo": "Custo do risco",
  "tela2.sim": "Sim",
  "tela2.nao": "Não",
  "tela2.detalhe-dica":
    "Escolha uma UF no mapa, na grade, na matriz, na tabela ou no ranking para ver os números e a série dela.",
  "tela2.taxa-da-uf": "Taxa de inadimplência",
  "tela2.variacao-da-uf": "Variação em {meses} meses",
  "tela2.variacao-do-pais": "No país, na mesma modalidade",
  "tela2.custo-do-risco": "Custo do risco",
  "tela2.alerta-texto":
    "A distância até o ativo problemático abriu {valor} a mais que no país, em {meses} meses.",
  "tela2.titulo-serie": "Inadimplência e ativo problemático, em % da carteira",
  "tela2.serie-carregando": "Carregando a série mensal",
  "tela2.serie-erro": "A série mensal não carregou. Os números acima continuam valendo.",

  "tela3.titulo": "Para onde a carteira de crédito PJ aponta nos próximos três meses",
  "tela3.fonte": "SCR.data, do Banco Central",
  "tela3.filtro-serie": "Série",
  "tela3.grupo-pais": "País",
  "tela3.grupo-modalidades": "Modalidades",
  "tela3.grupo-ufs": "UFs",
  "tela3.brasil": "Brasil, toda a carteira PJ",
  "tela3.periodo": "Período",
  "tela3.periodo-12-meses": "Últimos 12 meses",
  "tela3.periodo-desde-2024": "Desde jan/2024",
  "tela3.forma": "Ver como",
  "tela3.grafico": "Gráfico",
  "tela3.titulo-serie": "Carteira ativa PJ: {serie}, com a projeção de 3 meses",
  "tela3.janela-12-meses": "Últimos 12 meses e projeção até {ate}",
  "tela3.janela-desde-2024": "Desde jan/2024 e projeção até {ate}",
  "tela3.ultimo-dado": "Último dado, {mes}",
  "tela3.ultimo-dado-marco": "último dado",
  "tela3.rolagem-da-serie": "A série escolhida e a projeção mês a mês, com rolagem",
  "tela3.metodo": "Método escolhido",
  "tela3.mes-a-mes": "Projeção mês a mês",
  "tela3.coluna-mes": "Mês",
  "tela3.coluna-realizado": "Realizado",
  "tela3.coluna-projecao": "Projeção",
  "tela3.coluna-faixa": "Faixa provável",
  "tela3.coluna-inferior": "Faixa provável, de",
  "tela3.coluna-superior": "Faixa provável, até",
  "tela3.faixa": "{de} a {ate}",
  "tela3.faixa-na-dica": "faixa provável de {de} a {ate}",
  "tela3.faixa-explicacao":
    "Em 8 de cada 10 meses, o valor real deve cair dentro da faixa provável.",
  "tela3.como-titulo": "Como a projeção é feita",
  "tela3.como-texto":
    "Dez métodos passaram por 16 testes com meses que já aconteceram. A tendência média é a referência, e outro método só fica com a série se errar menos nesses testes, com uma diferença grande demais para ser acaso.",
  "tela3.modelo.deriva": "Tendência média",
  "tela3.modelo.ingenuo": "Repetir o último mês",
  "tela3.modelo.ingenuo_sazonal": "Repetir o mesmo mês do ano anterior",
  "tela3.modelo.theta": "Tendência suavizada",
  "tela3.modelo.holt_amortecido": "Tendência que perde força",
  "tela3.modelo.arima": "Padrão dos meses anteriores",
  "tela3.modelo.sarimax": "Padrão dos meses anteriores, com a Selic",
  "tela3.modelo.prophet": "Tendência com ciclo anual",
  "tela3.modelo.combinacao": "Média de três modelos",
  "tela3.modelo.lightgbm": "Aprendizado de máquina",
  "tela3.como.ingenuo_sazonal":
    "Nesta série, repetir o mesmo mês do ano anterior errou menos que a tendência média: a projeção de cada mês é o valor do mesmo mês um ano antes.",
  "tela3.como.holt_amortecido":
    "Nesta série, ficou a tendência que perde força: a projeção segue a direção recente da série, cada vez mais devagar.",
  "tela3.como.arima":
    "Nesta série, ficou o padrão dos meses anteriores: a projeção vem de como cada mês da série dependeu dos meses que vieram antes dele.",
  "tela3.como.sarimax":
    "Nesta série, ficou o padrão dos meses anteriores com a Selic: o mesmo método, que também leva em conta a Selic de três meses antes.",
  "tela3.como.prophet":
    "Nesta série, ficou a tendência com ciclo anual: a projeção soma uma tendência que pode mudar de inclinação e o efeito de cada mês do ano.",
  "tela3.como.lightgbm":
    "Nesta série, ficou o aprendizado de máquina: um modelo treinado com todas as UFs e modalidades ao mesmo tempo, com as variações recentes, o mês do ano e a Selic.",
  "tela3.como.deriva":
    "Nesta série, ficou a tendência média: a projeção soma ao último mês a variação média mensal da série desde jan/2024.",
  "tela3.como.combinacao":
    "Nesta série, ficou a média de três modelos: a tendência média, uma tendência que perde força com o tempo e um modelo de aprendizado de máquina treinado com todas as UFs e modalidades.",
  "tela3.como.theta":
    "Nesta série, ficou a tendência suavizada: a tendência de longo prazo da série, somada a uma média que pesa mais os meses recentes.",
  "tela3.como.ingenuo":
    "Nesta série, repetir o último mês errou menos que a tendência média: a projeção é o valor do último mês, com a faixa provável em volta.",
  "tela3.realizado": "Realizado",
  "tela3.projecao": "Projeção",
  "tela3.legenda-tabela": "Carteira ativa PJ, {serie}, mês a mês, com a projeção",
  "tela3.titulo-teste": "O que a projeção teria dito em {mes}",
  "tela3.subtitulo-teste": "Um dos 4 testes recentes, contra o que aconteceu depois",
  "tela3.data-do-teste": "Data do teste",
  "tela3.aconteceu": "O que aconteceu",
  "tela3.dizia": "O que a projeção dizia",
  "tela3.marco-do-teste": "teste",
  "tela3.erro-frase":
    "Nos 4 testes recentes, a projeção errou em média {erro}, contra {repetir} de repetir o último mês.",
  "tela3.erro-frase-repetir": "Nos 4 testes recentes, repetir o último mês errou em média {erro}.",
  "tela3.acertos": "A faixa provável acertou {n} de {total} casos.",
  "tela3.titulo-qualidade": "Como saber se a projeção é boa",
  "tela3.qualidade-texto":
    "Antes de aparecer aqui, a projeção foi testada em meses que já aconteceram, como se o resultado ainda não fosse conhecido. O teste compara a projeção com o jeito mais simples de prever, repetir o último mês. Quando ela erra menos que isso, vale a pena olhar para ela.",
  "tela3.aviso-poucos-testes":
    "Poucos testes: a tela mostra 4 dos 16, e uma diferença pequena pode ser acaso.",
  "tela3.aviso-mudanca-de-nivel":
    "Nesta série, a carteira mudou de patamar dentro dos testes, e o erro mede essa mudança, e não o método.",
  "tela3.aviso-meta": "A projeção é estatística, e não meta nem expectativa do Banco Central.",
  "tela3.aviso-soma":
    "As projeções não somam entre si: o Brasil não é a soma das UFs nem das modalidades.",

  "modalidade-curta.01": "Adiantamentos",
  "modalidade-curta.02": "Empréstimos",
  "modalidade-curta.03": "Direitos creditórios",
  "modalidade-curta.04": "Financiamentos",
  "modalidade-curta.05": "Exportação",
  "modalidade-curta.06": "Importação",
  "modalidade-curta.07": "Interveniência",
  "modalidade-curta.08": "Rurais",
  "modalidade-curta.09": "Imobiliários",
  "modalidade-curta.10": "Títulos e valores",
  "modalidade-curta.11": "Infraestrutura",
  "modalidade-curta.12": "Arrendamento",
  "modalidade-curta.13": "Outros créditos",
});
