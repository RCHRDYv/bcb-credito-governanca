/**
 * PT: Carregador dos arquivos do contrato (#66).
 *
 *     O site não tem banco nem conexão: lê os JSON que a exportação grava em
 *     `public/data/`, e o contrato (`contrato-dos-dados.yml`) diz o que cada
 *     um traz. Cada visão carrega só os arquivos que usa (RF-G11), e este
 *     módulo garante três coisas:
 *     - o mesmo arquivo é buscado uma vez só, mesmo que duas visões peçam;
 *     - a falha vira um `ErroDeCarga` com o motivo, rede ou formato, que a
 *       visão transforma no estado de erro com o botão de tentar de novo;
 *     - a falha não fica guardada, e tentar de novo busca outra vez.
 *
 *     A conferência completa do formato é do CI, contra o contrato. Aqui só
 *     se confere o mínimo para não quebrar a tela: que o arquivo é JSON e
 *     traz o próprio nome.
 *
 * EN: Loader for the contract files. The site reads the JSON files the
 *     export writes to `public/data/`. Each file is fetched once, failures
 *     become an `ErroDeCarga` with a network or format reason, and failures
 *     are not cached so retrying fetches again. Full format checking is CI's
 *     job; here only the minimum is checked.
 */

/**
 * PT: A pasta dos arquivos, relativa à página, como o `base: "./"` do Vite.
 * EN: Data folder, relative to the page, like Vite's `base: "./"`.
 */
const PASTA = "./data/";

/** @typedef {string | number | boolean | null} Valor */

/**
 * PT: Um arquivo de dados, por coluna, como o contrato define.
 * EN: A column-oriented data file, as the contract defines.
 *
 * @typedef {object} ArquivoDeDados
 * @property {string} arquivo Nome do arquivo / file name
 * @property {string} data_base Data-base da exportação, AAAA-MM-DD / export data-base
 * @property {Record<string, Valor[]>} colunas Valores por coluna / values by column
 */

/**
 * PT: Um registro do `ontologia.json`.
 * EN: One `ontologia.json` record.
 *
 * @typedef {object} Conceito
 * @property {string} ref Referência do contrato / contract reference
 * @property {string} id
 * @property {"conceito" | "dimensao" | "fonte_de_dado" | "aviso" | "quebra"} tipo
 * @property {string | null} rotulo
 * @property {string | null} definicao
 * @property {string | null} fonte
 * @property {string | null} confianca
 * @property {string | null} nota_de_escopo
 * @property {string} [codigo] Código da modalidade / modality code
 * @property {string | null} [explicacao] Explicação em palavras comuns, só nas modalidades (#69) / plain-language explanation
 * @property {string | null} [explicacao_confianca] Confiança da explicação / its confidence
 * @property {string | null} [explicacao_fonte] Fonte da explicação / its source
 * @property {string} [data] Data da quebra da série / series break date
 */

/**
 * PT: O `ontologia.json`: os conceitos e, por arquivo e coluna, a
 *     referência da definição (um conceito ou um ADR), para o site ir do
 *     número à definição (RF-G07).
 * EN: The ontology file: concepts and each column's definition reference.
 *
 * @typedef {object} Ontologia
 * @property {"ontologia.json"} arquivo
 * @property {Conceito[]} conceitos
 * @property {Record<string, Record<string, string>>} colunas
 */

/**
 * PT: O `manifesto.json`: a data-base, os parâmetros da decisão e, por
 *     arquivo, as linhas, o sha256 e as visões que o usam.
 * EN: The manifest: data-base, decision parameters and per-file metadata.
 *
 * @typedef {object} Manifesto
 * @property {"manifesto.json"} arquivo
 * @property {number} versao_do_contrato
 * @property {string} data_base
 * @property {Record<string, number>} parametros_da_decisao
 * @property {number[]} visoes_do_manifesto
 * @property {{ arquivo: string, linhas: number, sha256: string, visoes: number[] }[]} arquivos
 */

/**
 * PT: Falha ao carregar um arquivo. O `motivo` diz à visão o que mostrar:
 *     "rede" quando o arquivo não chegou, "formato" quando chegou quebrado.
 * EN: Load failure; `motivo` is "rede" (did not arrive) or "formato"
 *     (arrived broken).
 */
