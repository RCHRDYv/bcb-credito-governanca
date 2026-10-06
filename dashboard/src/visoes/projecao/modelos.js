/**
 * PT: O nome comum de cada um dos dez candidatos da previsão (#27, #98) e
 *     como ele projeta, para o cartão da esquerda da Tela 3 (#72). Todo
 *     modelo do `backtest_da_projecao.json` tem os dois textos, e o teste de
 *     unidade confere: o campeão de uma série pode mudar quando a previsão
 *     roda de novo, e um nome que falta quebra o teste, em vez de aparecer
 *     cru na tela.
 * EN: Plain name and method sentence for each of the ten forecast
 *     candidates; a missing text throws instead of showing the raw name.
 */

import { t } from "../../textos/index.js";

/** @typedef {import("../../textos/index.js").ChaveDeTexto} ChaveDeTexto */

/**
 * PT: O nome comum do campeão e a frase de como ele projeta.
 * EN: The champion's plain name and how it forecasts.
 *
 * @param {string} modelo Como no arquivo, como `deriva` / as in the file
 * @returns {{ nome: string, como: string }}
 */
export function sobreOModelo(modelo) {
  return {
    nome: t(/** @type {ChaveDeTexto} */ (`tela3.modelo.${modelo}`)),
    como: t(/** @type {ChaveDeTexto} */ (`tela3.como.${modelo}`)),
  };
}
