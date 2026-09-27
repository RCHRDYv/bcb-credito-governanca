/**
 * PT: Formatação de números e datas no padrão brasileiro, como o guia do
 *     design system pede: R$ 485,5 bi, 0,93%, +0,15 p.p., jul/2026.
 *
 *     Os arquivos de dados trazem os números sem formatação, em reais e em
 *     fração de 0 a 1 (RF-G10). A formatação acontece só aqui, na tela.
 *
 * EN: Brazilian number and date formatting, as the design system guide
 *     specifies. Data files carry raw numbers; formatting happens only here.
 */

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

/**
 * PT: Número com casas decimais fixas, no padrão brasileiro.
 * EN: Number with fixed decimals, Brazilian style.
 *
 * @param {number} valor
 * @param {number} [casas]
 * @returns {string}
 */
export function numero(valor, casas = 1) {
  return valor.toLocaleString("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  });
}

/**
 * PT: Reais na maior unidade que deixa o número curto: bi, mi ou mil.
 * EN: Reais in the largest unit that keeps the number short.
 *
 * @param {number} valor Em reais / in reais
 * @param {number} [casas]
 * @returns {string}
 */
export function reais(valor, casas = 1) {
  const absoluto = Math.abs(valor);
  if (absoluto >= 1e9) return `R$ ${numero(valor / 1e9, casas)} bi`;
  if (absoluto >= 1e6) return `R$ ${numero(valor / 1e6, casas)} mi`;
  if (absoluto >= 1e3) return `R$ ${numero(valor / 1e3, casas)} mil`;
  return `R$ ${numero(valor, 0)}`;
}

/**
 * PT: Taxa em porcentagem, a partir da fração.
 * EN: Rate as a percentage, from a fraction.
 *
 * @param {number} fracao De 0 a 1 / from 0 to 1
 * @param {number} [casas]
 * @returns {string}
 */
export function taxa(fracao, casas = 2) {
  return `${numero(fracao * 100, casas)}%`;
}

/**
 * PT: Diferença entre duas taxas, em pontos percentuais e sempre com sinal.
 * EN: Difference between two rates, in percentage points, always signed.
 *
 * @param {number} fracao Diferença de frações / difference of fractions
 * @param {number} [casas]
 * @returns {string}
 */
export function pontos(fracao, casas = 2) {
  const valor = fracao * 100;
  const sinal = valor > 0 ? "+" : valor < 0 ? "−" : "";
  return `${sinal}${numero(Math.abs(valor), casas)} p.p.`;
}

/**
 * PT: Quantas vezes uma referência, como "0,82×".
 * EN: Times a reference, such as "0,82×".
 *
 * @param {number} valor
 * @param {number} [casas]
 * @returns {string}
 */
export function vezes(valor, casas = 2) {
  return `${numero(valor, casas)}×`;
}

/**
 * PT: Data-base no formato do guia: "2026-07-31" vira "jul/2026".
 * EN: Reference date as "jul/2026".
 *
 * @param {string} data `aaaa-mm-dd`
 * @returns {string}
 */
export function dataBase(data) {
  return `${MESES[Number(data.slice(5, 7)) - 1]}/${data.slice(0, 4)}`;
}

/**
 * PT: Mês curto, para eixo de gráfico: "2026-07-31" vira "jul/26".
 * EN: Short month for chart axes.
 *
 * @param {string} data `aaaa-mm-dd`
 * @returns {string}
 */
export function mesCurto(data) {
  return `${MESES[Number(data.slice(5, 7)) - 1]}/${data.slice(2, 4)}`;
}
