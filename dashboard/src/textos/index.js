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
 * PT: Devolve o texto da chave, ou lança um erro se ela não existe. Um texto
 *     pode ter lacunas, como `{de}`, preenchidas pelos valores: assim a
 *     ordem das palavras fica no arquivo de tradução, e não no componente.
 * EN: Returns the text for a key, or throws if the key does not exist.
 *     Placeholders such as `{de}` are filled from `valores`.
 *
 * @param {ChaveDeTexto} chave
 * @param {Record<string, string>} [valores]
 * @returns {string}
 */
export function t(chave, valores) {
  if (!Object.hasOwn(ptBR, chave)) {
    throw new Error(`Texto sem chave no arquivo de tradução: ${chave}`);
  }
  const texto = ptBR[chave];
  if (!valores) return texto;
  return texto.replace(/\{(\w+)\}/g, (_lacuna, nome) => {
    if (!Object.hasOwn(valores, nome)) {
      throw new Error(`Valor sem lacuna preenchida em ${chave}: ${nome}`);
    }
    return valores[nome];
  });
}
