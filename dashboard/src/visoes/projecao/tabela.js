/**
 * PT: As tabelas da Tela 3 (#72): a da série inteira, uma das formas de ver
 *     o palco, com o CSV dos mesmos números (RF-G06); e a da projeção mês a
 *     mês, no cartão da esquerda.
 * EN: Screen 3's tables: the whole series as a stage form, with its CSV,
 *     and the month-by-month projection in the left card.
 */

import { botao } from "../../componentes/botao.js";
import { tabela } from "../../componentes/tabela.js";
import { baixarCsv, montarCsv, numeroDoCsv } from "../../dados/csv.js";
import { elemento } from "../../dom.js";
import { dataBase, mesCurto, numero, reais } from "../../formatos.js";
import { t } from "../../textos/index.js";

/** @typedef {import("./dados.js").SerieDaProjecao} SerieDaProjecao */
/** @typedef {import("./dados.js").MesProjetado} MesProjetado */

/**
 * @typedef {object} LinhaDaTabela
 * @property {string} mes `aaaa-mm-dd`
 * @property {number | null} realizado
 * @property {MesProjetado | null} projetado
 */

/**
 * PT: Uma linha por mês: os realizados, depois os projetados.
 * EN: One row per month: actuals, then projected months.
 *
 * @param {SerieDaProjecao} serie
 * @returns {LinhaDaTabela[]}
 */
export function linhasDaTabela(serie) {
  return [
    ...serie.meses.map((mes, i) => ({ mes, realizado: serie.valores[i], projetado: null })),
    ...serie.projetados.map((p) => ({ mes: p.mes, realizado: null, projetado: p })),
  ];
}

/**
 * PT: A faixa provável escrita, de um limite a outro.
 * EN: The band, written from one bound to the other.
 *
 * @param {MesProjetado} p
 * @returns {string}
 */
export function faixaEscrita(p) {
  return t("tela3.faixa", { de: reais(p.inferior, 2), ate: reais(p.superior, 2) });
}

/** @type {readonly [number, string][]} */
const UNIDADES = Object.freeze([
  [1e12, "tri"],
  [1e9, "bi"],
  [1e6, "mi"],
  [1e3, "mil"],
]);

/**
 * PT: A unidade de um valor e as casas que cabem na coluna estreita: duas
 *     abaixo de 100 na unidade, como "2,93 tri", e uma acima, como "185,6 bi".
 * EN: A value's unit and the decimals that fit the narrow column.
 *
 * @param {number} valor
 * @returns {{ divisor: number, unidade: string, casas: number }}
 */
function unidadeDe(valor) {
  const [divisor, unidade] = UNIDADES.find(([d]) => Math.abs(valor) >= d) ?? [1, ""];
  return { divisor, unidade, casas: Math.abs(valor) / divisor >= 100 ? 1 : 2 };
}

/**
 * PT: Um valor em reais para a coluna estreita do cartão da esquerda.
 * EN: A value in reais for the narrow left card.
 *
 * @param {number} valor
 * @returns {string}
 */
export function reaisCurtos(valor) {
  return reais(valor, unidadeDe(valor).casas);
}

/**
 * PT: A faixa provável curta, com a unidade uma vez só, como "2,88 a 2,97
 *     tri", para caber na coluna estreita do cartão da esquerda. A unidade e
 *     as casas são as do limite superior.
 * EN: The short band, unit written once, for the narrow left card.
 *
 * @param {MesProjetado} p
 * @returns {string}
 */
export function faixaCurta(p) {
  const { divisor, unidade, casas } = unidadeDe(p.superior);
  const de = numero(p.inferior / divisor, casas);
  const ate = `${numero(p.superior / divisor, casas)}${unidade ? ` ${unidade}` : ""}`;
  return t("tela3.faixa", { de, ate });
}

/**
 * PT: O CSV, com os números crus, em reais inteiros, como no arquivo.
 * EN: The CSV with raw numbers in whole reais.
 *
 * @param {SerieDaProjecao} serie
 * @returns {string}
 */