export class ErroDeCarga extends Error {
  /**
   * @param {string} arquivo
   * @param {"rede" | "formato"} motivo
   * @param {string} mensagem
   * @param {unknown} [causa]
   */
  constructor(arquivo, motivo, mensagem, causa) {
    super(mensagem, { cause: causa });
    this.name = "ErroDeCarga";
    this.arquivo = arquivo;
    this.motivo = motivo;
  }
}

/** @type {Map<string, Promise<object>>} */
const guardados = new Map();

/**
 * PT: Busca e lê um arquivo da pasta de dados, e confere que ele é um
 *     objeto JSON que traz o próprio nome.
 * EN: Fetches and parses one data folder file, checking it is a JSON object
 *     carrying its own name.
 *
 * @param {string} arquivo
 * @returns {Promise<object>}
 */
async function buscar(arquivo) {
  /** @type {Response} */
  let resposta;
  try {
    resposta = await fetch(`${PASTA}${arquivo}`);
  } catch (erro) {
    throw new ErroDeCarga(arquivo, "rede", `Não foi possível buscar ${arquivo}.`, erro);
  }
  if (!resposta.ok) {
    throw new ErroDeCarga(arquivo, "rede", `${arquivo} respondeu com o status ${resposta.status}.`);
  }

  /** @type {unknown} */
  let conteudo;
  try {
    conteudo = await resposta.json();
  } catch (erro) {
    throw new ErroDeCarga(arquivo, "formato", `${arquivo} não é um JSON válido.`, erro);
  }
  if (
    typeof conteudo !== "object" ||
    conteudo === null ||
    /** @type {{ arquivo?: unknown }} */ (conteudo).arquivo !== arquivo
  ) {
    throw new ErroDeCarga(
      arquivo,
      "formato",
      `${arquivo} não traz o próprio nome no campo arquivo.`,
    );
  }
  return conteudo;
}

/**
 * PT: Carrega um arquivo uma vez só. A promessa fica guardada enquanto dá
 *     certo; se falhar, é esquecida, para o tentar de novo buscar outra vez.
 * EN: Loads a file once; a failed promise is forgotten so retrying works.
 *
 * @param {string} arquivo
 * @returns {Promise<object>}
 */
function carregarUmaVez(arquivo) {
  const guardado = guardados.get(arquivo);
  if (guardado) return guardado;
  const promessa = buscar(arquivo);
  guardados.set(arquivo, promessa);
  promessa.catch(() => guardados.delete(arquivo));
  return promessa;
}

/**
 * PT: Carrega um arquivo de dados do contrato, como o `decisao.json`.
 * EN: Loads one contract data file, such as `decisao.json`.
 *
 * @param {string} arquivo
 * @returns {Promise<ArquivoDeDados>}
 */
export async function carregar(arquivo) {
  const conteudo = /** @type {Partial<ArquivoDeDados>} */ (await carregarUmaVez(arquivo));
  if (typeof conteudo.colunas !== "object" || conteudo.colunas === null) {
    throw new ErroDeCarga(arquivo, "formato", `${arquivo} não traz as colunas.`);
  }
  return /** @type {ArquivoDeDados} */ (conteudo);
}

/**
 * PT: Carrega o `ontologia.json`.
 * EN: Loads `ontologia.json`.
 *
 * @returns {Promise<Ontologia>}
 */
export async function carregarOntologia() {
  return /** @type {Ontologia} */ (await carregarUmaVez("ontologia.json"));
}

/**
 * PT: Carrega o `manifesto.json`.
 * EN: Loads `manifesto.json`.
 *
 * @returns {Promise<Manifesto>}
 */
export async function carregarManifesto() {
  return /** @type {Manifesto} */ (await carregarUmaVez("manifesto.json"));
}

/**
 * PT: Converte as colunas em linhas, uma por registro, para o componente de
 *     tabela. Os gráficos leem as colunas direto, pelo `dataset` do ECharts.
 * EN: Turns columns into one object per row, for the table component.
 *
 * @param {ArquivoDeDados} dados
 * @returns {Record<string, Valor>[]}
 */
export function emLinhas(dados) {
  const nomes = Object.keys(dados.colunas);
  const total = nomes.length ? dados.colunas[nomes[0]].length : 0;
  return Array.from({ length: total }, (_, indice) =>
    Object.fromEntries(nomes.map((nome) => [nome, dados.colunas[nome][indice]])),
  );
}
