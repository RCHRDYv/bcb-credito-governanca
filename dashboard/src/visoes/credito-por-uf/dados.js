/**
 * PT: Os dados da Tela 1, a partir dos arquivos do contrato (#69).
 *
 *     São funções puras: recebem os arquivos já carregados e devolvem o que
 *     a tela desenha. O site não calcula nenhuma razão: a carteira por
 *     empresa, a mediana, o índice de espaço, o crédito que faltaria para
 *     chegar à mediana e a participação no país vêm prontos dos marts (ADR
 *     0007). Aqui só se soma, conta e ordena.
 *
 *     - **Todas as modalidades** vêm do `carteira_por_uf.json`, que traz a
 *       carteira PJ inteira de cada UF com o denominador do ADR 0014.
 *     - **Uma modalidade** vem do `decisao.json`, a célula de UF e
 *       modalidade. A UF sem carteira nessa modalidade não tem linha no
 *       arquivo, e a célula abaixo do corte de materialidade vem sem mediana
 *       nem índice, com o motivo.
 *
 *     Só as UFs comparadas com a mediana recebem cor e entram no ranking da
 *     oportunidade, porque o ADR 0014 não compara razões de células pequenas
 *     demais para dar um número estável.
 *
 * EN: Screen 1 data from the contract files, as pure functions. No ratio is
 *     computed here; ratios, gaps and shares come from the marts. This module
 *     only sums, counts and sorts. "All modalities" comes from
 *     carteira_por_uf.json, one modality from decisao.json.
 */

import { UFS } from "../../graficos/ufs.js";

/** @typedef {import("../../dados/carregar.js").ArquivoDeDados} ArquivoDeDados */

/** PT: o valor do filtro para todas as modalidades / EN: the all-modalities filter value */
export const TODAS = "todas";

/**
 * PT: Comparada com a mediana; abaixo do corte de materialidade; numa
 *     modalidade com poucas UFs acima do corte; ou sem carteira.
 * EN: Compared with the median; below the cut; in a thin modality; or none.
 *
 * @typedef {"comparada" | "abaixo-do-corte" | "poucas-ufs" | "sem-carteira"} Situacao
 */

/**
 * @typedef {object} LinhaDaVisao
 * @property {string} uf Sigla / abbreviation
 * @property {string} nome Nome da UF / state name
 * @property {number | null} carteira Carteira PJ, em reais / PJ portfolio
 * @property {number | null} empresas Natureza empresarial, sem MEI / companies
 * @property {number | null} carteiraPorEmpresa Em reais / BRL per company
 * @property {number | null} mediana A das UFs comparadas / median across states
 * @property {number | null} indice Carteira por empresa sobre a mediana / room index
 * @property {number | null} custo Crédito que faltaria para chegar à mediana / gap to the median
 * @property {number | null} participacao Fatia da carteira PJ do país, só em todas / national share
 * @property {Situacao} situacao
 */

/**
 * @typedef {object} DadosDaVisao
 * @property {ArquivoDeDados} porUf O `carteira_por_uf.json`
 * @property {ArquivoDeDados} decisao O `decisao.json`
 */

/**
 * @typedef {object} Modalidade
 * @property {string} codigo Código do BCB / BCB code
 * @property {string} nome Nome do BCB / BCB name
 * @property {number} carteira A carteira PJ do país nela / national portfolio
 * @property {number} comparadas Quantas UFs entram na comparação / compared states
 */

/**
 * PT: Lê uma coluna como lista tipada. O validador do CI garante o tipo.
 * EN: Reads a column as a typed list; CI validation guarantees the type.
 *
 * @template T
 * @param {ArquivoDeDados} arquivo
 * @param {string} nome
 * @returns {T[]}
 */
function coluna(arquivo, nome) {
  return /** @type {T[]} */ (arquivo.colunas[nome]);
}

