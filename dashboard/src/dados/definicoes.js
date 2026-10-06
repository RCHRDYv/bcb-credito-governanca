/**
 * PT: De onde vem a definição de cada número da tela (RF-G07).
 *
 *     O contrato dos dados diz, para cada coluna, onde está a definição: um
 *     conceito da ontologia ("ontology/metricas.yml#carteira_ativa") ou o ADR
 *     que fixou a regra ("ADR 0014, decisão 1"). O `ontologia.json` traz os
 *     conceitos citados e o mapa de cada coluna para a sua definição. Este
 *     módulo transforma essa referência no que a tela mostra: o conceito, com
 *     a explicação, a definição oficial, a fonte e a confiança, ou o ADR, com
 *     o endereço dele no repositório.
 *
 * EN: Where each number's definition comes from. The contract maps every
 *     column to an ontology concept or to the ADR that set the rule; this
 *     module turns that reference into what the page shows.
 */

/** @typedef {import("./carregar.js").Ontologia} Ontologia */
/** @typedef {import("./carregar.js").Conceito} Conceito */

/**
 * PT: Os ADRs que o contrato cita, pelo número, com o nome do arquivo. Um
 *     ADR novo no contrato precisa entrar aqui, e o teste reprova o que
 *     faltar.
 * EN: ADRs the contract cites, by number, with their file names.
 */
export const ADRS = Object.freeze({
  "0003": "0003-conformacao-de-taxonomia-entre-versoes.md",
  "0009": "0009-empresas-ativas-reconstruidas-de-um-retrato-do-cnpj.md",
  "0014": "0014-matriz-de-decisao-espaco-contra-risco.md",
  "0023": "0023-previsao-da-carteira-escolhida-pelo-backtest.md",
});

const ENDERECO_DOS_ADRS = "https://github.com/RCHRDYv/bcb-credito-governanca/blob/main/docs/adr/";

/**
 * @typedef {object} DefinicaoDeConceito
 * @property {"conceito"} tipo
 * @property {string} rotulo
 * @property {string | null} explicacao Em palavras comuns, quando existe / plain words
 * @property {string | null} explicacaoFonte De onde a explicação saiu / its source
 * @property {string | null} definicao A definição da fonte / source definition
 * @property {string | null} fonte
 * @property {string | null} confianca
 */

/**
 * @typedef {object} DefinicaoPorAdr
 * @property {"adr"} tipo
 * @property {string} rotulo Como o contrato cita, "ADR 0014, decisão 1" / as cited
 * @property {string} endereco O ADR no repositório / the ADR in the repository
 */

/** @typedef {DefinicaoDeConceito | DefinicaoPorAdr} Definicao */

/**
 * PT: A definição a partir de um conceito da ontologia.
 * EN: A definition from an ontology concept.
 *
 * @param {Conceito} conceito
 * @returns {DefinicaoDeConceito}
 */
function doConceito(conceito) {
  return {
    tipo: "conceito",
    rotulo: conceito.rotulo ?? conceito.id,
    explicacao: conceito.explicacao ?? null,
    explicacaoFonte: conceito.explicacao_fonte ?? null,
    definicao: conceito.definicao,
    fonte: conceito.fonte,
    confianca: conceito.confianca,
  };
}

/**
 * PT: Resolve uma referência do contrato: um ADR ou um conceito pelo `ref`.
 *     Devolve `null` quando a referência não aponta para um conceito só,
 *     como a do arquivo inteiro de modalidades: aí quem chama resolve pela
 *     modalidade da linha.
 * EN: Resolves a contract reference: an ADR or a concept by `ref`.
 *
 * @param {Ontologia} ontologia
 * @param {string} referencia
 * @returns {Definicao | null}
 */
export function resolver(ontologia, referencia) {
  const adr = /^ADR (\d{4})/.exec(referencia);
  if (adr) {
    const arquivo = ADRS[/** @type {keyof typeof ADRS} */ (adr[1])];
    if (!arquivo) throw new Error(`ADR sem endereço em definicoes.js: ${referencia}`);
    return { tipo: "adr", rotulo: referencia, endereco: `${ENDERECO_DOS_ADRS}${arquivo}` };
  }
  const conceito = ontologia.conceitos.find((c) => c.ref === referencia);
  return conceito ? doConceito(conceito) : null;
}

/**
 * PT: A definição de uma coluna de um arquivo, pelo mapa do `ontologia.json`.
 * EN: A column's definition, through the `ontologia.json` map.
 *
 * @param {Ontologia} ontologia
 * @param {string} arquivo
 * @param {string} coluna
 * @returns {Definicao | null}
 */
export function definicaoDaColuna(ontologia, arquivo, coluna) {
  const referencia = ontologia.colunas[arquivo]?.[coluna];
  if (!referencia) throw new Error(`Coluna fora do contrato: ${arquivo}, ${coluna}`);
  return resolver(ontologia, referencia);
}

/**
 * PT: A definição de uma modalidade, pelo código do BCB.
 * EN: A modality's definition, by BCB code.
 *
 * @param {Ontologia} ontologia
 * @param {string} codigo
 * @returns {DefinicaoDeConceito | null}
 */
export function definicaoDaModalidade(ontologia, codigo) {
  const conceito = ontologia.conceitos.find((c) => c.codigo === codigo);
  return conceito ? doConceito(conceito) : null;
}
