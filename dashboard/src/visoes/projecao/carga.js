/**
 * PT: Os arquivos da Tela 3, num módulo leve, separado do que desenha a tela
 *     (#89): a projeção, o backtest, os testes recentes e a ontologia, que dá
 *     o nome das modalidades.
 * EN: Screen 3's files, in a light module the router loads alongside the
 *     screen code.
 */

import { carregar, carregarOntologia } from "../../dados/carregar.js";

/** @typedef {import("../../dados/carregar.js").ArquivoDeDados} ArquivoDeDados */
/** @typedef {import("../../dados/carregar.js").Ontologia} Ontologia */

/**
 * @typedef {object} DadosDaTela
 * @property {ArquivoDeDados} projecao O `projecao_da_carteira.json`
 * @property {ArquivoDeDados} backtest O `backtest_da_projecao.json`
 * @property {ArquivoDeDados} testes O `testes_da_projecao.json`
 * @property {Ontologia} ontologia
 */

/**
 * PT: Carrega os arquivos da tela.
 * EN: Loads the screen's files.
 *
 * @returns {Promise<DadosDaTela>}
 */
export async function carregarDados() {
  const [projecao, backtest, testes, ontologia] = await Promise.all([
    carregar("projecao_da_carteira.json"),
    carregar("backtest_da_projecao.json"),
    carregar("testes_da_projecao.json"),
    carregarOntologia(),
  ]);
  return { projecao, backtest, testes, ontologia };
}
