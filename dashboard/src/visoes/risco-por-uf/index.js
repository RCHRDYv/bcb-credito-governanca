/**
 * PT: Tela 2: onde o risco está piorando (#70, pergunta Q07).
 *
 *     O risco piora quando a inadimplência da célula sobe mais, em seis
 *     meses, que a da mesma modalidade no país (ADR 0014, decisão 3). A
 *     disposição é a da Tela 1, no modelo "Palco em tela única" (ADR 0022),
 *     aprovada no mockup de 2026-10-06:
 *     1. **À esquerda, os filtros:** a modalidade, sem "todas", porque a taxa
 *        não se soma entre modalidades, e a forma de ver o território.
 *     2. **À esquerda, embaixo, o que o território mostra:** o título, a
 *        janela e a fonte, o resumo do país, os dois números de atraso
 *        (RF-202) e as ressalvas, inclusive a da mudança de critério do
 *        ativo problemático quando a janela a cruza (RF-203).
 *     3. **No centro, o território,** em quatro formas: o mapa ou a grade,
 *        pintados por quanto a taxa subiu a mais que no país, com o marcador
 *        de alerta antecipado; a matriz da mesma conta por UF e modalidade; e
 *        a tabela, com o CSV (RF-G06).
 *     4. **À direita, o custo do risco** das UFs que pioraram mais que o
 *        país, com a ressalva de que não é perda (ADR 0014, decisão 5).
 *     5. **À direita, embaixo, o ranking** dessas UFs. Com uma UF escolhida,
 *        o painel dela toma a coluna inteira, com a série mensal da carteira
 *        inadimplida e do ativo problemático.
 *
 *     O estado mora num `Filtros` (ADR 0017), como na Tela 1.
 *
 * EN: Screen 2: where risk is getting worse. Same single-screen stage as
 *     Screen 1: filters and the territory summary on the left; the map, grid,
 *     heatmap or table colored by the change against the country in the
 *     centre; the risk cost and the ranking on the right, where the chosen
 *     state's panel, with its monthly series, takes the whole column.
 */

import { aviso } from "../../componentes/aviso.js";
import { campoDeSelecao } from "../../componentes/campo-de-selecao.js";
import { controleSegmentado } from "../../componentes/controle-segmentado.js";
import { definicao } from "../../componentes/definicao.js";
import { vazio } from "../../componentes/estados.js";
import { painelDeDetalhe } from "../../componentes/painel-de-detalhe.js";
import { carregar } from "../../dados/carregar.js";
import { definicaoDaColuna, definicaoDaModalidade } from "../../dados/definicoes.js";
import { elemento } from "../../dom.js";
import { Filtros } from "../../estado/filtros.js";
import { dataBase, pontos, reais, taxa } from "../../formatos.js";
import { areaDoGrafico, cartaoDeGrafico } from "../../graficos/cartao.js";
import { numeroDeDestaque } from "../../graficos/numero-de-destaque.js";
import { graficos } from "../../graficos/sob-demanda.js";
import { ufPelaSigla } from "../../graficos/ufs.js";
import { t } from "../../textos/index.js";
import { classesDoRisco, legendaDoRisco } from "./cor.js";
import {
  celulasDaMatriz,
  dataDaQuebra,
  ranking as itensDoRanking,
  janelaCruzaAQuebra,
  linhas,
  modalidades,
  resumo,
  serieDaUf,
  ufsPorCarteira,
} from "./dados.js";
import { perfilDaUf, prepararSerie } from "./perfil.js";
import { botaoDoCsv, tabelaDaTela } from "./tabela.js";
import "../palco.css";
import "./risco-por-uf.css";

/** @typedef {import("./carga.js").DadosDaTela} DadosDaTela */
/** @typedef {import("./dados.js").LinhaDoRisco} LinhaDoRisco */
/** @typedef {import("../../textos/index.js").ChaveDeTexto} ChaveDeTexto */
/** @typedef {import("../../componentes/painel-de-detalhe.js").ItemDoDetalhe} ItemDoDetalhe */
/** @typedef {import("../../graficos/grafico.js").Grafico} Grafico */

