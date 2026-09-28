/**
 * PT: Os ícones da interface, do Tabler Icons.
 *
 *     São os mesmos ícones do protótipo aprovado (ADR 0020), do pacote
 *     `@tabler/icons` 3.48.0, com licença MIT. Cada ícone é citado pelo nome
 *     e vem do arquivo SVG oficial do pacote: nenhum traço é desenhado aqui.
 *     O build junta só os ícones listados abaixo, e nenhum é buscado fora do
 *     site, como pede a política de segurança (#68). Os traços usam
 *     `currentColor`, então o ícone herda a cor do texto ao lado.
 *
 * EN: Interface icons from Tabler Icons (MIT), cited by name and taken from
 *     the package's official SVG files. Only the icons listed here are
 *     bundled, and nothing is fetched from outside the site.
 *
 *     Licença / license: https://github.com/tabler/tabler-icons/blob/main/LICENSE
 */

import alertCircle from "@tabler/icons/outline/alert-circle.svg?raw";
import alertTriangle from "@tabler/icons/outline/alert-triangle.svg?raw";
import arrowRight from "@tabler/icons/outline/arrow-right.svg?raw";
import arrowUp from "@tabler/icons/outline/arrow-up.svg?raw";
import arrowUpRight from "@tabler/icons/outline/arrow-up-right.svg?raw";
import ban from "@tabler/icons/outline/ban.svg?raw";
import bellRinging from "@tabler/icons/outline/bell-ringing.svg?raw";
import check from "@tabler/icons/outline/check.svg?raw";
import chevronRight from "@tabler/icons/outline/chevron-right.svg?raw";
import circleX from "@tabler/icons/outline/circle-x.svg?raw";
import download from "@tabler/icons/outline/download.svg?raw";
import equal from "@tabler/icons/outline/equal.svg?raw";
import eye from "@tabler/icons/outline/eye.svg?raw";
import infoCircle from "@tabler/icons/outline/info-circle.svg?raw";
import refresh from "@tabler/icons/outline/refresh.svg?raw";

/**
 * PT: Os ícones disponíveis, pelo nome do Tabler.
 * EN: Available icons, by Tabler name.
 */
const SVGS = Object.freeze({
  "alert-circle": alertCircle,
  "alert-triangle": alertTriangle,
  "arrow-right": arrowRight,
  "arrow-up": arrowUp,
  "arrow-up-right": arrowUpRight,
  ban,
  "bell-ringing": bellRinging,
  check,
  "chevron-right": chevronRight,
  "circle-x": circleX,
  download,
  equal,
  eye,
  "info-circle": infoCircle,
  refresh,
});

/** @typedef {keyof typeof SVGS} NomeDoIcone */

/** @type {Map<NomeDoIcone, SVGSVGElement>} */
const modelos = new Map();

/**
 * PT: Lê o SVG do pacote uma vez só e guarda o elemento como modelo. O
 *     conteúdo vem do pacote instalado, e não do visitante, então pode ser
 *     interpretado como SVG sem risco de injeção.
 * EN: Parses the package SVG once and keeps it as a template.
 *
 * @param {NomeDoIcone} nome
 * @returns {SVGSVGElement}
 */
function modelo(nome) {
  const guardado = modelos.get(nome);
  if (guardado) return guardado;
  const documento = new DOMParser().parseFromString(SVGS[nome], "image/svg+xml");
  const svg = /** @type {SVGSVGElement} */ (/** @type {unknown} */ (documento.documentElement));
  // PT: o tamanho vem do CSS, pela classe `icone` / EN: size comes from CSS
  svg.removeAttribute("width");
  svg.removeAttribute("height");
  svg.removeAttribute("class");
  svg.setAttribute("class", "icone");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  // PT: o arquivo do pacote traz quebras de linha entre os traços; elas não
  //     aparecem, mas entrariam no texto do componente que usa o ícone
  // EN: drop the file's whitespace text nodes between strokes
  for (const no of [...svg.childNodes]) {
    if (no.nodeType === Node.TEXT_NODE && !no.textContent?.trim()) no.remove();
  }
  modelos.set(nome, svg);
  return svg;
}

/**
 * PT: Um ícone, decorativo: quem lê a tela lê o texto ao lado, e não o
 *     ícone. Falha se o nome não estiver na lista.
 * EN: A decorative icon; throws for an unknown name.
 *
 * @param {NomeDoIcone} nome
 * @returns {SVGSVGElement}
 */
export function icone(nome) {
  if (!Object.hasOwn(SVGS, nome)) {
    throw new Error(`Ícone fora da lista: ${nome}`);
  }
  return /** @type {SVGSVGElement} */ (document.importNode(modelo(nome), true));
}
