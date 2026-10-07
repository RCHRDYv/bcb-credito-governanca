/**
 * PT: Tela 4: a recomendação (#71, ADR 0014).
 *
 *     A matriz espaço contra risco do `mrt_decisao`, no palco em tela única
 *     das Telas 1 a 3 (ADR 0022), aprovada na revisão de 2026-10-06. A tela
 *     segue a filosofia do dashboard: o visual vem antes do texto, e o texto
 *     só diz o que o gráfico não mostra.
 *     1. **À esquerda:** a forma de ver, matriz ou tabela, e o custo de errar
 *        nas duas direções, em dois números, com a fronteira do dado logo
 *        abaixo, em quatro linhas curtas.
 *     2. **No centro, a matriz:** cada bola é uma célula de UF e modalidade, e
 *        o tamanho é a carteira PJ. Os eixos ficam na faixa onde estão quase
 *        todas as células, e as poucas de fora viram setas na borda. Ou a
 *        tabela das células, com o CSV (RF-G06).
 *     3. **À direita:** a carteira PJ por quadrante, em barras, e as células
 *        que ficaram fora da matriz, numa linha (RF-403).
 *
 * EN: Screen 4: the recommendation. Same single-screen stage: the cost of
 *     being wrong and the data limits on the left; the bubble matrix, sized
 *     by portfolio, or the table in the centre; portfolio by quadrant and the
 *     cells left out on the right.
 */

import { controleSegmentado } from "../../componentes/controle-segmentado.js";
import { etiquetaDeQuadrante } from "../../componentes/etiqueta-de-quadrante.js";
import { elemento } from "../../dom.js";
import { Filtros } from "../../estado/filtros.js";
import { dataBase, reais, taxa } from "../../formatos.js";
import { cartaoDeGrafico, erroDoGrafico } from "../../graficos/cartao.js";
import { graficos } from "../../graficos/sob-demanda.js";
import { t } from "../../textos/index.js";
import {
  celulasAvaliadas,
  custoDeErrar,
  foraDaMatriz,
  maiorErroDaReconstrucao,
  resumoPorQuadrante,
} from "./dados.js";
import { botaoDoCsv, tabelaDaTela } from "./tabela.js";
import "../palco.css";
import "./recomendacao.css";

/** @typedef {import("./carga.js").DadosDaTela} DadosDaTela */
/** @typedef {import("./dados.js").Celula} Celula */
/** @typedef {import("./dados.js").ResumoDoQuadrante} ResumoDoQuadrante */
/** @typedef {import("../../graficos/grafico.js").Grafico} Grafico */

/** @typedef {"matriz" | "tabela"} Forma */

/**
 * PT: Os limites dos eixos da matriz: 0,25 a 4 vezes a mediana, e 2 p.p. para
 *     cada lado do país. Em jul/2026, 90% das células avaliadas ficam entre
 *     -1 e +1 p.p., e seis passam de 2 p.p. (decidido em 2026-10-06).
 * EN: Matrix axis limits; the few cells beyond them become edge arrows.
 */
const LIMITES = /** @type {const} */ ({ espaco: [0.25, 4], risco: [-2, 2] });

/** PT: as marcas da legenda do tamanho, em reais / EN: size legend marks */
const MARCAS_DO_TAMANHO = [1e9, 10e9, 100e9];

/** @type {Record<import("../../componentes/etiqueta-de-quadrante.js").Quadrante, string>} */
const DO_MART = {
  entrar: "entrar",
  observar: "observar",
  "nao-entrar": "não entrar",
  manter: "manter",
};

/**
 * PT: Monta a Tela 4 no elemento. Devolve a função que desmonta a tela.
 * EN: Builds Screen 4; returns the teardown.
 *
 * @param {HTMLElement} el
 * @param {DadosDaTela} dados
 * @returns {() => void}
 */
