/**
 * PT: Os gráficos do ECharts que as visões desenham, num módulo só, para a
 *     visão buscá-los de uma vez, por `graficos()`, de `sob-demanda.js`.
 *     Quem importa daqui puxa o ECharts junto.
 * EN: The ECharts charts the views draw, in one module that views load on
 *     demand through `graficos()`. Importing from here pulls in ECharts.
 */

export { cartograma } from "./cartograma.js";
export { mapaPorUf, registrarMalha } from "./mapa-por-uf.js";
export { matrizDeCalor } from "./matriz-de-calor.js";
export { ranking } from "./ranking.js";
export { serieDeLinhas } from "./serie-de-linhas.js";
export { serieTemporal } from "./serie-temporal.js";
