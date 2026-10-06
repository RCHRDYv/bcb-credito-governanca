/**
 * PT: A malha das UFs, buscada sem o ECharts.
 *
 *     A busca fica fora do módulo do mapa para a visão poder baixar a malha
 *     junto com os dados, antes de o ECharts chegar (#89). O registro no
 *     ECharts acontece só quando o mapa é desenhado, por `registrarMalha()`,
 *     em `mapa-por-uf.js`; no celular, onde a grade é a forma inicial, ele
 *     pode nem acontecer.
 *
 * EN: The state mesh, fetched without ECharts, so a view can download it with
 *     its data before ECharts arrives. Registration happens only when the map
 *     is drawn.
 */

import { ufPeloCodigo } from "./ufs.js";

/**
 * @typedef {object} Malha
 * @property {"FeatureCollection"} type
 * @property {{ properties: Record<string, string> }[]} features
 */

/**
 * PT: Busca a malha e dá a cada área a sigla da UF como nome. A malha do IBGE
 *     identifica a UF pelo código (`codarea`).
 * EN: Fetches the mesh and names each area by state abbreviation.
 *
 * @param {string} endereco
 * @returns {Promise<Malha>}
 */
export async function carregarMalha(endereco) {
  const resposta = await fetch(endereco);
  if (!resposta.ok) {
    throw new Error(`A malha das UFs não carregou: ${resposta.status}`);
  }
  const malha = /** @type {Malha} */ (await resposta.json());
  for (const feicao of malha.features) {
    feicao.properties.name = ufPeloCodigo(feicao.properties.codarea).sigla;
  }
  return malha;
}