export function csv(serie) {
  /** @type {[string, (linha: LinhaDaTabela) => string][]} */
  const colunas = [
    [t("tela3.coluna-mes"), (l) => l.mes],
    [t("tela3.coluna-realizado"), (l) => numeroDoCsv(l.realizado, 0)],
    [t("tela3.coluna-projecao"), (l) => numeroDoCsv(l.projetado?.valor ?? null, 0)],
    [t("tela3.coluna-inferior"), (l) => numeroDoCsv(l.projetado?.inferior ?? null, 0)],
    [t("tela3.coluna-superior"), (l) => numeroDoCsv(l.projetado?.superior ?? null, 0)],
  ];
  return montarCsv(colunas, linhasDaTabela(serie));
}

/**
 * PT: O botão que baixa o CSV da série inteira.
 * EN: The button that downloads the whole series as CSV.
 *
 * @param {SerieDaProjecao} serie
 * @param {string} arquivo
 * @returns {HTMLButtonElement}
 */
export function botaoDoCsv(serie, arquivo) {
  return botao({
    texto: t("tela1.baixar-csv"),
    variante: "secundario",
    icone: "download",
    aoClicar: () => baixarCsv(csv(serie), arquivo),
  });
}

/**
 * PT: A tabela da série inteira, do mês mais recente para o mais antigo,
 *     com a projeção em cima.
 * EN: The whole-series table, newest first, projection on top.
 *
 * @param {SerieDaProjecao} serie
 * @param {string} legenda
 * @returns {HTMLDivElement}
 */
export function tabelaDaSerie(serie, legenda) {
  const conteudo = tabela({
    legenda,
    colunas: [
      { titulo: t("tela3.coluna-mes"), celula: (l) => dataBase(l.mes) },
      {
        titulo: t("tela3.coluna-realizado"),
        tipo: "numero",
        celula: (l) => (l.realizado === null ? "–" : reais(l.realizado, 2)),
      },
      {
        titulo: t("tela3.coluna-projecao"),
        tipo: "numero",
        celula: (l) => (l.projetado ? reais(l.projetado.valor, 2) : "–"),
      },
      {
        titulo: t("tela3.coluna-faixa"),
        tipo: "numero",
        celula: (l) => (l.projetado ? faixaEscrita(l.projetado) : "–"),
      },
    ],
    linhas: linhasDaTabela(serie).reverse(),
  });
  return /** @type {HTMLDivElement} */ (
    elemento(
      "div",
      {
        classe: "visao__tabela",
        atributos: { tabindex: "0", role: "region", "aria-label": legenda },
      },
      [conteudo],
    )
  );
}

/**
 * PT: A projeção mês a mês do cartão da esquerda: o mês, o valor e a faixa.
 * EN: The left card's month-by-month projection.
 *
 * @param {MesProjetado[]} projetados
 * @returns {HTMLTableElement}
 */
export function tabelaMesAMes(projetados) {
  const cabecalho = elemento("tr", {}, [
    elemento("th", { texto: t("tela3.coluna-mes"), atributos: { scope: "col" } }),
    elemento("th", { texto: t("tela3.coluna-projecao"), atributos: { scope: "col" } }),
    elemento("th", { texto: t("tela3.coluna-faixa"), atributos: { scope: "col" } }),
  ]);
  const linhas = projetados.map((p) =>
    elemento("tr", {}, [
      elemento("th", { texto: mesCurto(p.mes), atributos: { scope: "row" } }),
      elemento("td", { texto: reaisCurtos(p.valor) }),
      elemento("td", { texto: faixaCurta(p) }),
    ]),
  );
  return /** @type {HTMLTableElement} */ (
    elemento("table", { classe: "projecao__mes-a-mes" }, [
      elemento("caption", { classe: "visualmente-oculto", texto: t("tela3.mes-a-mes") }),
      elemento("thead", {}, [cabecalho]),
      elemento("tbody", {}, linhas),
    ])
  );
}
