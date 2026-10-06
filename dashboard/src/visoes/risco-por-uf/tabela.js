/**
 * PT: A tabela da Tela 2 (RF-G06), uma das formas do território, e o CSV
 *     dos mesmos números (#70).
 *
 *     A tabela mostra as 27 UFs, da maior piora contra o país para a menor,
 *     com as que ficam fora da comparação no fim, e o motivo. O alerta
 *     antecipado e o quadrante vão nas etiquetas do design system. O nome da
 *     UF é um botão, que escolhe a UF pelo teclado. O CSV leva os números
 *     crus, como nos arquivos do contrato.
 *
 * EN: Screen 2's table and its CSV: all 27 states by excess change, the
 *     early warning and quadrant as design-system tags, raw numbers in CSV.
 */

import { alertaAntecipado } from "../../componentes/alerta-antecipado.js";
import { botao } from "../../componentes/botao.js";
import { etiquetaDeQuadrante, nomeDoQuadrante } from "../../componentes/etiqueta-de-quadrante.js";
import { tabela } from "../../componentes/tabela.js";
import { baixarCsv, montarCsv, numeroDoCsv, textoDoCsv } from "../../dados/csv.js";
import { elemento } from "../../dom.js";
import { pontos, reais, taxa } from "../../formatos.js";
import { t } from "../../textos/index.js";
import { ordenar } from "./dados.js";

/** @typedef {import("./dados.js").LinhaDoRisco} LinhaDoRisco */

/**
 * @typedef {object} OpcoesDaTabela
 * @property {LinhaDoRisco[]} linhasDoRisco
 * @property {string | null} escolhida A UF escolhida / chosen state
 * @property {string} legenda O que a tabela mostra / caption
 * @property {number} meses A janela da tendência / trend window
 * @property {(linha: LinhaDoRisco) => string} situacao O motivo de quem fica fora / reason
 * @property {string} arquivo O nome do CSV / CSV file name
 */

/**
 * PT: O conteúdo do CSV, com os números crus: reais em reais inteiros e
 *     frações com seis casas, como nos arquivos do contrato.
 * EN: The CSV content with raw numbers, as in the contract files.
 *
 * @param {LinhaDoRisco[]} linhasDoRisco
 * @param {number} meses
 * @param {(linha: LinhaDoRisco) => string} situacao
 * @returns {string}
 */
export function csv(linhasDoRisco, meses, situacao) {
  const m = { meses: String(meses) };
  /** @type {[string, (linha: LinhaDoRisco) => string][]} */
  const colunas = [
    [t("tela1.coluna-uf"), (l) => textoDoCsv(l.nome)],
    [t("tela1.carteira-pj"), (l) => numeroDoCsv(l.carteira, 0)],
    [t("tela2.coluna-taxa"), (l) => numeroDoCsv(l.taxa, 6)],
    [t("tela2.coluna-taxa-anterior", m), (l) => numeroDoCsv(l.taxaAnterior, 6)],
    [t("tela2.coluna-variacao", m), (l) => numeroDoCsv(l.variacao, 6)],
    [t("tela2.resumo-taxa-pais"), (l) => numeroDoCsv(l.taxaPais, 6)],
    [t("tela2.coluna-variacao-pais"), (l) => numeroDoCsv(l.variacaoPais, 6)],
    [t("tela2.coluna-contra-o-pais"), (l) => numeroDoCsv(l.contraOPais, 6)],
    [
      t("tela2.coluna-alerta"),
      (l) => (l.situacao === "comparada" ? t(l.alerta ? "tela2.sim" : "tela2.nao") : ""),
    ],
    [
      t("tela2.coluna-quadrante"),
      (l) => (l.quadrante ? textoDoCsv(nomeDoQuadrante(l.quadrante)) : ""),
    ],
    [t("tela2.coluna-custo"), (l) => numeroDoCsv(l.custoDoRisco, 0)],
    [t("tela1.coluna-situacao"), (l) => textoDoCsv(situacao(l))],
  ];
  return montarCsv(colunas, linhasDoRisco);
}

/**
 * PT: O botão que baixa os números da modalidade em CSV.
 * EN: The button that downloads the modality's numbers as CSV.
 *
 * @param {OpcoesDaTabela} opcoes
 * @returns {HTMLButtonElement}
 */
export function botaoDoCsv(opcoes) {
  return botao({
    texto: t("tela1.baixar-csv"),
    variante: "secundario",
    icone: "download",
    aoClicar: () =>
      baixarCsv(csv(ordenar(opcoes.linhasDoRisco), opcoes.meses, opcoes.situacao), opcoes.arquivo),
  });
}

/**
 * PT: A tabela, numa área que rola por dentro e recebe foco pelo teclado.
 * EN: The table, in a focusable area that scrolls inside.
 *
 * @param {OpcoesDaTabela} opcoes
 * @returns {HTMLElement}
 */
export function tabelaDaTela(opcoes) {
  const { linhasDoRisco, escolhida, situacao, meses } = opcoes;
  const conteudo = tabela({
    legenda: opcoes.legenda,
    colunas: [
      {
        titulo: t("tela1.coluna-uf"),
        celula: (linha) =>
          elemento("button", {
            classe: "visao__uf",
            texto: linha.nome,
            atributos: {
              type: "button",
              "aria-pressed": String(linha.uf === escolhida),
              "data-uf": linha.uf,
            },
          }),
      },
      {
        titulo: t("tela2.coluna-taxa"),
        tipo: "numero",
        celula: (linha) => (linha.taxa === null ? "–" : taxa(linha.taxa, 1)),
      },
      {
        titulo: t("tela2.coluna-variacao", { meses: String(meses) }),
        tipo: "numero",
        celula: (linha) => (linha.variacao === null ? "–" : pontos(linha.variacao)),
      },
      {
        titulo: t("tela2.coluna-contra-o-pais"),
        celula: (linha) =>
          linha.contraOPais === null ? situacao(linha) : pontos(linha.contraOPais),
      },
      {
        titulo: t("tela2.coluna-alerta"),
        celula: (linha) => (linha.alerta ? alertaAntecipado() : "–"),
      },
      {
        titulo: t("tela2.coluna-quadrante"),
        celula: (linha) => (linha.quadrante ? etiquetaDeQuadrante(linha.quadrante) : "–"),
      },
      {
        titulo: t("tela2.coluna-custo"),
        tipo: "numero",
        celula: (linha) => (linha.custoDoRisco === null ? "–" : reais(linha.custoDoRisco)),
      },
    ],
    linhas: ordenar(linhasDoRisco),
  });
  return elemento(
    "div",
    {
      classe: "visao__tabela",
      atributos: { tabindex: "0", role: "region", "aria-label": opcoes.legenda },
    },
    [conteudo],
  );
}