/**
 * PT: As modalidades presentes nos dados, com a carteira do país e quantas
 *     UFs entram na comparação, na ordem da carteira, da maior para a menor.
 * EN: Modalities in the data, with national portfolio and compared states,
 *     largest first.
 *
 * @param {ArquivoDeDados} decisao
 * @returns {Modalidade[]}
 */
export function modalidades(decisao) {
  const codigos = coluna(decisao, "codigo_modalidade");
  const nomes = coluna(decisao, "modalidade");
  const carteiras = coluna(decisao, "carteira_ativa");
  const avaliadas = coluna(decisao, "avaliada");
  /** @type {Map<string, Modalidade>} */
  const porCodigo = new Map();
  codigos.forEach((codigo, i) => {
    const chave = String(codigo);
    const atual = porCodigo.get(chave) ?? {
      codigo: chave,
      nome: String(nomes[i]),
      carteira: 0,
      comparadas: 0,
    };
    atual.carteira += Number(carteiras[i]);
    if (avaliadas[i]) atual.comparadas += 1;
    porCodigo.set(chave, atual);
  });
  return [...porCodigo.values()].sort((a, b) => b.carteira - a.carteira);
}

/**
 * PT: A linha de uma UF sem carteira no recorte.
 * EN: A state with no portfolio in the cut.
 *
 * @param {string} uf
 * @param {string} nome
 * @returns {LinhaDaVisao}
 */
function vazia(uf, nome) {
  return {
    uf,
    nome,
    carteira: null,
    empresas: null,
    carteiraPorEmpresa: null,
    mediana: null,
    indice: null,
    custo: null,
    participacao: null,
    situacao: "sem-carteira",
  };
}

/**
 * PT: As linhas de todas as modalidades: as 27 UFs, todas comparadas,
 *     porque no total da carteira PJ todas passam do corte.
 * EN: All-modalities rows: all 27 states, all compared.
 *
 * @param {ArquivoDeDados} porUf
 * @returns {LinhaDaVisao[]}
 */
function linhasDeTodas(porUf) {
  const ufs = coluna(porUf, "uf");
  const indice = new Map(ufs.map((uf, i) => [uf, i]));
  const carteira = coluna(porUf, "carteira_pj");
  const empresas = coluna(porUf, "empresas");
  const porEmpresa = coluna(porUf, "carteira_por_empresa");
  const mediana = coluna(porUf, "mediana_carteira_por_empresa");
  const espaco = coluna(porUf, "indice_de_espaco");
  const custo = coluna(porUf, "custo_de_nao_entrar");
  const participacao = coluna(porUf, "participacao_na_carteira_pj");
  return UFS.map((uf) => {
    const i = indice.get(uf.sigla);
    if (i === undefined) return vazia(uf.sigla, uf.nome);
    return {
      uf: uf.sigla,
      nome: uf.nome,
      carteira: /** @type {number} */ (carteira[i]),
      empresas: /** @type {number} */ (empresas[i]),
      carteiraPorEmpresa: /** @type {number} */ (porEmpresa[i]),
      mediana: /** @type {number} */ (mediana[i]),
      indice: /** @type {number} */ (espaco[i]),
      custo: /** @type {number | null} */ (custo[i]),
      participacao: /** @type {number} */ (participacao[i]),
      situacao: "comparada",
    };
  });
}

/**
 * PT: As linhas de uma modalidade, a partir das células do `decisao.json`.
 * EN: One modality's rows, from the decisao.json cells.
 *
 * @param {ArquivoDeDados} decisao
 * @param {string} codigo
 * @returns {LinhaDaVisao[]}
 */