/** @typedef {"mapa" | "grade" | "matriz" | "tabela"} Forma */

/**
 * @typedef {object} ValoresDosFiltros
 * @property {string} modalidade O código da modalidade / modality code
 * @property {string | null} uf A UF escolhida / chosen state
 * @property {Forma} desenho A forma de ver o território / territory form
 */

/**
 * @typedef {object} FormaDesenhada
 * @property {(chaves: string[]) => void} atualizar
 * @property {() => void} destruir
 */

/** PT: a mesma largura estreita da Tela 1 / EN: same narrow width as Screen 1 */
const TELA_ESTREITA = "(max-width: 671px)";

/** PT: as formas que pedem largura, como na Tela 1 / EN: wide forms */
const FORMAS_LARGAS = new Set(["matriz", "tabela"]);

/** @type {Record<Exclude<LinhaDoRisco["situacao"], "comparada">, ChaveDeTexto>} */
const MOTIVO = {
  "abaixo-do-corte": "tela1.motivo-abaixo-do-corte",
  "poucas-ufs": "tela1.motivo-poucas-ufs",
  "sem-carteira": "tela1.motivo-sem-carteira",
};

/**
 * PT: Uma área de rolagem com nome, que recebe foco para quem usa o teclado.
 * EN: A named scroll area, focusable for keyboard users.
 *
 * @param {HTMLElement} el
 * @param {string} classe
 * @param {string} rotulo
 */
function comRolagem(el, classe, rotulo) {
  el.classList.add(classe);
  el.setAttribute("tabindex", "0");
  el.setAttribute("role", "region");
  el.setAttribute("aria-label", rotulo);
}

/**
 * PT: Monta a Tela 2 no elemento. Devolve a função que desmonta a tela e
 *     libera os gráficos, para a navegação chamar ao trocar de visão.
 * EN: Builds Screen 2; returns the teardown the router calls.
 *
 * @param {HTMLElement} el
 * @param {DadosDaTela} dados
 * @returns {() => void}
 */
