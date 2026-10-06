/**
 * PT: Os dados da Tela 2, a partir dos arquivos do contrato (#70).
 *
 *     São funções puras: recebem os arquivos já carregados e devolvem o que
 *     a tela desenha. O site não calcula nenhuma taxa: a de inadimplência da
 *     UF e a do país, as variações em seis meses, o quadrante, o custo do
 *     risco e o alerta antecipado vêm prontos do `mrt_decisao` (ADR 0007 e
 *     ADR 0014). Aqui só se soma, conta, ordena e tira a diferença entre duas
 *     colunas da mesma linha, na mesma unidade.
 *
 *     - **A piora contra o país** é a variação da UF menos a do país, em
 *       pontos percentuais. Quem decide se a UF piorou mais que o país é o
 *       quadrante do mart, e não o sinal da diferença: os dois concordam, e
 *       o teste confere.
 *     - **Só as UFs comparadas** recebem cor, entram no ranking e somam o
 *       custo do risco, porque o ADR 0014 não compara células pequenas demais
 *       para dar um número estável. A modalidade não tem "todas": a taxa de
 *       inadimplência não se soma entre modalidades (revisão do mockup, em
 *       2026-10-06).
 *     - **A série mensal** vem do `carteira_mensal_pj.json`, com a taxa de
 *       inadimplência e a de ativo problemático de cada mês.
 *
 * EN: Screen 2 data from the contract files, as pure functions. Rates,
 *     changes, quadrant, risk cost and early warning come from the mart; this
 *     module only sums, counts, sorts and subtracts two same-row columns.
 */

import { quadranteDoMart } from "../../componentes/etiqueta-de-quadrante.js";
import { UFS } from "../../graficos/ufs.js";

/** @typedef {import("../../dados/carregar.js").ArquivoDeDados} ArquivoDeDados */
/** @typedef {import("../../dados/carregar.js").Ontologia} Ontologia */
/** @typedef {import("../../componentes/etiqueta-de-quadrante.js").Quadrante} Quadrante */

/**
 * PT: Comparada com o país; abaixo do corte de materialidade; numa
 *     modalidade com poucas UFs acima do corte; ou sem carteira.
 * EN: Compared with the country; below the cut; in a thin modality; or none.
 *
 * @typedef {"comparada" | "abaixo-do-corte" | "poucas-ufs" | "sem-carteira"} Situacao
 */

/**
 * @typedef {object} LinhaDoRisco
 * @property {string} uf Sigla / abbreviation
 * @property {string} nome Nome da UF / state name
 * @property {number | null} carteira Carteira ativa da célula, em reais / portfolio
 * @property {number | null} taxa Taxa de inadimplência na data-base / delinquency rate
 * @property {number | null} taxaAnterior A de seis meses antes / six months earlier
 * @property {number | null} variacao A variação em seis meses, em fração / change
 * @property {number | null} taxaPais A taxa do país na modalidade / national rate
 * @property {number | null} variacaoPais A variação do país / national change
 * @property {number | null} contraOPais A variação da UF menos a do país, só das comparadas / change minus national change
 * @property {boolean} piorando Piorou mais que o país, pelo quadrante do mart / worsened more than the country
 * @property {boolean} alerta O alerta antecipado do mart / early warning
 * @property {number | null} aberturaContraOPais Quanto a distância até o ativo problemático abriu a mais que no país / gap widening against the country
 * @property {Quadrante | null} quadrante
 * @property {number | null} custoDoRisco Em reais / BRL
 * @property {Situacao} situacao
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
 *     A primeira com UF comparável é a que a tela abre.
 * EN: Modalities with national portfolio and compared states, largest first.
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
 * PT: A linha de uma UF sem carteira na modalidade.
 * EN: A state with no portfolio in the modality.
 *
 * @param {string} uf
 * @param {string} nome
 * @returns {LinhaDoRisco}
 */
function vazia(uf, nome) {
  return {
    uf,
    nome,
    carteira: null,
    taxa: null,
    taxaAnterior: null,
    variacao: null,
    taxaPais: null,
    variacaoPais: null,
    contraOPais: null,
    piorando: false,
    alerta: false,
    aberturaContraOPais: null,
    quadrante: null,
    custoDoRisco: null,
    situacao: "sem-carteira",
  };
}

/**
 * PT: As 27 linhas de uma modalidade, a partir das células do
 *     `decisao.json`. A UF sem carteira nela não tem célula no arquivo.
 * EN: The modality's 27 rows from the decisao.json cells.
 *
 * @param {ArquivoDeDados} decisao
 * @param {string} codigo
 * @returns {LinhaDoRisco[]}
 */
