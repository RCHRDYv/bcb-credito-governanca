/**
 * PT: A tabela da Tela 4 (RF-G06), uma das formas de ver o palco, e o CSV
 *     dos mesmos números (#71). As células vêm por quadrante, na ordem do
 *     relatório, e dentro de cada um do custo maior para o menor. O
 *     quadrante e o alerta antecipado vão nas etiquetas do design system.
 * EN: Screen 4's table and its CSV: cells by quadrant, largest cost first,
 *     with the quadrant and early-warning tags.
 */

import { alertaAntecipado } from "../../componentes/alerta-antecipado.js";
import { botao } from "../../componentes/botao.js";
import { etiquetaDeQuadrante, nomeDoQuadrante } from "../../componentes/etiqueta-de-quadrante.js";
import { tabela } from "../../componentes/tabela.js";
import { baixarCsv, montarCsv, numeroDoCsv, textoDoCsv } from "../../dados/csv.js";
import { elemento } from "../../dom.js";
import { pontos, reais, vezes } from "../../formatos.js";
import { t } from "../../textos/index.js";
import { celulasDoQuadrante, ORDEM } from "./dados.js";

/** @typedef {import("./dados.js").Celula} Celula */
/** @typedef {import("../../textos/index.js").ChaveDeTexto} ChaveDeTexto */

/**
 * PT: As células na ordem da tabela e do CSV.
 * EN: Cells in table and CSV order.
 *
 * @param {Celula[]} celulas
 * @returns {Celula[]}
 */
export function emOrdem(celulas) {
  return ORDEM.flatMap((quadrante) => celulasDoQuadrante(celulas, quadrante));
}

/**
 * PT: O CSV, com os números crus, como nos arquivos do contrato: reais em
 *     reais inteiros e frações com seis casas.
 * EN: The CSV with raw numbers, as in the contract files.
 *
 * @param {Celula[]} celulas
 * @returns {string}
 */
export function csv(celulas) {
  /** @type {[string, (c: Celula) => string][]} */
  const colunas = [
    [t("tela1.coluna-uf"), (c) => c.uf],
    [t("tela4.coluna-modalidade"), (c) => textoDoCsv(c.modalidade)],
    [t("tela2.coluna-quadrante"), (c) => textoDoCsv(nomeDoQuadrante(c.quadrante))],
    [t("tela1.carteira-pj"), (c) => numeroDoCsv(c.carteira, 0)],
    [t("tela4.coluna-espaco"), (c) => numeroDoCsv(c.indiceDeEspaco, 6)],
    [t("tela4.coluna-risco"), (c) => numeroDoCsv(c.desvioDoRisco, 6)],
    [t("tela4.coluna-custo-nao-entrar"), (c) => numeroDoCsv(c.custoDeNaoEntrar, 0)],
    [t("tela4.coluna-custo-risco"), (c) => numeroDoCsv(c.custoDoRisco, 0)],
    [t("tela2.coluna-alerta"), (c) => t(c.alerta ? "tela2.sim" : "tela2.nao")],
  ];
  return montarCsv(colunas, emOrdem(celulas));
}

/**
 * PT: O botão que baixa o CSV.
 * EN: The CSV download button.
 *
 * @param {Celula[]} celulas
 * @param {string} arquivo
 * @returns {HTMLButtonElement}
 */
export function botaoDoCsv(celulas, arquivo) {
  return botao({
    texto: t("tela1.baixar-csv"),
    variante: "secundario",
    icone: "download",
    aoClicar: () => baixarCsv(csv(celulas), arquivo),
  });
}

/**
 * PT: A tabela das células avaliadas, numa área que rola por dentro.
 * EN: The evaluated cells' table, in an inner scroll area.
 *
 * @param {Celula[]} celulas
 * @param {string} legenda
 * @returns {HTMLDivElement}
 */
export function tabelaDaTela(celulas, legenda) {
  const conteudo = tabela({
    legenda,
    colunas: [
      { titulo: t("tela1.coluna-uf"), celula: (c) => c.uf },
      {
        titulo: t("tela4.coluna-modalidade"),
        celula: (c) => t(/** @type {ChaveDeTexto} */ (`modalidade-curta.${c.codigo}`)),
      },
      { titulo: t("tela2.coluna-quadrante"), celula: (c) => etiquetaDeQuadrante(c.quadrante) },
      { titulo: t("tela1.carteira-pj"), tipo: "numero", celula: (c) => reais(c.carteira) },
      { titulo: t("tela4.coluna-espaco"), tipo: "numero", celula: (c) => vezes(c.indiceDeEspaco) },
      { titulo: t("tela4.coluna-risco"), tipo: "numero", celula: (c) => pontos(c.desvioDoRisco) },
      {
        titulo: t("tela4.coluna-custo-nao-entrar"),
        tipo: "numero",
        celula: (c) => (c.custoDeNaoEntrar === null ? "–" : reais(c.custoDeNaoEntrar)),
      },
      {
        titulo: t("tela4.coluna-custo-risco"),
        tipo: "numero",
        celula: (c) => (c.custoDoRisco === null ? "–" : reais(c.custoDoRisco)),
      },
      { titulo: t("tela2.coluna-alerta"), celula: (c) => (c.alerta ? alertaAntecipado() : "–") },
    ],
    linhas: emOrdem(celulas),
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
