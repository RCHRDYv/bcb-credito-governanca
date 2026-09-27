/**
 * PT: A lista de tokens gerada, com tipo, para quem precisa dos valores em
 *     JavaScript: o catálogo, o teste de contraste e, na #63, o tema dos
 *     gráficos. O CSS continua lendo as variáveis do tokens.css.
 *
 * EN: The generated token list, typed, for code that needs the values in
 *     JavaScript. CSS keeps reading the variables from tokens.css.
 */

import lista from "./estilos/tokens.json" with { type: "json" };

/**
 * @typedef {object} CorNoTema
 * @property {string} hex
 * @property {number} alpha
 */

/**
 * @typedef {object} TokenGerado
 * @property {string} caminho Caminho do token, como `color.text.primary` / token path
 * @property {string} variavel Variável CSS, como `--color-text-primary` / CSS variable
 * @property {string} tipo Tipo DTCG, como `color` ou `dimension` / DTCG type
 * @property {"primitivo" | "semantico" | "componente"} camada
 * @property {string | null} descricao
 * @property {string} css Valor no CSS, com `var()` nas referências / CSS value
 * @property {CorNoTema} [claro] Cor final no tema claro, só nas cores / light color
 * @property {CorNoTema} [escuro] Cor final no tema escuro, só nas cores / dark color
 */

/** @typedef {"claro" | "escuro"} Tema */

/** @type {TokenGerado[]} */
export const TOKENS = /** @type {TokenGerado[]} */ (lista);

const porCaminho = new Map(TOKENS.map((token) => [token.caminho, token]));
const porVariavel = new Map(TOKENS.map((token) => [token.variavel, token]));

/**
 * PT: O token pelo caminho. Falha se ele não existir, para um nome errado
 *     não passar calado.
 * EN: The token by path; throws when missing.
 *
 * @param {string} caminho
 * @returns {TokenGerado}
 */
export function token(caminho) {
  const encontrado = porCaminho.get(caminho);
  if (!encontrado) {
    throw new Error(`Token não encontrado: ${caminho}`);
  }
  return encontrado;
}

/**
 * PT: A cor final de um token de cor num tema.
 * EN: A color token's final color in a theme.
 *
 * @param {string} caminho
 * @param {Tema} tema
 * @returns {CorNoTema}
 */
export function cor(caminho, tema) {
  const valor = token(caminho)[tema];
  if (!valor) {
    throw new Error(`Token sem cor: ${caminho}`);
  }
  return valor;
}

/**
 * PT: O valor literal por trás de uma variável, seguindo os `var()` até um
 *     valor sem referência. Serve para mostrar, por exemplo, que o
 *     `--type-heading-02` usa 16px e peso 600.
 * EN: The literal value behind a variable, following `var()` chains.
 *
 * @param {string} variavel
 * @returns {string}
 */
export function valorLiteral(variavel) {
  const encontrado = porVariavel.get(variavel);
  if (!encontrado) {
    return variavel;
  }
  return encontrado.css.replace(/var\((--[\w-]+)\)/g, (_, nome) => valorLiteral(nome));
}
