/**
 * PT: A navegação entre as visões (RF-G01) e os estados de carga de cada uma
 *     (RF-G11).
 *
 *     A barra de topo lista as visões que existem e marca a atual com
 *     `aria-current="page"`. Ao abrir uma visão, a área principal mostra o
 *     estado de carregando; se um arquivo não chega ou chega quebrado, mostra
 *     o estado de erro, que diz o problema e oferece tentar de novo. A visão
 *     anterior é desmontada antes, para os gráficos dela liberarem memória.
 *
 *     Um pedido de visão que chega atrasado, depois de a pessoa já ter ido
 *     para outra, é descartado.
 *
 * EN: Navigation between views and their load states. The top bar lists the
 *     views and marks the current one; the main area shows loading, then the
 *     view, or an error with retry. The previous view is torn down first, and
 *     late responses for an abandoned view are discarded.
 */

import { carregando, erro } from "./componentes/estados.js";
import { ErroDeCarga } from "./dados/carregar.js";
import { elemento } from "./dom.js";
import { t } from "./textos/index.js";
import { endereco, VISOES, visaoDoHash } from "./visoes/indice.js";

/**
 * PT: A lista de links da navegação, um por visão.
 * EN: The navigation links, one per view.
 *
 * @returns {HTMLElement}
 */
export function navegacao() {
  return elemento(
    "nav",
    { classe: "navegacao", atributos: { "aria-label": t("navegacao.rotulo") } },
    [
      elemento(
        "ul",
        { classe: "navegacao__lista" },
        VISOES.map((visao) =>
          elemento("li", {}, [
            elemento("a", {
              classe: "navegacao__link",
              texto: visao.nome,
              atributos: { href: endereco(visao), "data-visao": visao.id },
            }),
          ]),
        ),
      ),
    ],
  );
}

/**
 * PT: Marca a visão atual na navegação.
 * EN: Marks the current view in the navigation.
 *
 * @param {HTMLElement} nav
 * @param {string} id
 */
function marcar(nav, id) {
  for (const link of nav.querySelectorAll("[data-visao]")) {
    if (link.getAttribute("data-visao") === id) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
}

/**
 * PT: Começa a navegação: abre a visão do endereço e acompanha as trocas.
 * EN: Starts navigation: opens the address's view and follows changes.
 *
 * @param {object} lugares
 * @param {HTMLElement} lugares.principal Onde a visão é montada / where views mount
 * @param {HTMLElement} lugares.nav A navegação da barra de topo / the top bar navigation
 * @returns {void}
 */
export function iniciarNavegacao({ principal, nav }) {
  /** @type {(() => void) | null} */
  let desmontar = null;
  let pedido = 0;

  const abrir = async () => {
    pedido += 1;
    const meu = pedido;
    const visao = visaoDoHash(window.location.hash);
    marcar(nav, visao.id);
    document.title = `${visao.nome} · ${t("produto.nome")}`;
    desmontar?.();
    desmontar = null;
    principal.replaceChildren(carregando());
    try {
      const modulo = await visao.modulo();
      const dados = await modulo.carregarDados();
      if (meu !== pedido) return;
      desmontar = modulo.render(principal, dados);
    } catch (falha) {
      if (meu !== pedido) return;
      const motivo = falha instanceof ErroDeCarga ? falha.motivo : "rede";
      principal.replaceChildren(
        erro({
          titulo: t("navegacao.erro-titulo"),
          texto: t(motivo === "formato" ? "navegacao.erro-formato" : "navegacao.erro-rede"),
          aoTentarDeNovo: () => void abrir(),
        }),
      );
    }
  };

  // PT: só endereços de visão mudam a visão; `#conteudo`, do link de pular
  //     para o conteúdo, é âncora da própria página
  // EN: only view addresses switch views; `#conteudo` is an in-page anchor
  window.addEventListener("hashchange", () => {
    const { hash } = window.location;
    if (hash === "" || hash.startsWith("#/")) void abrir();
  });
  void abrir();
}
