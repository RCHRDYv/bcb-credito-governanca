/**
 * PT: Os arquivos da Tela 1, num módulo leve, separado do que desenha a tela.
 *
 *     A navegação busca este módulo junto com o da tela, e os dados começam
 *     a baixar sem esperar pelo código da tela (#89). Por isso aqui não entra
 *     nada que puxe o ECharts.
 *
 * EN: Screen 1's files, in a light module apart from the screen code, so the
 *     router starts downloading data without waiting for that code. Nothing
 *     here may pull in ECharts.
 */

import { carregar, carregarManifesto, carregarOntologia } from "../../dados/carregar.js";
import { carregarMalha } from "../../graficos/malha.js";

/** @typedef {import("./dados.js").DadosDaVisao} DadosDaVisao */
/** @typedef {import("../../dados/carregar.js").Ontologia} Ontologia */
/** @typedef {import("../../graficos/malha.js").Malha} Malha */

/**
 * @typedef {DadosDaVisao & {
 *   ontologia: Ontologia,
 *   malha: Malha | null,
 *   corte: number,
 *   minimoDeUfs: number,
 * }} DadosDaTela
 */

const ENDERECO_DA_MALHA = "./geo/ufs.json";

/**
 * PT: Carrega os arquivos da tela. A malha não derruba a tela: sem ela, a
 *     grade toma o lugar do mapa.
 * EN: Loads the screen's files; without the mesh the grid replaces the map.
 *
 * @returns {Promise<DadosDaTela>}
 */
export async function carregarDados() {
  const [porUf, decisao, ontologia, manifesto, malha] = await Promise.all([
    carregar("carteira_por_uf.json"),
    carregar("decisao.json"),
    carregarOntologia(),
    carregarManifesto(),
    carregarMalha(ENDERECO_DA_MALHA).catch(() => null),
  ]);
  // PT: os parâmetros do ADR 0014, lidos do que a exportação registra, para
  //     o texto nunca ficar velho
  // EN: ADR 0014 parameters, from the exported manifest
  const corte = manifesto.parametros_da_decisao.decisao_carteira_minima;
  const minimoDeUfs = manifesto.parametros_da_decisao.decisao_minimo_de_ufs;
  return { porUf, decisao, ontologia, malha, corte, minimoDeUfs };
}
