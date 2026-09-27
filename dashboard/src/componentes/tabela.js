/**
 * PT: Tabela de dados, em vidro regular.
 *
 *     Números à direita, com algarismos tabulares e com unidade, para
 *     alinharem em coluna. O cabeçalho é translúcido. A linha sob o mouse
 *     ganha um fundo azul leve, que só ajuda a seguir a linha: o destaque
 *     por valor vem da ordenação e do filtro, e nunca da cor de fundo.
 *
 *     Toda visão com gráfico tem uma tabela com os mesmos números (RF-G06).
 *     Em tela estreita a tabela rola na horizontal, dentro de uma região
 *     que recebe foco pelo teclado.
 *
 * EN: Data table on regular glass: right-aligned tabular numbers with units,
 *     translucent header, subtle row hover. Scrolls horizontally inside a
 *     keyboard-focusable region on narrow screens.
 */

import { elemento } from "../dom.js";

let contador = 0;

/**
 * @template T
 * @typedef {object} Coluna
 * @property {string} titulo
 * @property {"texto" | "numero"} [tipo] Número vai à direita / numbers align right
 * @property {(linha: T) => string | Node} celula O conteúdo da célula / cell content
 */

/**
 * @template T
 * @typedef {object} OpcoesDaTabela
 * @property {string} legenda O que a tabela mostra, como o título do gráfico / caption
 * @property {Coluna<T>[]} colunas
 * @property {T[]} linhas
 * @property {number} [colunaDeTitulo] A coluna que nomeia a linha / row header column
 */

/**
 * PT: Monta a tabela. A primeira coluna nomeia cada linha, e vira cabeçalho
 *     de linha para leitores de tela.
 * EN: Builds the table; the first column becomes the row header.
 *
 * @template T
 * @param {OpcoesDaTabela<T>} opcoes
 * @returns {HTMLDivElement}
 */
export function tabela({ legenda, colunas, linhas, colunaDeTitulo = 0 }) {
  contador += 1;
  const id = `tabela-${contador}`;
  const classeDa = (/** @type {Coluna<T>} */ coluna) =>
    coluna.tipo === "numero" ? "tabela__numero" : "";

  const cabecalho = elemento("thead", {}, [
    elemento(
      "tr",
      {},
      colunas.map((coluna) =>
        elemento("th", {
          classe: classeDa(coluna),
          texto: coluna.titulo,
          atributos: { scope: "col" },
        }),
      ),
    ),
  ]);
  const corpo = elemento(
    "tbody",
    {},
    linhas.map((linha) =>
      elemento(
        "tr",
        {},
        colunas.map((coluna, i) =>
          i === colunaDeTitulo
            ? elemento("th", { classe: classeDa(coluna), atributos: { scope: "row" } }, [
                coluna.celula(linha),
              ])
            : elemento("td", { classe: classeDa(coluna) }, [coluna.celula(linha)]),
        ),
      ),
    ),
  );

  return elemento(
    "div",
    {
      classe: "tabela",
      atributos: { role: "region", "aria-labelledby": id, tabindex: "0" },
    },
    [
      elemento("table", {}, [
        elemento("caption", { classe: "tabela__legenda", texto: legenda, atributos: { id } }),
        cabecalho,
        corpo,
      ]),
    ],
  );
}
