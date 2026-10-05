/**
 * PT: As visões que o site tem, na ordem da navegação.
 *
 *     Cada visão tem um endereço por hash, porque o GitHub Pages não tem rota
 *     de reserva: um endereço como `/credito-por-uf` daria 404, e
 *     `#/credito-por-uf` sempre abre o mesmo `index.html`. Cada visão é
 *     carregada só quando é aberta, então o código de uma não pesa na outra.
 *
 *     Uma visão entra aqui quando fica pronta. A primeira da lista é a que o
 *     endereço do site abre (decidido em 2026-10-01).
 *
 * EN: The site's views, in navigation order. Hash addresses, since GitHub
 *     Pages has no fallback route; each view loads only when opened. The
 *     first one is what the site's address opens.
 */

import { t } from "../textos/index.js";

/**
 * @typedef {object} ModuloDeVisao
 * @property {() => Promise<unknown>} carregarDados Busca os arquivos da visão / loads the view's files
 * @property {(el: HTMLElement, dados: any) => () => void} render Monta a visão e devolve como desmontá-la / builds and returns teardown
 */

/**
 * @typedef {object} Visao
 * @property {string} id
 * @property {string} nome Como aparece na navegação / navigation label
 * @property {() => Promise<ModuloDeVisao>} modulo
 */

/** @type {readonly Visao[]} */
export const VISOES = Object.freeze([
  {
    id: "credito-por-uf",
    nome: t("navegacao.credito-por-uf"),
    modulo: () => import("./credito-por-uf/index.js"),
  },
]);

/**
 * PT: O endereço por hash de uma visão.
 * EN: A view's hash address.
 *
 * @param {Visao} visao
 * @returns {string}
 */
export function endereco(visao) {
  return `#/${visao.id}`;
}

/**
 * PT: A visão de um hash, ou a primeira, para endereço vazio ou desconhecido.
 * EN: The view for a hash, or the first one.
 *
 * @param {string} hash
 * @returns {Visao}
 */
export function visaoDoHash(hash) {
  const id = hash.replace(/^#\/?/, "");
  return VISOES.find((visao) => visao.id === id) ?? VISOES[0];
}
