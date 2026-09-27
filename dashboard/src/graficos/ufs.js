/**
 * PT: As 27 unidades da federação, com o código do IBGE e a posição no
 *     cartograma de grade.
 *
 *     O cartograma dá a cada UF um quadrado do mesmo tamanho, numa grade que
 *     preserva a posição aproximada de cada uma no mapa. Assim o Distrito
 *     Federal e os estados pequenos do Nordeste ficam tão legíveis quanto o
 *     Amazonas (RF-103). A malha do IBGE identifica a UF pelo código, e o
 *     dado do projeto pela sigla: esta tabela liga os dois.
 *
 *     Como a grade foi montada (revisada em 2026-09-27): cada UF foi posta
 *     perto do centroide dela na malha do IBGE, e todo par de UFs vizinhas
 *     na grade aponta, de uma para a outra, a menos de 60 graus da direção
 *     real entre os centroides. O teste `ufs.test.js` confere isso. A grade
 *     br_states_grid1 do geofacet serviu de ponto de partida, mas tinha o
 *     DF abaixo de Goiás e Santa Catarina ao lado do Paraná.
 *
 * EN: The 27 Brazilian states with their IBGE code and tile-grid position.
 *     Every state gets one equal tile, so small ones stay legible; the table
 *     also links the IBGE mesh code to the project's state abbreviation.
 *     Each grid neighbor lies within 60 degrees of the real centroid
 *     direction, checked by `ufs.test.js`.
 */

/**
 * @typedef {object} Uf
 * @property {string} sigla
 * @property {string} nome
 * @property {string} codigo Código do IBGE, como na malha / IBGE code
 * @property {number} linha Linha no cartograma, de norte a sul / tile row
 * @property {number} coluna Coluna no cartograma, de oeste a leste / tile column
 */

/** @type {readonly Uf[]} */
export const UFS = Object.freeze([
  { sigla: "RR", nome: "Roraima", codigo: "14", linha: 0, coluna: 2 },
  { sigla: "AP", nome: "Amapá", codigo: "16", linha: 0, coluna: 3 },
  { sigla: "AM", nome: "Amazonas", codigo: "13", linha: 1, coluna: 2 },
  { sigla: "PA", nome: "Pará", codigo: "15", linha: 1, coluna: 3 },
  { sigla: "MA", nome: "Maranhão", codigo: "21", linha: 1, coluna: 4 },
  { sigla: "CE", nome: "Ceará", codigo: "23", linha: 1, coluna: 5 },
  { sigla: "RN", nome: "Rio Grande do Norte", codigo: "24", linha: 1, coluna: 6 },
  { sigla: "AC", nome: "Acre", codigo: "12", linha: 2, coluna: 0 },
  { sigla: "RO", nome: "Rondônia", codigo: "11", linha: 2, coluna: 1 },
  { sigla: "MT", nome: "Mato Grosso", codigo: "51", linha: 2, coluna: 2 },
  { sigla: "TO", nome: "Tocantins", codigo: "17", linha: 2, coluna: 3 },
  { sigla: "PI", nome: "Piauí", codigo: "22", linha: 2, coluna: 4 },
  { sigla: "PE", nome: "Pernambuco", codigo: "26", linha: 2, coluna: 5 },
  { sigla: "PB", nome: "Paraíba", codigo: "25", linha: 2, coluna: 6 },
  { sigla: "MS", nome: "Mato Grosso do Sul", codigo: "50", linha: 3, coluna: 2 },
  { sigla: "GO", nome: "Goiás", codigo: "52", linha: 3, coluna: 3 },
  { sigla: "DF", nome: "Distrito Federal", codigo: "53", linha: 3, coluna: 4 },
  { sigla: "BA", nome: "Bahia", codigo: "29", linha: 3, coluna: 5 },
  { sigla: "SE", nome: "Sergipe", codigo: "28", linha: 3, coluna: 6 },
  { sigla: "AL", nome: "Alagoas", codigo: "27", linha: 3, coluna: 7 },
  { sigla: "SP", nome: "São Paulo", codigo: "35", linha: 4, coluna: 3 },
  { sigla: "MG", nome: "Minas Gerais", codigo: "31", linha: 4, coluna: 4 },
  { sigla: "ES", nome: "Espírito Santo", codigo: "32", linha: 4, coluna: 5 },
  { sigla: "PR", nome: "Paraná", codigo: "41", linha: 5, coluna: 3 },
  { sigla: "RJ", nome: "Rio de Janeiro", codigo: "33", linha: 5, coluna: 4 },
  { sigla: "SC", nome: "Santa Catarina", codigo: "42", linha: 6, coluna: 3 },
  { sigla: "RS", nome: "Rio Grande do Sul", codigo: "43", linha: 7, coluna: 3 },
]);

const porSigla = new Map(UFS.map((uf) => [uf.sigla, uf]));
const porCodigo = new Map(UFS.map((uf) => [uf.codigo, uf]));

/**
 * PT: A UF pela sigla. Falha se a sigla não existir.
 * EN: The state by abbreviation; throws when unknown.
 *
 * @param {string} sigla
 * @returns {Uf}
 */
export function ufPelaSigla(sigla) {
  const uf = porSigla.get(sigla);
  if (!uf) throw new Error(`UF desconhecida: ${sigla}`);
  return uf;
}

/**
 * PT: A UF pelo código do IBGE. Falha se o código não existir.
 * EN: The state by IBGE code; throws when unknown.
 *
 * @param {string} codigo
 * @returns {Uf}
 */
export function ufPeloCodigo(codigo) {
  const uf = porCodigo.get(codigo);
  if (!uf) throw new Error(`Código de UF desconhecido: ${codigo}`);
  return uf;
}
