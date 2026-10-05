/**
 * PT: O perfil de uma UF, no painel de detalhe da Tela 1 (revisão de
 *     2026-10-01).
 *
 *     Responde o que o executivo e o RevOps perguntam ao escolher uma UF: de
 *     que tamanho é o mercado, onde ela fica em relação à mediana, quanto
 *     crédito faltaria para chegar a ela e, por modalidade, onde está o
 *     espaço. Cada número tem a definição a um clique (RF-G07). A lista das
 *     modalidades leva à modalidade escolhida.
 *
 * EN: A state's profile in the detail panel: market size, position against
 *     the median, the gap in reais and, per modality, where the room is.
 *     Every number has its definition one click away; the modality list
 *     switches the filter.
 */

import { elemento } from "../../dom.js";
import { numero, reais, taxa } from "../../formatos.js";
import { t } from "../../textos/index.js";
import { posicao } from "./cor.js";
import { modalidadesDaUf, posicaoDaUf } from "./dados.js";

/** @typedef {import("./dados.js").LinhaDaVisao} LinhaDaVisao */
/** @typedef {import("../../dados/carregar.js").ArquivoDeDados} ArquivoDeDados */
/** @typedef {import("../../componentes/painel-de-detalhe.js").ConteudoDoDetalhe} ConteudoDoDetalhe */
/** @typedef {import("../../componentes/painel-de-detalhe.js").ItemDoDetalhe} ItemDoDetalhe */

/**
 * @typedef {object} OpcoesDoPerfil
 * @property {LinhaDaVisao} linha A UF escolhida, no recorte atual / chosen state
 * @property {LinhaDaVisao[]} linhasDaVisao As 27 do recorte / the cut's rows
 * @property {ArquivoDeDados} decisao Para as modalidades da UF / for the state's modalities
 * @property {boolean} todas Se o recorte é o de todas as modalidades / all-modalities cut
 * @property {string} modalidade O código escolhido, ou `todas` / chosen code
 * @property {string} subtitulo O recorte e a data-base / cut and date
 * @property {string} nota A ressalva do pé do painel / footer caveat
 * @property {(rotulo: string, coluna: string) => Node | undefined} comDefinicao
 * @property {(codigo: string) => void} aoEscolherModalidade
 */

/**
 * PT: A lista das modalidades da UF, da maior carteira para a menor, cada
 *     uma com a posição dela e um botão que escolhe a modalidade.
 * EN: The state's modalities, largest first, each a button that chooses it.
 *
 * @param {ArquivoDeDados} decisao
 * @param {string} uf
 * @param {string} atual
 * @param {(codigo: string) => void} aoEscolher
 * @returns {HTMLElement}
 */
function listaDeModalidades(decisao, uf, atual, aoEscolher) {
  const itens = modalidadesDaUf(decisao, uf).map((m) =>
    elemento("li", { classe: "perfil__modalidade" }, [
      elemento("button", {
        classe: "perfil__escolher",
        texto: m.nome,
        atributos: {
          type: "button",
          "data-modalidade": m.codigo,
          ...(m.codigo === atual ? { "aria-current": "true" } : {}),
        },
      }),
      elemento("span", { classe: "perfil__carteira", texto: reais(m.carteira) }),
      elemento("span", {
        classe: "perfil__posicao",
        texto: m.indice === null ? t("tela1.fora-da-comparacao") : posicao(m.indice),
      }),
    ]),
  );
  const lista = elemento("ul", { classe: "perfil__lista" }, itens);
  lista.addEventListener("click", (evento) => {
    const botao = /** @type {HTMLElement} */ (evento.target).closest("[data-modalidade]");
    const codigo = botao?.getAttribute("data-modalidade");
    if (codigo) aoEscolher(codigo);
  });
  return elemento("section", { classe: "perfil" }, [
    elemento("h3", { classe: "perfil__titulo", texto: t("tela1.modalidades-da-uf") }),
    lista,
  ]);
}

/**
 * PT: O conteúdo do painel de detalhe para a UF escolhida.
 * EN: The detail panel content for the chosen state.
 *
 * @param {OpcoesDoPerfil} opcoes
 * @returns {ConteudoDoDetalhe}
 */
export function perfilDaUf(opcoes) {
  const { linha, linhasDaVisao, todas, comDefinicao } = opcoes;
  /** @type {ItemDoDetalhe[]} */
  const itens = [];
  const rotuloDaCarteira = todas ? t("tela1.carteira-pj") : t("tela1.carteira-na-modalidade");

  if (linha.carteira !== null) {
    itens.push({
      chave: rotuloDaCarteira,
      valor: reais(linha.carteira),
      apoio: comDefinicao(rotuloDaCarteira, todas ? "carteira_pj" : "carteira_ativa"),
    });
  }
  if (linha.participacao !== null) {
    itens.push({
      chave: t("tela1.coluna-participacao"),
      valor: taxa(linha.participacao, 1),
      apoio: comDefinicao(t("tela1.coluna-participacao"), "participacao_na_carteira_pj"),
    });
  }
  if (linha.empresas !== null) {
    itens.push({
      chave: t("tela1.empresas"),
      valor: numero(linha.empresas, 0),
      apoio: comDefinicao(t("tela1.empresas"), "empresas"),
    });
  }
  if (linha.carteiraPorEmpresa !== null) {
    itens.push({
      chave: t("tela1.carteira-por-empresa"),
      valor: reais(linha.carteiraPorEmpresa),
      apoio: comDefinicao(t("tela1.carteira-por-empresa"), "carteira_por_empresa"),
    });
  }
  if (linha.indice !== null && linha.mediana !== null) {
    const lugar = posicaoDaUf(linhasDaVisao, linha.uf);
    itens.push({
      chave: t("tela1.coluna-posicao"),
      valor: posicao(linha.indice),
      apoio: comDefinicao(t("tela1.coluna-posicao"), "indice_de_espaco"),
    });
    if (lugar) {
      itens.push({
        chave: t("tela1.posicao"),
        valor: t("tela1.posicao-entre", { posicao: String(lugar.posicao), de: String(lugar.de) }),
      });
    }
  }
  if (linha.custo !== null) {
    itens.push({
      chave: t("tela1.custo-da-uf"),
      valor: reais(linha.custo),
      apoio: comDefinicao(t("tela1.custo-da-uf"), "custo_de_nao_entrar"),
    });
  }

  return {
    titulo: linha.nome,
    subtitulo: opcoes.subtitulo,
    itens,
    complemento: listaDeModalidades(
      opcoes.decisao,
      linha.uf,
      opcoes.modalidade,
      opcoes.aoEscolherModalidade,
    ),
    nota: opcoes.nota,
  };
}
