/**
 * PT: Ponto de entrada do site.
 *
 *     Por enquanto monta só a página inicial vazia do esqueleto (#65): um
 *     cabeçalho com o nome do produto e a área principal com o título. As
 *     visões entram como módulos próprios, cada um com `render(el, dados)`
 *     (ADR 0017, decisão 1).
 *
 *     O HTML é montado com `createElement` e `textContent`, nunca com
 *     `innerHTML`. Texto não vira HTML sem passar por sanitização, e aqui
 *     nenhum texto precisa virar HTML.
 *
 * EN: Site entry point. For now it only builds the skeleton's empty home page.
 *     Views will be their own modules with `render(el, data)`. DOM is built
 *     with `createElement` and `textContent`, never `innerHTML`.
 */

import { t } from "./textos/index.js";

/**
 * PT: Cria um elemento com um texto dentro.
 * EN: Creates an element holding a text.
 *
 * @template {keyof HTMLElementTagNameMap} Tag
 * @param {Tag} tag
 * @param {string} texto
 * @returns {HTMLElementTagNameMap[Tag]}
 */
function elementoComTexto(tag, texto) {
  const elemento = document.createElement(tag);
  elemento.textContent = texto;
  return elemento;
}

/**
 * PT: Monta a página inicial dentro da raiz: o link para pular ao conteúdo,
 *     o cabeçalho com o nome do produto e a área principal.
 * EN: Builds the home page inside the root: skip link, header and main area.
 *
 * @param {HTMLElement} raiz
 * @returns {void}
 */
export function montarPaginaInicial(raiz) {
  const pular = elementoComTexto("a", t("pagina.pular-para-o-conteudo"));
  pular.href = "#conteudo";
  pular.className = "pular-para-o-conteudo";

  const cabecalho = document.createElement("header");
  cabecalho.append(elementoComTexto("p", t("produto.nome")));

  const principal = document.createElement("main");
  principal.id = "conteudo";
  principal.tabIndex = -1;
  principal.append(
    elementoComTexto("h1", t("inicio.titulo")),
    elementoComTexto("p", t("inicio.em-construcao")),
  );

  raiz.replaceChildren(pular, cabecalho, principal);
}

document.title = t("pagina.titulo");

const raiz = document.getElementById("app");
if (raiz) {
  montarPaginaInicial(raiz);
}