export function linhas(decisao, codigo) {
  const codigos = coluna(decisao, "codigo_modalidade");
  const ufs = coluna(decisao, "uf");
  const carteira = coluna(decisao, "carteira_ativa");
  const taxa = coluna(decisao, "taxa_inadimplencia");
  const anterior = coluna(decisao, "taxa_inadimplencia_anterior");
  const variacao = coluna(decisao, "variacao_taxa_inadimplencia");
  const taxaPais = coluna(decisao, "taxa_pais");
  const variacaoPais = coluna(decisao, "variacao_taxa_pais");
  const avaliada = coluna(decisao, "avaliada");
  const motivo = coluna(decisao, "motivo_nao_avaliada");
  const quadrante = coluna(decisao, "quadrante");
  const custo = coluna(decisao, "custo_do_risco");
  const alerta = coluna(decisao, "alerta_antecipado");
  const abertura = coluna(decisao, "variacao_distancia");
  const aberturaPais = coluna(decisao, "variacao_distancia_pais");

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
    const v = /** @type {number | null} */ (variacao[i]);
    const vp = /** @type {number | null} */ (variacaoPais[i]);
    const a = /** @type {number | null} */ (abertura[i]);
    const ap = /** @type {number | null} */ (aberturaPais[i]);
    const q = comparada ? quadranteDoMart(String(quadrante[i])) : null;
    return {
      uf: uf.sigla,
      nome: uf.nome,
      carteira: /** @type {number} */ (carteira[i]),
      taxa: /** @type {number | null} */ (taxa[i]),
      taxaAnterior: /** @type {number | null} */ (anterior[i]),
      variacao: v,
      taxaPais: /** @type {number | null} */ (taxaPais[i]),
      variacaoPais: vp,
      contraOPais: comparada && v !== null && vp !== null ? v - vp : null,
      piorando: q === "observar" || q === "nao-entrar",
      alerta: comparada && Boolean(alerta[i]),
      aberturaContraOPais: comparada && a !== null && ap !== null ? a - ap : null,
      quadrante: q,
      custoDoRisco: comparada ? /** @type {number | null} */ (custo[i]) : null,
      situacao,
    };
  });
}

/**
 * @typedef {object} ResumoDoRisco
 * @property {number | null} taxaPais
 * @property {number | null} variacaoPais
 * @property {number} comparadas
 * @property {number} piorando UFs que pioraram mais que o país / states worse than the country
 * @property {number} alertas UFs com alerta antecipado / states with early warning
 * @property {number} custo O custo do risco das que pioraram, somado / summed risk cost
 */

/**
 * PT: O resumo da modalidade: a taxa e a variação do país, quantas UFs
 *     pioraram mais que ele, quantas têm alerta e o custo do risco das que
 *     pioraram, somado.
 * EN: The modality summary: national rate and change, worsening states,
 *     early warnings and the summed risk cost of worsening states.
 *
 * @param {LinhaDoRisco[]} linhasDoRisco
 * @returns {ResumoDoRisco}
 */
export function resumo(linhasDoRisco) {
  const comparadas = linhasDoRisco.filter((linha) => linha.situacao === "comparada");
  const piorando = comparadas.filter((linha) => linha.piorando);
  const comPais = linhasDoRisco.find((linha) => linha.taxaPais !== null);
  return {
    taxaPais: comPais?.taxaPais ?? null,
    variacaoPais: comPais?.variacaoPais ?? null,
    comparadas: comparadas.length,
    piorando: piorando.length,
    alertas: comparadas.filter((linha) => linha.alerta).length,
    custo: piorando.reduce((soma, linha) => soma + (linha.custoDoRisco ?? 0), 0),
  };
}

/**
 * PT: Os itens do ranking: as UFs que pioraram mais que o país, pela
 *     diferença, com o marcador de alerta.
 * EN: Ranking items: worsening states by their excess change, with the
 *     early-warning marker.
 *
 * @param {LinhaDoRisco[]} linhasDoRisco
 * @returns {{ rotulo: string, valor: number, chave: string, marcada: boolean }[]}
 */
export function ranking(linhasDoRisco) {
  return linhasDoRisco
    .filter((linha) => linha.piorando && linha.contraOPais !== null)
    .map((linha) => ({
      rotulo: linha.nome,
      valor: /** @type {number} */ (linha.contraOPais),
      chave: linha.uf,
      marcada: linha.alerta,
    }));
}

/**
 * PT: As linhas na ordem da tabela e do CSV: da maior piora contra o país
 *     para a menor, e as que ficam fora da comparação no fim.
 * EN: Table and CSV order: largest excess change first, uncompared last.
 *
 * @param {LinhaDoRisco[]} linhasDoRisco
 * @returns {LinhaDoRisco[]}
 */
