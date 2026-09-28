/**
 * PT: Ponto de entrada do site.
 *
 *     Por enquanto monta só a página inicial vazia do esqueleto (#65): um
 *     cabeçalho com o nome do produto e a área principal com o título. As
 *     visões entram como módulos próprios, cada um com `render(el, dados)`
 *     (ADR 0017, decisão 1). O visual vem dos tokens (#62).
 *
 * EN: Site entry point. For now it only builds the skeleton's empty home page.
 *     Views will be their own modules with `render(el, data)`. Styling comes
 *     from the tokens.
 */

import "./estilos/index.css";
import "./estilos/pagina-inicial.css";
import { topo } from "./componentes/topo.js";
import { elemento } from "./dom.js";
import { t } from "./textos/index.js";

/**
 * PT: Monta a página inicial dentro da raiz: o link para pular ao conteúdo,
 *     o cabeçalho com o nome do produto e a área principal.
 * EN: Builds the home page inside the root: skip link, header and main area.
 *
 * @param {HTMLElement} raiz
 * @returns {void}
 */
export function montarPaginaInicial(raiz) {
  const pular = elemento("a", {
    classe: "pular-para-o-conteudo",
    texto: t("pagina.pular-para-o-conteudo"),
    atributos: { href: "#conteudo" },
  });

  const cabecalho = topo();

  const principal = elemento(
    "main",
    { classe: "inicio", atributos: { id: "conteudo", tabindex: "-1" } },
    [
      elemento("h1", { texto: t("inicio.titulo") }),
      elemento("p", { classe: "inicio__aviso", texto: t("inicio.em-construcao") }),
    ],
  );

  raiz.replaceChildren(pular, cabecalho, principal);
}

document.title = t("pagina.titulo");

const raiz = document.getElementById("app");
if (raiz) {
  montarPaginaInicial(raiz);
}
