/**
 * PT: Os arquivos da Tela 4, num módulo leve, separado do que desenha a tela
 *     (#89): a decisão, o erro da reconstrução das empresas, para a fronteira
 *     do dado, e o manifesto, que dá o corte de materialidade.
 * EN: Screen 4's files, in a light module the router loads alongside the
 *     screen code.
 */

import { carregar, carregarManifesto } from "../../dados/carregar.js";

/** @typedef {import("../../dados/carregar.js").ArquivoDeDados} ArquivoDeDados */

/**
 * @typedef {object} DadosDaTela
 * @property {ArquivoDeDados} decisao O `decisao.json`
 * @property {ArquivoDeDados} erro O `erro_da_reconstrucao.json`
 * @property {number} corte O corte de materialidade, em reais (ADR 0014, decisão 2) / materiality cut
 */

/**
 * PT: Carrega os arquivos da tela.
 * EN: Loads the screen's files.
 *
 * @returns {Promise<DadosDaTela>}
 */
export async function carregarDados() {
  const [decisao, erro, manifesto] = await Promise.all([
    carregar("decisao.json"),
    carregar("erro_da_reconstrucao.json"),
    carregarManifesto(),
  ]);
  return { decisao, erro, corte: manifesto.parametros_da_decisao.decisao_carteira_minima };
}