function linhasDaModalidade(decisao, codigo) {
  const codigos = coluna(decisao, "codigo_modalidade");
  const ufs = coluna(decisao, "uf");
  const carteira = coluna(decisao, "carteira_ativa");
  const empresas = coluna(decisao, "empresas");
  const porEmpresa = coluna(decisao, "carteira_por_empresa");
  const mediana = coluna(decisao, "mediana_carteira_por_empresa");
  const espaco = coluna(decisao, "indice_de_espaco");
  const custo = coluna(decisao, "custo_de_nao_entrar");
  const avaliada = coluna(decisao, "avaliada");
  const motivo = coluna(decisao, "motivo_nao_avaliada");

  /** @type {Map<string, number>} */
  const indice = new Map();
  codigos.forEach((c, i) => {
    if (c === codigo) indice.set(String(ufs[i]), i);
  });
  return UFS.map((uf) => {
    const i = indice.get(uf.sigla);
    if (i === undefined) return vazia(uf.sigla, uf.nome);
    /** @type {Situacao} */
    let situacao = "comparada";
    if (!avaliada[i]) {
      situacao = String(motivo[i]).includes("poucas UFs") ? "poucas-ufs" : "abaixo-do-corte";
    }
    const comparada = situacao === "comparada";
    return {
      uf: uf.sigla,
      nome: uf.nome,
      carteira: /** @type {number} */ (carteira[i]),
      empresas: /** @type {number} */ (empresas[i]),
      carteiraPorEmpresa: /** @type {number} */ (porEmpresa[i]),
      mediana: comparada ? /** @type {number} */ (mediana[i]) : null,
      indice: comparada ? /** @type {number} */ (espaco[i]) : null,
      custo: comparada ? /** @type {number | null} */ (custo[i]) : null,
      participacao: null,
      situacao,
    };
  });
}

/**
 * PT: As 27 linhas da visão no recorte escolhido.
 * EN: The view's 27 rows for the chosen cut.
 *
 * @param {DadosDaVisao} dados
 * @param {string} codigo `TODAS` ou o código da modalidade / or a modality code
 * @returns {LinhaDaVisao[]}
 */
export function linhas(dados, codigo) {
  return codigo === TODAS ? linhasDeTodas(dados.porUf) : linhasDaModalidade(dados.decisao, codigo);
}

/**
 * @typedef {object} Resumo
 * @property {number} carteira A carteira PJ do recorte, somada / cut's portfolio
 * @property {number | null} mediana
 * @property {number} comparadas
 * @property {number} abaixo UFs abaixo da mediana / states below the median
 * @property {number} custo O crédito que faltaria, somado / summed gap
 */

/**
 * PT: O resumo do recorte, para o topo da tela: a carteira, a mediana,
 *     quantas UFs estão abaixo dela e quanto faltaria para elas chegarem a
 *     ela. Só somas e contagens das colunas dos marts.
 * EN: The cut's summary: portfolio, median, states below it and the summed
 *     gap. Only sums and counts of mart columns.
 *
 * @param {LinhaDaVisao[]} linhasDaVisao
 * @returns {Resumo}
 */
export function resumo(linhasDaVisao) {
  const comparadas = linhasDaVisao.filter((linha) => linha.situacao === "comparada");
  const abaixo = comparadas.filter((linha) => linha.custo !== null);
  return {
    carteira: linhasDaVisao.reduce((soma, linha) => soma + (linha.carteira ?? 0), 0),
    mediana: comparadas[0]?.mediana ?? null,
    comparadas: comparadas.length,
    abaixo: abaixo.length,
    custo: abaixo.reduce((soma, linha) => soma + /** @type {number} */ (linha.custo), 0),
  };
}

/**
 * PT: Os itens do ranking da oportunidade: as UFs abaixo da mediana, pelo
 *     crédito que faltaria para chegarem a ela.
 * EN: Opportunity ranking items: states below the median, by gap.
 *
 * @param {LinhaDaVisao[]} linhasDaVisao
 * @returns {{ rotulo: string, valor: number, chave: string }[]}
 */
export function oportunidade(linhasDaVisao) {
  return linhasDaVisao
    .filter((linha) => linha.custo !== null)
    .map((linha) => ({
      rotulo: linha.nome,
      valor: /** @type {number} */ (linha.custo),
      chave: linha.uf,
    }));
}

