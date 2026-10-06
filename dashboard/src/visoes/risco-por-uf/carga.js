/**
 * PT: Os arquivos da Tela 2, num módulo leve, separado do que desenha a tela
 *     (#89). A navegação busca este módulo junto com o da tela. A série
 *     mensal, o maior arquivo do site, fica de fora: a tela a busca só
 *     quando uma UF é escolhida, porque só o painel da UF a usa.
 *
 * EN: Screen 2's files, in a light module the router loads alongside the
 *     screen code. The monthly series, the site's largest file, is fetched
 *     only when a state is chosen.
 */

import { carregar, carregarManifesto, carregarOntologia } from "../../dados/carregar.js";
import { carregarMalha } from "../../graficos/malha.js";

/** @typedef {import("../../dados/carregar.js").ArquivoDeDados} ArquivoDeDados */
/** @typedef {import("../../dados/carregar.js").Ontologia} Ontologia */
/** @typedef {import("../../graficos/malha.js").Malha} Malha */

/**
 * @typedef {object} DadosDaTela
 * @property {ArquivoDeDados} decisao O `decisao.json`
 * @property {Ontologia} ontologia
 * @property {Malha | null} malha
 * @property {number} corte O corte de materialidade, em reais (ADR 0014, decisão 2) / materiality cut
 * @property {number} minimoDeUfs (ADR 0014, decisão 7)
 * @property {number} meses A janela da tendência, em meses (ADR 0014, decisão 3) / trend window
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
  const [decisao, ontologia, manifesto, malha] = await Promise.all([
    carregar("decisao.json"),
    carregarOntologia(),
    carregarManifesto(),
    carregarMalha(ENDERECO_DA_MALHA).catch(() => null),
  ]);
  const parametros = manifesto.parametros_da_decisao;
  return {
    decisao,
    ontologia,
    malha,
    corte: parametros.decisao_carteira_minima,
    minimoDeUfs: parametros.decisao_minimo_de_ufs,
    meses: parametros.decisao_meses_de_tendencia,
  };
}