export function ordenar(linhasDoRisco) {
  return [...linhasDoRisco].sort(
    (a, b) =>
      (b.contraOPais ?? Number.NEGATIVE_INFINITY) - (a.contraOPais ?? Number.NEGATIVE_INFINITY),
  );
}

/**
 * @typedef {object} CelulaDoRisco
 * @property {string} uf
 * @property {string} codigo
 * @property {number | null} contraOPais `null` fora da comparação / null outside the comparison
 */

/**
 * PT: As células da matriz de UF por modalidade, com a piora contra o país
 *     das comparadas.
 * EN: State-by-modality cells, with the excess change of compared ones.
 *
 * @param {ArquivoDeDados} decisao
 * @returns {CelulaDoRisco[]}
 */
export function celulasDaMatriz(decisao) {
  const ufs = coluna(decisao, "uf");
  const codigos = coluna(decisao, "codigo_modalidade");
  const variacao = coluna(decisao, "variacao_taxa_inadimplencia");
  const variacaoPais = coluna(decisao, "variacao_taxa_pais");
  const avaliada = coluna(decisao, "avaliada");
  return ufs.map((uf, i) => ({
    uf: String(uf),
    codigo: String(codigos[i]),
    contraOPais: avaliada[i]
      ? /** @type {number} */ (variacao[i]) - /** @type {number} */ (variacaoPais[i])
      : null,
  }));
}

/**
 * PT: As UFs na ordem da carteira da decisão, somada entre as modalidades,
 *     da maior para a menor, para as linhas da matriz.
 * EN: States by total portfolio across modalities, largest first.
 *
 * @param {ArquivoDeDados} decisao
 * @returns {string[]}
 */
export function ufsPorCarteira(decisao) {
  const ufs = coluna(decisao, "uf");
  const carteira = coluna(decisao, "carteira_ativa");
  /** @type {Map<string, number>} */
  const soma = new Map();
  ufs.forEach((uf, i) => {
    soma.set(String(uf), (soma.get(String(uf)) ?? 0) + Number(carteira[i]));
  });
  return [...soma.entries()].sort((a, b) => b[1] - a[1]).map(([uf]) => uf);
}

/**
 * @typedef {object} SerieDaUf
 * @property {string[]} meses `aaaa-mm-dd`
 * @property {(number | null)[]} inadimplencia
 * @property {(number | null)[]} ativoProblematico
 */

/**
 * PT: A série mensal de uma UF numa modalidade: a taxa de inadimplência e a
 *     de ativo problemático, na ordem dos meses.
 * EN: A state's monthly series in a modality, in month order.
 *
 * @param {ArquivoDeDados} mensal O `carteira_mensal_pj.json`
 * @param {string} uf
 * @param {string} codigo
 * @returns {SerieDaUf}
 */
export function serieDaUf(mensal, uf, codigo) {
  const datas = coluna(mensal, "data_base");
  const ufs = coluna(mensal, "uf");
  const codigos = coluna(mensal, "codigo_modalidade");
  const inadimplencia = coluna(mensal, "taxa_inadimplencia");
  const ativo = coluna(mensal, "taxa_ativo_problematico");
  const pontos = datas
    .map((data, i) => ({ data: String(data), i }))
    .filter(({ i }) => ufs[i] === uf && codigos[i] === codigo)
    .sort((a, b) => a.data.localeCompare(b.data));
  return {
    meses: pontos.map(({ data }) => data),
    inadimplencia: pontos.map(({ i }) => /** @type {number | null} */ (inadimplencia[i])),
    ativoProblematico: pontos.map(({ i }) => /** @type {number | null} */ (ativo[i])),
  };
}

/**
 * PT: A data da mudança de critério do ativo problemático, pela ontologia,
 *     que a lê de `ontology/dimensoes.yml` (RF-203).
 * EN: The problem-asset criterion break date, from the ontology.
 *
 * @param {Ontologia} ontologia
 * @returns {string | null} `aaaa-mm-dd`
 */
export function dataDaQuebra(ontologia) {
  const quebra = ontologia.conceitos.find((c) => c.id === "criterio_ativo_problematico");
  return quebra?.data ?? null;
}

/**
 * PT: Se a janela da decisão cruza a mudança de critério: o mês anterior
 *     fica antes da mudança, e a data-base, nela ou depois (RF-203). Só
 *     compara datas no formato `aaaa-mm-dd`.
 * EN: Whether the decision window crosses the criterion break.
 *
 * @param {string} anterior
 * @param {string} dataBase
 * @param {string | null} quebra
 * @returns {boolean}
 */
export function janelaCruzaAQuebra(anterior, dataBase, quebra) {
  return quebra !== null && anterior < quebra && quebra <= dataBase;
}