export function render(el, dados) {
  const { decisao, erro, corte } = dados;
  const celulas = celulasAvaliadas(decisao);
  const resumo = resumoPorQuadrante(celulas);
  const custo = custoDeErrar(resumo);
  const fora = foraDaMatriz(decisao);
  const data = dataBase(decisao.data_base);
  const anterior = String(decisao.colunas.data_base_anterior[0]);
  const janela = t("tela4.janela", { de: dataBase(anterior), ate: data });
  const fonte = t("tela4.fonte");

  /** @type {Filtros<{ forma: Forma }>} */
  const filtros = new Filtros({ forma: /** @type {Forma} */ ("matriz") });

  // ------------------------------------------------------------ esquerda

  const controleDaForma = controleSegmentado({
    rotulo: t("tela4.forma"),
    opcoes: [
      { valor: "matriz", texto: t("tela4.matriz") },
      { valor: "tabela", texto: t("tela1.tabela") },
    ],
    valor: filtros.valores.forma,
    aoMudar: (valor) => filtros.definir({ forma: /** @type {Forma} */ (valor) }),
  });

  const numero = (/** @type {number} */ valor, /** @type {string} */ rotulo) =>
    elemento("div", { classe: "recomendacao__custo" }, [
      elemento("p", { classe: "recomendacao__custo-valor", texto: reais(valor) }),
      elemento("p", { classe: "recomendacao__custo-rotulo", texto: rotulo }),
    ]);
  const limites = [
    t("tela4.limite-lucro"),
    t("tela4.limite-instituicao"),
    t("tela4.limite-local"),
    t("tela4.limite-empresas", { erro: taxa(maiorErroDaReconstrucao(erro), 1) }),
  ];
  const cartaoDoCusto = cartaoDeGrafico(
    {
      titulo: t("tela4.titulo-custo"),
      dataBase: data,
      fonte: t("tela4.ordem-de-grandeza"),
      nivel: "h2",
    },
    [
      numero(custo.naoEntrar, t("tela4.custo-nao-entrar")),
      numero(custo.risco, t("tela4.custo-risco")),
      elemento("div", { classe: "recomendacao__limites" }, [
        elemento("h3", { classe: "recomendacao__subtitulo", texto: t("tela4.titulo-limites") }),
        elemento(
          "ul",
          {},
          limites.map((texto) => elemento("li", { texto })),
        ),
      ]),
    ],
  );
  const idDoTitulo = /** @type {HTMLElement} */ (
    cartaoDoCusto.querySelector(".cartao-grafico__titulo")
  ).id;

  // ------------------------------------------------------------ palco

  const formaEl = elemento("div", { classe: "visao__forma" });
  const palco = elemento(
    "div",
    { classe: "visao__palco", atributos: { role: "region", "aria-labelledby": idDoTitulo } },
    [formaEl],
  );
  /** @type {Grafico | null} */
  let graficoDaMatriz = null;
  let pedido = 0;

  const desenharPalco = async () => {
    pedido += 1;
    const meu = pedido;
    graficoDaMatriz?.destruir();
    graficoDaMatriz = null;
    formaEl.className = `visao__forma visao__forma--${filtros.valores.forma}`;
    // PT: a tabela pede largura e toma a coluna da direita, como nas Telas 1 e 2
    // EN: the table needs width and takes the right column, as on Screens 1 and 2
    raiz.classList.toggle("visao--forma-larga", filtros.valores.forma === "tabela");
    if (filtros.valores.forma === "tabela") {
      const legenda = t("tela4.legenda-tabela", { de: dataBase(anterior), ate: data });
      formaEl.replaceChildren(
        elemento("div", { classe: "visao__acoes" }, [
          botaoDoCsv(celulas, `recomendacao-credito-pj-${decisao.data_base}.csv`),
        ]),
        tabelaDaTela(celulas, legenda),
      );
      return;
    }
    const lugar = elemento("div", { classe: "recomendacao__matriz" });
    formaEl.replaceChildren(lugar);
    try {
      const { matriz } = await graficos();
      if (meu !== pedido) return;
      const grafico = await matriz(lugar, {
        celulas: celulas.map((c) => ({
          uf: c.uf,
          modalidade: c.modalidade,
          indice_de_espaco: c.indiceDeEspaco,
          desvio_do_risco: c.desvioDoRisco,
          quadrante: DO_MART[c.quadrante],
          tamanho: c.carteira,
        })),
        tamanho: {
          rotulo: t("tela4.tamanho"),
          formatar: (v) => reais(v, 0),
          marcas: MARCAS_DO_TAMANHO,
        },
        limites: { espaco: [...LIMITES.espaco], risco: [...LIMITES.risco] },
      });
      if (meu !== pedido) {
        grafico.destruir();
        return;
      }
      graficoDaMatriz = grafico;
    } catch {
      if (meu === pedido) formaEl.replaceChildren(erroDoGrafico(t("tela2.serie-erro")));
    }
  };

  // ------------------------------------------------------------ direita

  const maior = Math.max(...resumo.map((r) => r.carteira));
  const barras = elemento(
    "ul",
    { classe: "recomendacao__barras" },
    resumo.map((r) => {
      const barra = elemento("span", {
        classe: `recomendacao__barra recomendacao__barra--${r.quadrante}`,
        atributos: { "aria-hidden": "true" },
      });
      barra.style.inlineSize = `${(100 * r.carteira) / maior}%`;
      return elemento("li", {}, [
        etiquetaDeQuadrante(r.quadrante),
        elemento("span", { classe: "recomendacao__trilho" }, [barra]),
        elemento("span", { classe: "recomendacao__valor", texto: reais(r.carteira) }),
        elemento("span", {
          classe: "recomendacao__celulas",
          texto: t("tela4.celulas", { n: String(r.celulas) }),
        }),
      ]);
    }),
  );
  const abaixo = fora.find((f) => f.motivo.startsWith("carteira abaixo"))?.celulas ?? 0;
  const total = fora.reduce((s, f) => s + f.celulas, 0);
  const cartaoDosQuadrantes = cartaoDeGrafico(
    { titulo: t("tela4.titulo-quadrantes"), dataBase: janela, fonte, nivel: "h2" },
    [
      barras,
      elemento("p", {
        classe: "recomendacao__fora",
        texto: t("tela4.fora", {
          n: String(total),
          soma: reais(fora.reduce((s, f) => s + f.carteira, 0)),
          abaixo: String(abaixo),
          corte: reais(corte),
          poucas: String(total - abaixo),
        }),
      }),
    ],
  );

  // ------------------------------------------------------------ montagem

  const raiz = elemento("div", { classe: "visao visao--palco visao--recomendacao" }, [
    elemento("h1", { classe: "visualmente-oculto", texto: t("tela4.titulo") }),
    elemento("div", { classe: "visao__lado visao__lado--esquerdo" }, [
      elemento("div", { classe: "visao__filtros" }, [controleDaForma]),
      elemento("div", { classe: "visao__sobre-o-territorio" }, [cartaoDoCusto]),
    ]),
    palco,
    elemento("div", { classe: "visao__lado visao__lado--direito" }, [cartaoDosQuadrantes]),
  ]);
  el.replaceChildren(raiz);
  void desenharPalco();

  const pararDeOuvir = filtros.aoMudar(() => void desenharPalco());

  return () => {
    pararDeOuvir();
    pedido += 1;
    graficoDaMatriz?.destruir();
  };
}
