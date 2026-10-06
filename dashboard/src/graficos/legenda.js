/**
 * PT: A legenda das classes de cor de um mapa ou cartograma, em HTML.
 *
 *     A legenda fica fora do SVG do ECharts por três motivos: quebra linha
 *     sozinha em tela estreita, é lida como texto por leitor de tela, e pinta
 *     cada amostra pela variável CSS do token, que já segue o tema do lugar
 *     onde a legenda está, sem precisar redesenhar nada.
 *
 * EN: HTML legend for a map's color classes: wraps on narrow screens, reads
 *     as text, and paints swatches with the token CSS variable.
 */

import { elemento } from "../dom.js";

/** @typedef {import("./escalas.js").Classe} Classe */

/**
 * PT: Monta a legenda, da classe mais alta para a mais baixa. Com
 *     `rotuloSemValor`, a legenda ganha no fim o item de quem fica sem cor de
 *     classe, com a mesma textura listrada do gráfico.
 * EN: Builds the legend, highest class first; with `rotuloSemValor`, a last
 *     item for value-less states, with the chart's striped texture.
 *
 * @param {Classe[]} classes
 * @param {string} [rotuloSemValor]
 * @returns {HTMLUListElement}
 */
export function legendaDeClasses(classes, rotuloSemValor) {
  const itens = classes.map((classe) => {
    const amostra = elemento("span", {
      classe: "legenda__cor",
      atributos: { "aria-hidden": "true" },
    });
    amostra.style.setProperty("background-color", `var(${classe.variavel})`);
    return elemento("li", { classe: "legenda__item" }, [amostra, classe.label]);
  });
  if (rotuloSemValor) {
    itens.push(
      elemento("li", { classe: "legenda__item" }, [
        elemento("span", {
          classe: "legenda__cor legenda__cor--sem-valor",
          atributos: { "aria-hidden": "true" },
        }),
        rotuloSemValor,
      ]),
    );
  }
  return elemento("ul", { classe: "legenda" }, itens);
}

/**
 * @typedef {(classes: Classe[], rotuloSemValor?: string) => HTMLElement} FazerLegenda
 */

/**
 * @typedef {object} OpcoesDaEscala
 * @property {Classe[]} classes Na ordem da barra, da esquerda para a direita / left to right
 * @property {string[]} marcas As divisas entre as classes, uma a menos que elas / boundaries
 * @property {[string, string]} extremos O que cada ponta quer dizer / what each end means
 * @property {string} titulo O que a escala mede / what the scale measures
 * @property {string} [rotuloSemValor] Item de quem fica sem cor de classe / value-less item
 * @property {string} [rotuloDaMarca] Item do marcador de alerta antecipado, quando o desenho o usa (#70) / early-warning marker item
 */

/**
 * PT: A legenda em escala: uma barra em degradê contínuo, do roxo mais forte
 *     ao mais fraco, com as divisas das classes marcadas embaixo e o sentido
 *     de cada ponta. Serve para faixas em torno de uma referência, como a
 *     distância até a mediana na Tela 1 (revisão de 2026-10-05).
 *
 *     O mapa pinta por classe, e o degradê passa pela cor de cada classe
 *     exatamente no meio da faixa dela; as marcas mostram onde uma classe
 *     termina e a outra começa. Para leitor de tela, cada classe vem por
 *     extenso numa lista escondida, e a barra e as marcas ficam fora da
 *     leitura.
 * EN: Scale legend: a continuous gradient bar through each class color at
 *     the centre of its band, boundaries marked below and each end's
 *     meaning, with the full class labels in a hidden list for screen readers.
 *
 * @param {OpcoesDaEscala} opcoes
 * @returns {HTMLElement}
 */
export function legendaEmEscala({
  classes,
  marcas,
  extremos,
  titulo,
  rotuloSemValor,
  rotuloDaMarca,
}) {
  const paradas = classes.map(
    (classe, i) => `var(${classe.variavel}) ${((i + 0.5) / classes.length) * 100}%`,
  );
  const barra = elemento("div", { classe: "escala__barra", atributos: { "aria-hidden": "true" } });
  barra.style.setProperty("background-image", `linear-gradient(to right, ${paradas.join(", ")})`);
  const divisas = marcas.map((marca, i) => {
    const el = elemento("span", { classe: "escala__marca", texto: marca });
    el.style.setProperty("--posicao", `${((i + 1) / classes.length) * 100}%`);
    return el;
  });
  const oculto = { "aria-hidden": "true" };
  return elemento("div", { classe: "escala" }, [
    elemento("p", { classe: "escala__titulo", texto: titulo }),
    barra,
    elemento("div", { classe: "escala__marcas", atributos: oculto }, divisas),
    elemento("div", { classe: "escala__extremos", atributos: oculto }, [
      elemento("span", { texto: extremos[0] }),
      elemento("span", { texto: extremos[1] }),
    ]),
    elemento(
      "ul",
      { classe: "visualmente-oculto" },
      classes.map((classe) => elemento("li", { texto: classe.label })),
    ),
    ...(rotuloSemValor
      ? [
          elemento("p", { classe: "escala__sem-valor" }, [
            elemento("span", {
              classe: "legenda__cor legenda__cor--sem-valor",
              atributos: oculto,
            }),
            rotuloSemValor,
          ]),
        ]
      : []),
    ...(rotuloDaMarca
      ? [
          elemento("p", { classe: "escala__marca-de-alerta" }, [
            elemento("span", { classe: "marcador-de-alerta", atributos: oculto }),
            rotuloDaMarca,
          ]),
        ]
      : []),
  ]);
}