export function render(el, dados) {
  const { decisao, ontologia, meses } = dados;
  const estreita = window.matchMedia(TELA_ESTREITA);
  const todasAsModalidades = modalidades(decisao);
  const inicial = (todasAsModalidades.find((m) => m.comparadas > 0) ?? todasAsModalidades[0])
    .codigo;
  /** @type {Filtros<ValoresDosFiltros>} */
  const filtros = new Filtros({
    modalidade: inicial,
    uf: /** @type {string | null} */ (null),
    desenho: /** @type {Forma} */ (estreita.matches || !dados.malha ? "grade" : "mapa"),
  });

  const data = dataBase(decisao.data_base);
  const anterior = String(decisao.colunas.data_base_anterior[0]);
  const janela = t("tela2.janela", { de: dataBase(anterior), ate: data });
  const quebra = dataDaQuebra(ontologia);
  const nomes = new Map(todasAsModalidades.map((m) => [m.codigo, m.nome]));
  const classes = classesDoRisco();
  const fonte = t("tela2.fonte");
  const corte = reais(dados.corte, 0);
  const m = { meses: String(meses) };

  const recorte = () => nomes.get(filtros.valores.modalidade) ?? filtros.valores.modalidade;
  const linhasAtuais = () => linhas(decisao, filtros.valores.modalidade);
  const motivo = (/** @type {LinhaDoRisco} */ linha) =>
    linha.situacao === "comparada" ? "" : t(MOTIVO[linha.situacao], { corte });

  /**
   * @param {string} rotulo
   * @param {string} coluna
   * @returns {Node | undefined}
   */
  const comDefinicao = (rotulo, coluna) => {
    const origem = definicaoDaColuna(ontologia, "decisao.json", coluna);
    return origem ? definicao({ rotulo, definicao: origem }) : undefined;
  };

  const opcoesDaTabela = () => ({
    linhasDoRisco: linhasAtuais(),
    escolhida: filtros.valores.uf,
    legenda: t("tela2.legenda-tabela", {
      modalidade: recorte(),
      de: dataBase(anterior),
      ate: data,
    }),
    meses,
    situacao: motivo,
    arquivo: `risco-pj-por-uf-${filtros.valores.modalidade}-${decisao.data_base}.csv`,
  });

  // ------------------------------------------------------------ filtros

  const apoioDaModalidade = elemento("span", { classe: "visao__apoio" });
  const atualizarApoio = () => {
    const origem = definicaoDaModalidade(ontologia, filtros.valores.modalidade);
    apoioDaModalidade.replaceChildren(
      ...(origem ? [definicao({ rotulo: recorte(), definicao: origem })] : []),
    );
  };
  const seletor = campoDeSelecao({
    rotulo: t("tela1.filtro-modalidade"),
    opcoes: todasAsModalidades.map((modalidade) => ({
      valor: modalidade.codigo,
      texto:
        modalidade.comparadas > 0
          ? modalidade.nome
          : t("tela1.opcao-sem-comparacao", { nome: modalidade.nome }),
    })),
    valor: inicial,
    aoMudar: (valor) => filtros.definir({ modalidade: valor }),
    apoio: apoioDaModalidade,
  });
  const selecao = /** @type {HTMLSelectElement} */ (seletor.querySelector("select"));
  const controleDaForma = controleSegmentado({
    rotulo: t("tela1.desenho"),
    opcoes: [
      ...(dados.malha ? [{ valor: "mapa", texto: t("tela1.mapa") }] : []),
      { valor: "grade", texto: t("tela1.grade") },
      { valor: "matriz", texto: t("tela1.matriz") },
      { valor: "tabela", texto: t("tela1.tabela") },
    ],
    valor: filtros.valores.desenho,
    aoMudar: (valor) => filtros.definir({ desenho: /** @type {Forma} */ (valor) }),
  });
  const barra = elemento("div", { classe: "visao__filtros" }, [seletor, controleDaForma]);

  // ------------------------------------------------------------ território

  const tituloDoTerritorio = () =>
    filtros.valores.desenho === "matriz"
      ? t("tela2.titulo-matriz")
      : t("tela2.titulo-territorio", { ...m, modalidade: recorte() });

  const resumoDoTerritorio = elemento("dl", { classe: "visao__resumo" });
  const desenharResumo = () => {
    const r = resumo(linhasAtuais());
    /** @type {ItemDoDetalhe[]} */
    const itens = [
      {
        chave: t("tela2.resumo-taxa-pais"),
        valor: r.taxaPais === null ? "–" : taxa(r.taxaPais, 1),
        apoio: comDefinicao(t("tela2.resumo-taxa-pais"), "taxa_pais"),
      },
      {
        chave: t("tela2.resumo-variacao-pais", m),
        valor: r.variacaoPais === null ? "–" : pontos(r.variacaoPais),
        apoio: comDefinicao(t("tela2.resumo-variacao-pais", m), "variacao_taxa_pais"),
      },
      {
        chave: t("tela2.resumo-piorando"),
        valor: t("tela2.de", { n: String(r.piorando), total: String(r.comparadas) }),
      },
      {
        chave: t("tela2.resumo-alertas"),
        valor: String(r.alertas),
        apoio: comDefinicao(t("tela2.resumo-alertas"), "alerta_antecipado"),
      },
    ];
    resumoDoTerritorio.replaceChildren(
      ...itens.flatMap((item) => [
        elemento("dt", {}, [item.chave, ...(item.apoio ? [item.apoio] : [])]),
        elemento("dd", { texto: item.valor }),
      ]),
    );
  };

  // PT: os dois números de atraso, com a definição oficial a um clique (RF-202)
  // EN: the two arrears measures, with the official definition one click away
  const definicaoMensal = (/** @type {string} */ rotulo, /** @type {string} */ coluna) => {
    const origem = definicaoDaColuna(ontologia, "carteira_mensal_pj.json", coluna);
    return origem ? [definicao({ rotulo, definicao: origem })] : [];
  };
  const doisNumeros = elemento("div", { classe: "risco__dois-numeros" }, [
    elemento("p", { classe: "risco__dois-numeros-titulo", texto: t("tela2.dois-numeros") }),
    elemento("p", {}, [
      elemento("span", { classe: "risco__medida" }, [
        elemento("strong", { texto: t("tela2.inadimplida") }),
        ...definicaoMensal(t("tela2.inadimplida"), "carteira_inadimplencia"),
      ]),
      ` ${t("tela2.inadimplida-texto")}`,
    ]),
    elemento("p", {}, [
      elemento("span", { classe: "risco__medida" }, [
        elemento("strong", { texto: t("tela2.ativo-problematico") }),
        ...definicaoMensal(t("tela2.ativo-problematico"), "criterio_ativo_problematico"),
      ]),
      ` ${t("tela2.ativo-problematico-texto")}`,
    ]),
  ]);

  const cartaoTerritorio = cartaoDeGrafico(
    { titulo: tituloDoTerritorio(), dataBase: janela, fonte, nivel: "h2" },
    [
      resumoDoTerritorio,
      doisNumeros,
      ...(janelaCruzaAQuebra(anterior, decisao.data_base, quebra)
        ? [
            aviso({
              tipo: "atencao",
              texto: t("tela2.quebra-na-janela", {
                de: dataBase(anterior),
                ate: data,
                quebra: dataBase(/** @type {string} */ (quebra)),
              }),
              variante: "linha",
            }),
          ]
        : []),
      ...(dados.malha
        ? []
        : [aviso({ tipo: "atencao", texto: t("tela1.sem-malha"), variante: "linha" })]),
      aviso({ tipo: "informacao", texto: t("tela1.aviso-sede"), variante: "linha" }),
    ],
  );
  const idDoTitulo = /** @type {HTMLElement} */ (
    cartaoTerritorio.querySelector(".cartao-grafico__titulo")
  ).id;
  const territorio = elemento("div", { classe: "visao__sobre-o-territorio" }, [cartaoTerritorio]);
  const formaEl = elemento("div", { classe: "visao__forma" });
  formaEl.addEventListener("click", (evento) => {
    const botao = /** @type {HTMLElement} */ (evento.target).closest("[data-uf]");
    if (botao) filtros.definir({ uf: botao.getAttribute("data-uf") });
  });
  const palco = elemento(
    "div",
    { classe: "visao__palco", atributos: { role: "region", "aria-labelledby": idDoTitulo } },
    [formaEl],
  );

  /** @type {FormaDesenhada | null} */
  let atual = null;
  let geracao = 0;

  const dicaDaUf = (/** @type {string} */ sigla) => {
    const linha = linhasAtuais().find((l) => l.uf === sigla);
    if (!linha) return null;
    if (linha.contraOPais === null) return motivo(linha);
    const texto = t("tela2.contra-o-pais", { valor: pontos(linha.contraOPais) });
    return linha.alerta ? `${texto} · ${t("alerta-antecipado.nome")}` : texto;
  };
  const corDoTerritorio = () => {
    const linhasDoRisco = linhasAtuais();
    return {
      valores: Object.fromEntries(linhasDoRisco.map((l) => [l.uf, l.contraOPais])),
      classes,
      formatar: (/** @type {number} */ v) => pontos(v),
      rotuloSemValor: linhasDoRisco.some((l) => l.contraOPais === null)
        ? t("tela2.sem-comparacao")
        : undefined,
      marcadas: linhasDoRisco.filter((l) => l.alerta).map((l) => l.uf),
    };
  };

  /**
   * PT: O mapa ou a grade, que mudam de cor e de marcadores com a modalidade.
   * EN: The map or the tile grid, recolored and re-marked by modality.
   *
   * @param {"mapa" | "grade"} tipo
   * @returns {Promise<FormaDesenhada>}
   */
  const desenharUfs = async (tipo) => {
    const area = areaDoGrafico(tipo === "mapa" ? "grafico--mapa" : "grafico--cartograma");
    formaEl.replaceChildren(
      tipo === "mapa" ? area : elemento("div", { classe: "cartograma" }, [area]),
    );
    const opcoes = {
      ...corDoTerritorio(),
      dica: dicaDaUf,
      aoSelecionar: (/** @type {string} */ sigla) => filtros.definir({ uf: sigla }),
      selecionada: filtros.valores.uf,
      legenda: legendaDoRisco({ comMarca: true }),
    };
    const { cartograma, mapaPorUf, registrarMalha } = await graficos();
    let grafico;
    if (tipo === "mapa" && dados.malha) {
      registrarMalha(dados.malha);
      grafico = await mapaPorUf(area, opcoes);
    } else {
      grafico = await cartograma(area, opcoes);
    }
    return {
      atualizar: (chaves) => {
        if (chaves.includes("modalidade")) grafico.mudar(corDoTerritorio());
        if (chaves.includes("uf") || chaves.includes("modalidade")) {
          grafico.selecionar(filtros.valores.uf);
        }
      },
      destruir: () => grafico.destruir(),
    };
  };

  const modalidadesDaMatriz = todasAsModalidades
    .filter((modalidade) => modalidade.comparadas > 0)
    .map((modalidade) => ({
      chave: modalidade.codigo,
      rotulo: t(/** @type {ChaveDeTexto} */ (`modalidade-curta.${modalidade.codigo}`)),
    }));
  const ufsDaMatriz = ufsPorCarteira(decisao).map((sigla) => ({ chave: sigla, rotulo: sigla }));
  const celulasDaTela = celulasDaMatriz(decisao).map((c) => {
    const modalidade = nomes.get(c.codigo) ?? c.codigo;
    const uf = ufPelaSigla(c.uf).nome;
    return {
      uf: c.uf,
      codigo: c.codigo,
      valor: c.contraOPais,
      dica:
        c.contraOPais === null
          ? t("tela1.dica-celula-fora", { uf, modalidade })
          : t("tela2.dica-celula", { uf, modalidade, valor: pontos(c.contraOPais) }),
    };
  });

  /**
   * PT: A matriz de UF por modalidade, deitada no computador e de pé no
   *     celular, como na Tela 1.
   * EN: The state-by-modality heatmap, as on Screen 1.
   *
   * @returns {Promise<FormaDesenhada>}
   */
  const desenharMatriz = async () => {
    const deitada = !estreita.matches;
    const area = areaDoGrafico("grafico--matriz-de-calor");
    formaEl.replaceChildren(area);
    const selecionada = () => {
      const { uf, modalidade } = filtros.valores;
      return deitada ? { linha: modalidade, coluna: uf } : { linha: uf, coluna: modalidade };
    };
    const { matrizDeCalor } = await graficos();
    const grafico = await matrizDeCalor(area, {
      linhas: deitada ? modalidadesDaMatriz : ufsDaMatriz,
      colunas: deitada ? ufsDaMatriz : modalidadesDaMatriz,
      celulas: celulasDaTela.map((c) => ({
        linha: deitada ? c.codigo : c.uf,
        coluna: deitada ? c.uf : c.codigo,
        valor: c.valor,
        dica: c.dica,
      })),
      classes,
      rotuloSemValor: t("tela2.sem-comparacao"),
      legenda: legendaDoRisco({ comMarca: false }),
      aoSelecionar: (linha, coluna) =>
        filtros.definir(
          deitada ? { modalidade: linha, uf: coluna } : { uf: linha, modalidade: coluna },
        ),
      selecionada: selecionada(),
    });
    return {
      atualizar: (chaves) => {
        if (chaves.includes("uf") || chaves.includes("modalidade")) {
          grafico.selecionar(selecionada());
        }
      },
      destruir: () => grafico.destruir(),
    };
  };

  /**
   * PT: A tabela, com o download em CSV em cima, só nesta forma.
   * EN: The table, with the CSV download above it, in this form only.
   *
   * @returns {FormaDesenhada}
   */
  const desenharTabela = () => {
    const desenhar = () => {
      const topo = formaEl.querySelector(".visao__tabela")?.scrollTop ?? 0;
      const opcoes = opcoesDaTabela();
      const nova = tabelaDaTela(opcoes);
      formaEl.replaceChildren(
        elemento("div", { classe: "visao__acoes" }, [botaoDoCsv(opcoes)]),
        nova,
      );
      nova.scrollTop = topo;
    };
    desenhar();
    return { atualizar: desenhar, destruir: () => {} };
  };

  const desenharTerritorio = async () => {
    geracao += 1;
    const minha = geracao;
    atual?.destruir();
    atual = null;
    const tipo = filtros.valores.desenho;
    formaEl.className = `visao__forma visao__forma--${tipo}`;
    raiz.classList.toggle("visao--forma-larga", FORMAS_LARGAS.has(tipo));
    atualizarTitulos();
    const origem = cartaoTerritorio.querySelector(".cartao-grafico__origem");
    if (origem) {
      origem.textContent = `${janela} · ${tipo === "mapa" ? t("tela2.fonte-com-malha") : fonte}`;
    }
    const nova =
      tipo === "tabela"
        ? desenharTabela()
        : tipo === "matriz"
          ? await desenharMatriz()
          : await desenharUfs(tipo);
    if (minha !== geracao) {
      nova.destruir();
      return;
    }
    atual = nova;
  };

  const aoCruzarALargura = () => {
    if (filtros.valores.desenho === "matriz") void desenharTerritorio();
  };
  estreita.addEventListener("change", aoCruzarALargura);

  // ------------------------------------------------------------ custo do risco

  const corpoDoDestaque = elemento("div", { classe: "visao__oportunidade" });
  const cartaoDestaque = cartaoDeGrafico(
    {
      titulo: t("tela2.titulo-destaque", { modalidade: recorte() }),
      dataBase: data,
      fonte,
      nivel: "h2",
    },
    [corpoDoDestaque],
  );
  const vazioDaModalidade = () =>
    vazio({
      titulo: t("tela2.vazio-titulo"),
      texto: t("tela2.vazio-texto", { corte, minimo: String(dados.minimoDeUfs) }),
    });
  const vazioDaPiora = () =>
    vazio({ titulo: t("tela2.vazio-piora-titulo"), texto: t("tela2.vazio-piora-texto", m) });
  const desenharDestaque = () => {
    const r = resumo(linhasAtuais());
    corpoDoDestaque.replaceChildren(
      r.comparadas === 0
        ? vazioDaModalidade()
        : r.piorando === 0
          ? vazioDaPiora()
          : numeroDeDestaque({
              valor: reais(r.custo),
              rotulo:
                r.piorando === 1
                  ? t("tela2.destaque-rotulo-uma")
                  : t("tela2.destaque-rotulo", { n: String(r.piorando) }),
            }),
      aviso({ tipo: "informacao", texto: t("tela2.ressalva-perda"), variante: "linha" }),
    );
  };
  const destaqueEl = elemento("div", { classe: "visao__destaque" }, [cartaoDestaque]);

  // ------------------------------------------------------------ ranking

  const areaRanking = areaDoGrafico("grafico--ranking");
  const vazioDoRanking = elemento("div", { classe: "visao__vazio" });
  const notaDoRanking = elemento("p", { classe: "risco__nota" }, [
    elemento("span", { classe: "marcador-de-alerta", atributos: { "aria-hidden": "true" } }),
    `${t("alerta-antecipado.nome")} · ${t("tela2.nota-ranking")}`,
  ]);
  const cartaoRanking = cartaoDeGrafico(
    {
      titulo: t("tela2.titulo-ranking", { modalidade: recorte() }),
      dataBase: janela,
      fonte,
      nivel: "h2",
    },
    [areaRanking, vazioDoRanking, notaDoRanking],
  );
  const rolagemDoRanking = /** @type {HTMLElement} */ (
    cartaoRanking.querySelector(".cartao-grafico__corpo")
  );
  cartaoRanking.classList.add("cartao-grafico--preenche");
  comRolagem(rolagemDoRanking, "visao__rolagem", t("tela2.rolagem-do-ranking"));
  const mostrarVazio = () => {
    const r = resumo(linhasAtuais());
    const semItens = r.piorando === 0;
    areaRanking.hidden = semItens;
    notaDoRanking.hidden = semItens;
    vazioDoRanking.replaceChildren(
      ...(semItens ? [r.comparadas === 0 ? vazioDaModalidade() : vazioDaPiora()] : []),
    );
  };
  /** @type {import("../../graficos/ranking.js").GraficoDoRanking | null} */
  let graficoRanking = null;

  const mostrarNoRanking = (/** @type {string | null} */ sigla) => {
    const y = sigla && graficoRanking ? graficoRanking.posicaoDe(sigla) : null;
    if (y === null) return;
    rolagemDoRanking.scrollTo({ top: Math.max(0, y - rolagemDoRanking.clientHeight / 2) });
  };

  // ------------------------------------------------------------ painel

  const painel = painelDeDetalhe({
    dica: t("tela2.detalhe-dica"),
    aoFechar: () => filtros.definir({ uf: null }),
  });
  /** @type {Grafico | null} */
  let graficoDaSerie = null;
  let pedidoDaSerie = 0;

  /**
   * PT: Desenha a série da UF no painel, quando o arquivo mensal e o ECharts
   *     chegam. Um pedido que chega atrasado, depois de outra UF ou outra
   *     modalidade, é descartado.
   * EN: Draws the state's series once the monthly file and ECharts arrive,
   *     discarding late requests.
   *
   * @param {HTMLElement} lugar
   * @param {string} uf
   * @param {string} codigo
   */
  const desenharSerie = async (lugar, uf, codigo) => {
    pedidoDaSerie += 1;
    const meu = pedidoDaSerie;
    graficoDaSerie?.destruir();
    graficoDaSerie = null;
    try {
      const [mensal, { serieDeLinhas }] = await Promise.all([
        carregar("carteira_mensal_pj.json"),
        graficos(),
      ]);
      if (meu !== pedidoDaSerie) return;
      const serie = serieDaUf(mensal, uf, codigo);
      const area = prepararSerie(lugar, "pronta");
      if (!area) return;
      const primeiro = serie.meses[0];
      const ultimo = serie.meses.at(-1);
      const cruza =
        quebra !== null && primeiro < quebra && ultimo !== undefined && quebra <= ultimo;
      if (cruza) {
        lugar.append(
          aviso({
            tipo: "informacao",
            texto: t("tela2.quebra-na-serie", { quebra: dataBase(/** @type {string} */ (quebra)) }),
            variante: "linha",
          }),
        );
      }
      const grafico = await serieDeLinhas(area, {
        meses: serie.meses,
        linhas: [
          { nome: t("tela2.inadimplida"), valores: serie.inadimplencia },
          { nome: t("tela2.ativo-problematico"), valores: serie.ativoProblematico },
        ],
        formatar: (v) => taxa(v, 1),
        formatarEixo: (v) => taxa(v, 0),
        ...(cruza
          ? { marco: { mes: /** @type {string} */ (quebra), rotulo: t("tela2.quebra-marco") } }
          : {}),
        janela: { de: anterior, ate: decisao.data_base, rotulo: t("tela2.janela-rotulo", m) },
      });
      if (meu !== pedidoDaSerie) {
        grafico.destruir();
        return;
      }
      graficoDaSerie = grafico;
    } catch {
      if (meu === pedidoDaSerie) prepararSerie(lugar, "erro");
    }
  };

  const mostrarDetalhe = () => {
    const { uf } = filtros.valores;
    const linha = uf ? linhasAtuais().find((l) => l.uf === uf) : undefined;
    raiz.classList.toggle("visao--com-uf", Boolean(linha));
    if (!linha) {
      pedidoDaSerie += 1;
      graficoDaSerie?.destruir();
      graficoDaSerie = null;
      painel.limpar();
      return;
    }
    const { conteudo, serie } = perfilDaUf({
      linha,
      subtitulo: `${recorte()} · ${data}`,
      meses,
      nota: motivo(linha),
      comDefinicao,
    });
    painel.mostrar(conteudo);
    void desenharSerie(serie, linha.uf, filtros.valores.modalidade);
  };

  // ------------------------------------------------------------ montagem

  function atualizarTitulos() {
    for (const [cartao, titulo] of /** @type {[HTMLElement, string][]} */ ([
      [cartaoDestaque, t("tela2.titulo-destaque", { modalidade: recorte() })],
      [cartaoTerritorio, tituloDoTerritorio()],
      [cartaoRanking, t("tela2.titulo-ranking", { modalidade: recorte() })],
    ])) {
      const alvo = cartao.querySelector(".cartao-grafico__titulo");
      if (alvo) alvo.textContent = titulo;
    }
  }

  const raiz = elemento(
    "div",
    { classe: "visao visao--palco visao--painel-inteiro visao--risco-por-uf" },
    [
      elemento("h1", { classe: "visualmente-oculto", texto: t("tela2.titulo") }),
      elemento("div", { classe: "visao__lado visao__lado--esquerdo" }, [barra, territorio]),
      palco,
      elemento("div", { classe: "visao__lado visao__lado--direito" }, [
        destaqueEl,
        elemento("div", { classe: "visao__ranking" }, [cartaoRanking]),
        painel.elemento,
      ]),
    ],
  );
  el.replaceChildren(raiz);

  atualizarApoio();
  desenharResumo();
  desenharDestaque();
  mostrarVazio();
  mostrarDetalhe();
  void desenharTerritorio();

  // PT: o ranking se desenha quando o cartão aparece, como na Tela 1 (#89)
  // EN: the ranking draws when its card shows up, as on Screen 1
  let desmontada = false;
  let rankingPedido = false;
  const desenharRanking = async () => {
    if (rankingPedido) return;
    rankingPedido = true;
    const { ranking } = await graficos();
    const grafico = await ranking(areaRanking, {
      itens: itensDoRanking(linhasAtuais()),
      formatar: (v) => pontos(v),
      aoSelecionar: (sigla) => filtros.definir({ uf: sigla }),
    });
    if (desmontada) {
      grafico.destruir();
      return;
    }
    graficoRanking = grafico;
    if (filtros.valores.uf) grafico.selecionar(filtros.valores.uf);
  };
  const vigiaDoRanking =
    "IntersectionObserver" in window
      ? new IntersectionObserver((entradas) => {
          if (!entradas.some((entrada) => entrada.isIntersecting)) return;
          vigiaDoRanking?.disconnect();
          void desenharRanking();
        })
      : null;
  if (vigiaDoRanking) vigiaDoRanking.observe(cartaoRanking);
  else void desenharRanking();

  const pararDeOuvir = filtros.aoMudar((evento) => {
    const { chaves } = evento.detail;
    if (chaves.includes("modalidade")) {
      selecao.value = filtros.valores.modalidade;
      atualizarTitulos();
      atualizarApoio();
      desenharResumo();
      desenharDestaque();
      mostrarVazio();
      graficoRanking?.mudar({ itens: itensDoRanking(linhasAtuais()) });
    }
    if (chaves.includes("desenho")) void desenharTerritorio();
    else atual?.atualizar(chaves);
    if (chaves.includes("uf") || chaves.includes("modalidade")) {
      graficoRanking?.selecionar(filtros.valores.uf);
      mostrarNoRanking(filtros.valores.uf);
      mostrarDetalhe();
    }
  });

  return () => {
    desmontada = true;
    vigiaDoRanking?.disconnect();
    pararDeOuvir();
    estreita.removeEventListener("change", aoCruzarALargura);
    geracao += 1;
    pedidoDaSerie += 1;
    atual?.destruir();
    graficoRanking?.destruir();
    graficoDaSerie?.destruir();
  };
}