/**
 * PT: A posição da UF entre as comparadas, da menor carteira por empresa
 *     para a maior: 1 é a de mais espaço.
 * EN: The state's rank among compared ones, lowest per-company first.
 *
 * @param {LinhaDaVisao[]} linhasDaVisao
 * @param {string} uf
 * @returns {{ posicao: number, de: number } | null}
 */
export function posicaoDaUf(linhasDaVisao, uf) {
  const ordenadas = linhasDaVisao
    .filter((linha) => linha.situacao === "comparada")
    .sort(
      (a, b) =>
        /** @type {number} */ (a.carteiraPorEmpresa) - /** @type {number} */ (b.carteiraPorEmpresa),
    );
  const indice = ordenadas.findIndex((linha) => linha.uf === uf);
  return indice < 0 ? null : { posicao: indice + 1, de: ordenadas.length };
}

/**
 * @typedef {object} ModalidadeDaUf
 * @property {string} codigo
 * @property {string} nome
 * @property {number} carteira
 * @property {number | null} indice `null` fora da comparação / null outside the comparison
 */

/**
 * PT: As modalidades de uma UF, da maior carteira para a menor, com a
 *     posição de cada uma em relação à mediana da modalidade.
 * EN: A state's modalities, largest first, with each one's index.
 *
 * @param {ArquivoDeDados} decisao
 * @param {string} uf
 * @returns {ModalidadeDaUf[]}
 */
export function modalidadesDaUf(decisao, uf) {
  const ufs = coluna(decisao, "uf");
  const codigos = coluna(decisao, "codigo_modalidade");
  const nomes = coluna(decisao, "modalidade");
  const carteira = coluna(decisao, "carteira_ativa");
  const espaco = coluna(decisao, "indice_de_espaco");
  const avaliada = coluna(decisao, "avaliada");
  return ufs
    .map((u, i) => ({ u, i }))
    .filter(({ u }) => u === uf)
    .map(({ i }) => ({
      codigo: String(codigos[i]),
      nome: String(nomes[i]),
      carteira: Number(carteira[i]),
      indice: avaliada[i] ? /** @type {number} */ (espaco[i]) : null,
    }))
    .sort((a, b) => b.carteira - a.carteira);
}

/**
 * @typedef {object} CelulaDaMatriz
 * @property {string} uf
 * @property {string} codigo
 * @property {number} carteira
 * @property {number | null} indice `null` fora da comparação / null outside the comparison
 */

/**
 * PT: As células da matriz de UF por modalidade: todas as que existem no
 *     `decisao.json`, com o índice das comparadas.
 * EN: The state-by-modality cells: every existing cell, with the index of
 *     compared ones.
 *
 * @param {ArquivoDeDados} decisao
 * @returns {CelulaDaMatriz[]}
 */
export function celulasDaMatriz(decisao) {
  const ufs = coluna(decisao, "uf");
  const codigos = coluna(decisao, "codigo_modalidade");
  const carteira = coluna(decisao, "carteira_ativa");
  const espaco = coluna(decisao, "indice_de_espaco");
  const avaliada = coluna(decisao, "avaliada");
  return ufs.map((uf, i) => ({
    uf: String(uf),
    codigo: String(codigos[i]),
    carteira: Number(carteira[i]),
    indice: avaliada[i] ? /** @type {number} */ (espaco[i]) : null,
  }));
}

/**
 * PT: As UFs na ordem da carteira PJ, da maior para a menor, para as linhas
 *     da matriz: os mercados grandes ficam em cima.
 * EN: States by PJ portfolio, largest first, for the heatmap rows.
 *
 * @param {ArquivoDeDados} porUf
 * @returns {string[]}
 */
export function ufsPorCarteira(porUf) {
  const ufs = coluna(porUf, "uf");
  const carteira = coluna(porUf, "carteira_pj");
  return ufs
    .map((uf, i) => ({ uf: String(uf), carteira: Number(carteira[i]) }))
    .sort((a, b) => b.carteira - a.carteira)
    .map(({ uf }) => uf);
}
