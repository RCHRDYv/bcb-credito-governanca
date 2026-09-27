/**
 * PT: Acesso aos textos da interface.
 *
 *     `t(chave)` devolve o texto em português. Uma chave que não existe faz a
 *     função lançar um erro, em vez de devolver vazio: assim o texto que falta
 *     quebra o teste, e não aparece em branco na tela. O tipo `ChaveDeTexto`
 *     faz a checagem de tipos acusar a chave errada antes mesmo do teste.
 *
 * EN: Access to interface texts. `t(key)` returns the Portuguese text and
 *     throws on an unknown key, so a missing text breaks a test instead of
 *     rendering blank. `ChaveDeTexto` lets the type checker flag wrong keys.
 */

import { ptBR } from "./pt-BR.js";

/** @typedef {keyof typeof ptBR} ChaveDeTexto */

/**
 * PT: Devolve o texto da chave, ou lança um erro se ela não existe.
 * EN: Returns the text for a key, or throws if the key does not exist.
 *
 * @param {ChaveDeTexto} chave
 * @returns {string}
 */
export function t(chave) {
  if (!Object.hasOwn(ptBR, chave)) {
    throw new Error(`Texto sem chave no arquivo de tradução: ${chave}`);
  }
  return ptBR[chave];
}
