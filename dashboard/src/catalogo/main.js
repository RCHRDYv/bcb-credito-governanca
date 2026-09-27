/**
 * PT: Ponto de entrada do catálogo do design system.
 *
 *     Monta a página a partir do `tokens.json` gerado: nada do que aparece
 *     aqui é digitado à mão. Se um token muda, o catálogo muda junto.
 *
 * EN: Design system catalog entry point. Built from the generated
 *     `tokens.json`, so nothing shown here is typed by hand.
 */

import "../estilos/index.css";
import "./catalogo.css";
import { elemento } from "../dom.js";
import { t } from "../textos/index.js";
import { secaoGraficos, secaoPaletasDeGrafico } from "./graficos.js";
import {
  secaoCores,
  secaoElevacao,
  secaoEspacamento,
  secaoMovimento,
  secaoPaleta,
  secaoRaios,
  secaoTipografia,
  secaoVidro,
} from "./secoes.js";

const ENDERECO_DO_GUIA =
  "https://github.com/RCHRDYv/bcb-credito-governanca/blob/main/docs/dashboard/design-system.md";

/**
 * PT: Monta o catálogo dentro da raiz.
 * EN: Builds the catalog inside the root.
 *
 * @param {HTMLElement} raiz
 * @returns {Promise<void>}
 */
export async function montarCatalogo(raiz) {
  const graficos = secaoGraficos();
  const pular = elemento("a", {
    classe: "pular-para-o-conteudo",
    texto: t("pagina.pular-para-o-conteudo"),
    atributos: { href: "#conteudo" },
  });

  const topo = elemento("header", { classe: "topo" }, [
    elemento("p", { classe: "topo__nome", texto: t("produto.nome") }),
  ]);

  const cabecalho = elemento("div", { classe: "catalogo__cabecalho" }, [
    elemento("h1", { texto: t("catalogo.titulo") }),
    elemento("p", { classe: "catalogo__introducao", texto: t("catalogo.introducao") }),
    elemento("a", { texto: t("catalogo.guia"), atributos: { href: ENDERECO_DO_GUIA } }),
  ]);

  const principal = elemento(
    "main",
    { classe: "catalogo", atributos: { id: "conteudo", tabindex: "-1" } },
    [
      cabecalho,
      secaoCores(),
      secaoPaleta(),
      secaoTipografia(),
      secaoEspacamento(),
      secaoRaios(),
      secaoElevacao(),
      secaoVidro(),
      secaoMovimento(),
      secaoPaletasDeGrafico(),
      graficos.elemento,
    ],
  );

  raiz.replaceChildren(pular, topo, principal);
  // PT: os gráficos só são desenhados com a seção já na página, porque o tema
  //     de cada um vem do painel onde ele está
  // EN: charts are drawn once on the page, since each takes its panel theme
  await graficos.desenhar();
}

document.title = t("catalogo.titulo-da-pagina");

const raiz = document.getElementById("app");
if (raiz) {
  montarCatalogo(raiz);
}
