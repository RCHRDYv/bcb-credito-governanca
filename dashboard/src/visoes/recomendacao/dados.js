/**
 * PT: Os números da Tela 4 (#71), lidos do `decisao.json`, que sai do
 *     `mrt_decisao`, o mesmo mart de `docs/recomendacao.md`.
 *
 *     O site não decide nada: o mart dá o quadrante, os dois custos e o
 *     alerta de cada célula (ADR 0014). Aqui só se agrupa por quadrante, se
 *     soma e se separa o que ficou fora da matriz e por quê.
 *
 * EN: Screen 4's numbers, from the decision mart's export. The site only
 *     groups by quadrant, sums, and separates the cells left out.
 */

import { quadranteDoMart } from "../../componentes/etiqueta-de-quadrante.js";

/** @typedef {import("../../dados/carregar.js").ArquivoDeDados} ArquivoDeDados */
/** @typedef {import("../../componentes/etiqueta-de-quadrante.js").Quadrante} Quadrante */

/**
 * @typedef {object} Celula
 * @property {string} uf
 * @property {string} codigo O código da modalidade / modality code
 * @property {string} modalidade O nome do BCB / BCB name
 * @property {Quadrante} quadrante
 * @property {number} carteira Em reais / in reais
 * @property {number} carteiraPorEmpresa
 * @property {number} indiceDeEspaco Carteira por empresa sobre a mediana / ratio to median
 * @property {number} desvioDoRisco Variação da taxa da UF menos a do país, em fração / fraction
 * @property {number} taxa Taxa de inadimplência / default rate
 * @property {number} variacao Variação da taxa em 6 meses / 6-month change
 * @property {number} variacaoPais
 * @property {number | null} custoDeNaoEntrar Em reais; só onde o espaço é alto / only where space is high
 * @property {number | null} custoDoRisco Em reais / in reais
 * @property {boolean} alerta O alerta antecipado / early warning
 */

/**
 * @typedef {object} ResumoDoQuadrante
 * @property {Quadrante} quadrante
 * @property {number} celulas
 * @property {number} carteira
 * @property {number} custoDeNaoEntrar
 * @property {number} custoDoRisco
 * @property {number} alertas
 */

/**
 * @typedef {object} Fora
 * @property {string} motivo Como no mart / as in the mart
 * @property {number} celulas
 * @property {number} carteira
 */

/** PT: a ordem dos quadrantes, a do resumo do relatório / EN: report order */
export const ORDEM = /** @type {const} */ (["entrar", "observar", "nao-entrar", "manter"]);

/**
 * PT: Por qual custo cada quadrante se ordena, como no relatório: onde há
 *     espaço e o risco não piora, pelo custo de não entrar; nos outros, pelo
 *     custo do risco.
 * EN: Each quadrant's sort cost, as in the report.
 *
 * @type {Record<Quadrante, "custoDeNaoEntrar" | "custoDoRisco">}
 */
const ORDENAR_POR = {
  entrar: "custoDeNaoEntrar",
  observar: "custoDoRisco",
  "nao-entrar": "custoDoRisco",
  manter: "custoDoRisco",
};

/**
 * @template T
 * @param {ArquivoDeDados} arquivo
 * @param {string} nome
 * @returns {T[]}
 */
function coluna(arquivo, nome) {
  const valores = arquivo.colunas[nome];
  if (!valores) throw new Error(`Coluna fora do arquivo: ${arquivo.arquivo}, ${nome}`);
  return /** @type {T[]} */ (valores);
}

/**
 * PT: As células avaliadas, as que têm quadrante.
 * EN: Evaluated cells, the ones with a quadrant.
 *
 * @param {ArquivoDeDados} decisao
 * @returns {Celula[]}
 */
export function celulasAvaliadas(decisao) {
  /** @type {(nome: string) => any[]} */
  const c = (nome) => coluna(decisao, nome);
  const avaliada = c("avaliada");
  /** @type {Celula[]} */
  const celulas = [];
  avaliada.forEach((sim, i) => {
    if (sim !== true) return;
    const quadrante = quadranteDoMart(String(c("quadrante")[i]));
    const numeroOuNulo = (/** @type {unknown} */ v) => (v === null ? null : Number(v));
    celulas.push({
      uf: String(c("uf")[i]),
      codigo: String(c("codigo_modalidade")[i]),
      modalidade: String(c("modalidade")[i]),
      quadrante,
      carteira: Number(c("carteira_ativa")[i]),
      carteiraPorEmpresa: Number(c("carteira_por_empresa")[i]),
      indiceDeEspaco: Number(c("indice_de_espaco")[i]),
      desvioDoRisco:
        Number(c("variacao_taxa_inadimplencia")[i]) - Number(c("variacao_taxa_pais")[i]),
      taxa: Number(c("taxa_inadimplencia")[i]),
      variacao: Number(c("variacao_taxa_inadimplencia")[i]),
      variacaoPais: Number(c("variacao_taxa_pais")[i]),
      custoDeNaoEntrar: numeroOuNulo(c("custo_de_nao_entrar")[i]),
      custoDoRisco: numeroOuNulo(c("custo_do_risco")[i]),
      alerta: c("alerta_antecipado")[i] === true,
    });
  });
  return celulas;
}

