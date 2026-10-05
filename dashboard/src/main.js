/**
 * PT: Ponto de entrada do site.
 *
 *     Monta a página: o link para pular ao conteúdo, a barra de topo com a
 *     navegação entre as visões e a área principal, onde a navegação monta a
 *     visão do endereço. Cada visão é um módulo com `render(el, dados)` (ADR
 *     0017, decisão 1). O endereço do site abre direto na primeira visão, a
 *     Tela 1 (decidido em 2026-10-01).
 *
 * EN: Site entry point: skip link, top bar with view navigation, and the
 *     main area where navigation mounts the address's view. The site's
 *     address opens straight on the first view.
 */

import "./estilos/index.css";
import { topo } from "./componentes/topo.js";
import { elemento } from "./dom.js";
import { iniciarNavegacao, navegacao } from "./navegacao.js";
import { t } from "./textos/index.js";

/**
 * PT: Monta a página dentro da raiz e começa a navegação.
 * EN: Builds the page inside the root and starts navigation.
 *
 * @param {HTMLElement} raiz
 * @returns {void}
 */
export function montarPagina(raiz) {
  const pular = elemento("a", {
    classe: "pular-para-o-conteudo",
    texto: t("pagina.pular-para-o-conteudo"),
    atributos: { href: "#conteudo" },
  });
  const nav = navegacao();
  const principal = elemento("main", {
    classe: "principal",
    atributos: { id: "conteudo", tabindex: "-1" },
  });
  // PT: a classe liga a tela única do ADR 0022, só no site, e não no catálogo
  // EN: the class turns on ADR 0022's single screen, on the site only
  raiz.classList.add("pagina");
  raiz.replaceChildren(pular, topo({ navegacao: nav }), principal);
  iniciarNavegacao({ principal, nav });
}

document.title = t("pagina.titulo");

const raiz = document.getElementById("app");
if (raiz) {
  montarPagina(raiz);
}
