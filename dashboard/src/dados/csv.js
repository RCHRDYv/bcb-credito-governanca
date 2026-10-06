/**
 * PT: O CSV das visões (RF-G06): números crus, com vírgula decimal, e
 *     ponto e vírgula entre as colunas, como abre o Excel em português. O
 *     arquivo leva a marca de ordem de bytes, para os acentos chegarem
 *     certos.
 * EN: The views' CSV: raw numbers, decimal comma, semicolon-separated, with
 *     a byte order mark so accents survive in Excel.
 */

import { elemento } from "../dom.js";

/**
 * PT: Um número para o CSV, com vírgula decimal e sem separador de milhar.
 * EN: A CSV number, decimal comma, no thousands separator.
 *
 * @param {number | null} valor
 * @param {number} casas
 * @returns {string}
 */
export function numeroDoCsv(valor, casas) {
  if (valor === null) return "";
  return valor.toFixed(casas).replace(".", ",");
}

/**
 * PT: Um texto para o CSV, entre aspas quando precisa.
 * EN: A CSV text, quoted when needed.
 *
 * @param {string} texto
 * @returns {string}
 */
export function textoDoCsv(texto) {
  return /[;"\n]/.test(texto) ? `"${texto.replaceAll('"', '""')}"` : texto;
}

/**
 * PT: Monta o CSV a partir das colunas: o cabeçalho e uma linha por item.
 * EN: Builds the CSV from columns: header plus one line per item.
 *
 * @template T
 * @param {[string, (item: T) => string][]} colunas O título e o valor já escrito / title and written value
 * @param {T[]} itens
 * @returns {string}
 */
export function montarCsv(colunas, itens) {
  const cabecalho = colunas.map(([titulo]) => textoDoCsv(titulo)).join(";");
  const corpo = itens.map((item) => colunas.map(([, valor]) => valor(item)).join(";"));
  return `${[cabecalho, ...corpo].join("\r\n")}\r\n`;
}

/**
 * PT: Entrega o CSV ao navegador como arquivo para salvar.
 * EN: Hands the CSV to the browser as a file to save.
 *
 * @param {string} conteudo
 * @param {string} nome
 */
export function baixarCsv(conteudo, nome) {
  const arquivo = new Blob([`﻿${conteudo}`], { type: "text/csv;charset=utf-8" });
  const endereco = URL.createObjectURL(arquivo);
  const link = elemento("a", { atributos: { href: endereco, download: nome } });
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(endereco), 0);
}