/**
 * PT: O resumo de cada quadrante, na ordem do relatório.
 * EN: Each quadrant's summary, in report order.
 *
 * @param {Celula[]} celulas
 * @returns {ResumoDoQuadrante[]}
 */
export function resumoPorQuadrante(celulas) {
  return ORDEM.map((quadrante) => {
    const doQuadrante = celulas.filter((c) => c.quadrante === quadrante);
    const somar = (/** @type {(c: Celula) => number | null} */ valor) =>
      doQuadrante.reduce((soma, c) => soma + (valor(c) ?? 0), 0);
    return {
      quadrante,
      celulas: doQuadrante.length,
      carteira: somar((c) => c.carteira),
      custoDeNaoEntrar: somar((c) => c.custoDeNaoEntrar),
      custoDoRisco: somar((c) => c.custoDoRisco),
      alertas: doQuadrante.filter((c) => c.alerta).length,
    };
  });
}

/**
 * PT: As células de um quadrante, na ordem do relatório: do custo maior
 *     para o menor.
 * EN: A quadrant's cells, largest cost first, as in the report.
 *
 * @param {Celula[]} celulas
 * @param {Quadrante} quadrante
 * @returns {Celula[]}
 */
export function celulasDoQuadrante(celulas, quadrante) {
  const custo = ORDENAR_POR[quadrante];
  return celulas
    .filter((c) => c.quadrante === quadrante)
    .sort((a, b) => (b[custo] ?? 0) - (a[custo] ?? 0));
}

/**
 * PT: As células que ficaram fora da matriz, por motivo, do motivo com mais
 *     células para o com menos (RF-403).
 * EN: Cells left out of the matrix, by reason.
 *
 * @param {ArquivoDeDados} decisao
 * @returns {Fora[]}
 */
export function foraDaMatriz(decisao) {
  const avaliada = coluna(decisao, "avaliada");
  const motivos = coluna(decisao, "motivo_nao_avaliada");
  const carteira = coluna(decisao, "carteira_ativa");
  /** @type {Map<string, Fora>} */
  const porMotivo = new Map();
  avaliada.forEach((sim, i) => {
    if (sim === true) return;
    const motivo = String(motivos[i]);
    const atual = porMotivo.get(motivo) ?? { motivo, celulas: 0, carteira: 0 };
    atual.celulas += 1;
    atual.carteira += Number(carteira[i]);
    porMotivo.set(motivo, atual);
  });
  return [...porMotivo.values()].sort((a, b) => b.celulas - a.celulas);
}

/**
 * PT: O custo de errar nas duas direções do ADR 0014, decisão 5:
 *     - não entrar onde a matriz diz Entrar custa a carteira que faltaria
 *       para chegar à mediana nessas células;
 *     - entrar onde o risco piora, em Observar e Não entrar, custa o aumento
 *       da carteira inadimplida atribuível à piora.
 *     O segundo número soma dois quadrantes do resumo de
 *     `docs/recomendacao.md` (decidido em 2026-10-06, na revisão da #71).
 * EN: The cost of being wrong both ways: not entering where the matrix says
 *     Enter, and entering where risk worsens (Watch plus Don't enter).
 *
 * @param {ResumoDoQuadrante[]} resumo
 * @returns {{ naoEntrar: number, risco: number }}
 */
export function custoDeErrar(resumo) {
  const de = (/** @type {Quadrante} */ q) => {
    const r = resumo.find((item) => item.quadrante === q);
    if (!r) throw new Error(`Quadrante fora do resumo: ${q}`);
    return r;
  };
  return {
    naoEntrar: de("entrar").custoDeNaoEntrar,
    risco: de("observar").custoDoRisco + de("nao-entrar").custoDoRisco,
  };
}

/**
 * PT: O maior erro da reconstrução do número de empresas, em qualquer UF e
 *     retrato, em fração (ADR 0009). Vai na fronteira do dado.
 * EN: Largest error of the reconstructed company count, as a fraction.
 *
 * @param {ArquivoDeDados} erro O `erro_da_reconstrucao.json`
 * @returns {number}
 */
export function maiorErroDaReconstrucao(erro) {
  return Math.max(...coluna(erro, "erro_relativo").map((v) => Math.abs(Number(v))));
}
