/**
 * PT: A tabela da Tela 1 e o download dos números em CSV.
 *
 *     A tabela tem os mesmos números dos gráficos (RF-G06) e é uma das
 *     formas de ver o território, ao lado do mapa, da grade e da matriz:
 *     troca dentro do cartão, e não alonga a página (ADR 0022, decisão 5).
 *     O nome de cada UF é um botão, que escolhe a UF pelo teclado.
 *
 *     O CSV serve o RevOps, que leva os números de uma UF e de uma
 *     modalidade para o plano dele. Vai com ponto e vírgula e vírgula
 *     decimal, como o Excel em português abre sem configurar nada, e com a
 *     marca de UTF-8 no começo, para os acentos chegarem certos.
 *
 * EN: Screen 1 table and CSV download. The table carries the charts' numbers
 *     and is one of the territory card's forms; state names are buttons. The CSV uses
 *     semicolons, decimal commas and a UTF-8 BOM, as Portuguese Excel opens it.
 */

import { botao } from "../../componentes/botao.js";
import { tabela } from "../../componentes/tabela.js";
import { baixarCsv, montarCsv, numeroDoCsv, textoDoCsv } from "../../dados/csv.js";
import { elemento } from "../../dom.js";
import { numero, reais, taxa } from "../../formatos.js";
import { t } from "../../textos/index.js";
import { posicao } from "./cor.js";

/** @typedef {import("./dados.js").LinhaDaVisao} LinhaDaVisao */
/** @typedef {import("../../textos/index.js").ChaveDeTexto} ChaveDeTexto */

/**
 * @typedef {object} OpcoesDaTabela
 * @property {LinhaDaVisao[]} linhasDaVisao
 * @property {boolean} todas Se o recorte é o de todas as modalidades / all-modalities cut
 * @property {string | null} escolhida A UF escolhida / chosen state
 * @property {string} legenda O que a tabela mostra / caption
 * @property {(linha: LinhaDaVisao) => string} situacao O motivo de quem fica fora / reason
 * @property {string} arquivo O nome do CSV / CSV file name
 */

/**
 * PT: O conteúdo do CSV, com os números crus: reais em reais inteiros e
 *     frações com seis casas, como nos arquivos do contrato.
 * EN: The CSV content with raw numbers, as in the contract files.
 *
 * @param {LinhaDaVisao[]} linhasDaVisao
 * @param {boolean} todas
 * @param {(linha: LinhaDaVisao) => string} situacao
 * @returns {string}
 */
export function csv(linhasDaVisao, todas, situacao) {
  /** @type {[ChaveDeTexto, (linha: LinhaDaVisao) => string][]} */
  const colunas = [
    ["tela1.coluna-uf", (l) => textoDoCsv(l.nome)],
    ["tela1.carteira-pj", (l) => numeroDoCsv(l.carteira, 0)],
    ...(todas
      ? /** @type {[ChaveDeTexto, (linha: LinhaDaVisao) => string][]} */ ([
          ["tela1.coluna-participacao", (l) => numeroDoCsv(l.participacao, 6)],
        ])
      : []),
    ["tela1.empresas", (l) => numeroDoCsv(l.empresas, 0)],
    ["tela1.carteira-por-empresa", (l) => numeroDoCsv(l.carteiraPorEmpresa, 0)],
    ["tela1.mediana-das-ufs", (l) => numeroDoCsv(l.mediana, 0)],
    ["tela1.indice-csv", (l) => numeroDoCsv(l.indice, 6)],
    ["tela1.coluna-custo", (l) => numeroDoCsv(l.custo, 0)],
    ["tela1.coluna-situacao", (l) => textoDoCsv(situacao(l))],
  ];
  return montarCsv(
    colunas.map(([chave, valor]) => [t(chave), valor]),
    linhasDaVisao,
  );
}

/**
 * PT: As linhas na ordem da tabela e do CSV: a carteira por empresa, da
 *     menor para a maior, com as UFs com mais espaço em cima, e as que ficam
 *     fora da comparação no fim.
 * EN: Table and CSV order: smallest per-company portfolio first.
 *
 * @param {LinhaDaVisao[]} linhasDaVisao
 * @returns {LinhaDaVisao[]}
 */
function ordenar(linhasDaVisao) {
  return [...linhasDaVisao].sort(
    (a, b) =>
      (a.carteiraPorEmpresa ?? Number.POSITIVE_INFINITY) -
      (b.carteiraPorEmpresa ?? Number.POSITIVE_INFINITY),
  );
}

/**
 * PT: O botão que baixa os números do recorte em CSV.
 * EN: The button that downloads the cut's numbers as CSV.
 *
 * @param {OpcoesDaTabela} opcoes
 * @returns {HTMLButtonElement}
 */
export function botaoDoCsv(opcoes) {
  return botao({
    texto: t("tela1.baixar-csv"),
    variante: "secundario",
    icone: "download",
    aoClicar: () =>
      baixarCsv(csv(ordenar(opcoes.linhasDaVisao), opcoes.todas, opcoes.situacao), opcoes.arquivo),
  });
}

/**
 * PT: A tabela, numa área que rola por dentro e recebe foco pelo teclado.
 * EN: The table, in a focusable area that scrolls inside.
 *
 * @param {OpcoesDaTabela} opcoes
 * @returns {HTMLElement}
 */
export function tabelaDaTela(opcoes) {
  const { linhasDaVisao, todas, escolhida, situacao } = opcoes;
  const ordenadas = ordenar(linhasDaVisao);
  const conteudo = tabela({
    legenda: opcoes.legenda,
    colunas: [
      {
        titulo: t("tela1.coluna-uf"),
        celula: (linha) =>
          elemento("button", {
            classe: "visao__uf",
            texto: linha.nome,
            atributos: {
              type: "button",
              "aria-pressed": String(linha.uf === escolhida),
              "data-uf": linha.uf,
            },
          }),
      },
      {
        titulo: t("tela1.carteira-pj"),
        tipo: "numero",
        celula: (linha) => (linha.carteira === null ? "–" : reais(linha.carteira)),
      },
      ...(todas
        ? [
            {
              titulo: t("tela1.coluna-participacao"),
              tipo: /** @type {const} */ ("numero"),
              celula: (/** @type {LinhaDaVisao} */ linha) =>
                linha.participacao === null ? "–" : taxa(linha.participacao, 1),
            },
          ]
        : []),
      {
        titulo: t("tela1.empresas"),
        tipo: "numero",
        celula: (linha) => (linha.empresas === null ? "–" : numero(linha.empresas, 0)),
      },
      {
        titulo: t("tela1.carteira-por-empresa"),
        tipo: "numero",
        celula: (linha) =>
          linha.carteiraPorEmpresa === null ? "–" : reais(linha.carteiraPorEmpresa),
      },
      {
        titulo: t("tela1.coluna-posicao"),
        celula: (linha) => (linha.indice === null ? situacao(linha) : posicao(linha.indice)),
      },
      {
        titulo: t("tela1.coluna-custo"),
        tipo: "numero",
        celula: (linha) => (linha.custo === null ? "–" : reais(linha.custo)),
      },
    ],
    linhas: ordenadas,
  });
  return elemento(
    "div",
    {
      classe: "visao__tabela",
      atributos: { tabindex: "0", role: "region", "aria-label": opcoes.legenda },
    },
    [conteudo],
  );
}
