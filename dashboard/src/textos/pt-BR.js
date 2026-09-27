/**
 * PT: Todos os textos da interface, em português do Brasil.
 *
 *     Nenhum componente escreve texto fixo: ele pede o texto pela chave, com a
 *     função `t()` de `./index.js`. Quando o inglês entrar, ele vira um arquivo
 *     irmão deste, com as mesmas chaves, sem mexer em componente nenhum
 *     (ADR 0017, decisão 6; requisito RNF-13).
 *
 *     As chaves são planas e agrupadas pelo prefixo: `produto.`, `pagina.` e
 *     `inicio.`. "Crédito PJ" é o nome provisório do produto, até a decisão
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
  "inicio.titulo": "Onde crescer em crédito para empresas, e onde o risco está piorando",
  "inicio.em-construcao": "As visões do dashboard estão em construção.",

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
    "Cada paleta tem um papel. A categórica diz qual série é qual; a sequencial diz quanto; a divergente diz para que lado de uma referência. As faixas de baixo mostram como cada paleta aparece para quem tem daltonismo, pela simulação de Machado, Oliveira e Fernandes (2009).",
  "catalogo.paleta-categorica": "Categórica",
  "catalogo.paleta-sequencial": "Sequencial",
  "catalogo.paleta-divergente": "Divergente",
  "catalogo.sem-daltonismo": "Sem daltonismo",
  "catalogo.protanopia": "Protanopia",
  "catalogo.deuteranopia": "Deuteranopia",
  "catalogo.tritanopia": "Tritanopia",

  "catalogo.graficos": "Gráficos",
  "catalogo.graficos-explicacao":
    "Os componentes de gráfico, com dado real do projeto. Cada cartão traz só o título e a data-base com a fonte, sem conclusão escrita. Passe o mouse sobre um elemento para ver os números.",
  "catalogo.fonte-dos-exemplos": "SCR.data, do Banco Central",
  "catalogo.exemplo-mapa": "Carteira PJ por empresa ativa em Empréstimos, por UF",
  "catalogo.exemplo-cartograma-divergente":
    "Variação da inadimplência contra a do país em Empréstimos, por UF",
  "catalogo.exemplo-matriz": "Espaço contra risco, por UF e modalidade",
  "catalogo.exemplo-serie": "Taxa de inadimplência PJ no país",
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
  "grafico.acima-do-pais": "Acima do país",
  "grafico.abaixo-do-pais": "Abaixo do país",
  "grafico.igual-ao-pais": "Igual ao país",

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
});
