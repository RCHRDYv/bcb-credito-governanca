/**
 * PT: As classes de cor dos mapas e do cartograma.
 *
 *     Um mapa não pinta cada valor com uma cor própria: ele agrupa os
 *     valores em poucas classes, e cada classe recebe um degrau da paleta.
 *     Com poucas classes, a legenda é lida sem esforço e cada cor é
 *     distinguível das vizinhas. As classes são as mesmas no mapa e no
 *     cartograma, para os dois se lerem igual.
 *
 *     - **Sequencial,** para magnitude: cinco classes em quintis, cada uma
 *       com o mesmo número de UFs.
 *     - **Divergente,** para desvio contra uma referência: três classes de
 *       cada lado, com limites simétricos, e o meio neutro.
 *
 * EN: Color classes for maps and the tile cartogram. Sequential uses five
 *     quintile classes; diverging uses three symmetric classes per side plus
 *     a neutral middle. Map and cartogram share the same classes.
 */

import { DEGRAUS, paletas } from "./tema.js";

/** @typedef {import("../tokens.js").Tema} Tema */

/**
 * @typedef {object} Classe
 * @property {number} [gt] Maior que / greater than
 * @property {number} [gte] Maior ou igual / greater or equal
 * @property {number} [lt] Menor que / less than
 * @property {number} [lte] Menor ou igual / less or equal
 * @property {string} label Rótulo na legenda / legend label
 * @property {string} color A cor no tema pedido / color in the given theme
 * @property {string} variavel A variável CSS do token, que segue o tema sozinha / CSS variable
 */

/** @typedef {(tema: Tema) => Classe[]} Classes */

/**
 * PT: Os limites de quintis de uma lista de valores.
 * EN: Quintile limits of a list of values.
 *
 * @param {number[]} valores
 * @param {number} [classes]
 * @returns {number[]} Os limites internos, em ordem / inner limits
 */
export function quantis(valores, classes = DEGRAUS.sequencial) {
  const ordenados = valores.filter(Number.isFinite).sort((a, b) => a - b);
  return Array.from({ length: classes - 1 }, (_, i) => {
    const posicao = ((i + 1) / classes) * (ordenados.length - 1);
    return ordenados[Math.round(posicao)];
  });
}

/**
 * PT: Classes sequenciais em quintis, da mais alta para a mais baixa, que é
 *     a ordem em que a legenda é lida.
 * EN: Quintile sequential classes, highest first, as the legend reads.
 *
 * @param {number[]} valores
 * @param {(v: number) => string} formatar
 * @returns {Classes}
 */
export function classesSequenciais(valores, formatar) {
  const limites = quantis(valores);
  return (tema) => {
    const cores = paletas(tema).sequencial;
    return cores
      .map((color, i) => {
        const de = limites[i - 1];
        const ate = limites[i];
        const variavel = `--color-chart-sequential-${i + 1}`;
        if (i === 0) return { lte: ate, label: `até ${formatar(ate)}`, color, variavel };
        if (i === cores.length - 1) {
          return { gt: de, label: `acima de ${formatar(de)}`, color, variavel };
        }
        return { gt: de, lte: ate, label: `${formatar(de)} a ${formatar(ate)}`, color, variavel };
      })
      .reverse();
  };
}

/**
 * @typedef {object} RotulosDivergentes
 * @property {string} acima Como se diz "acima da referência" / "above"
 * @property {string} abaixo Como se diz "abaixo da referência" / "below"
 * @property {string} igual Rótulo do meio / middle label
 */

/**
 * PT: Classes divergentes com limites simétricos em torno de zero. Com os
 *     limites 0,1, 0,5 e 1, por exemplo, o meio vai de −0,1 a 0,1.
 * EN: Diverging classes with symmetric limits around zero.
 *
 * @param {[number, number, number]} limites Do meio para a ponta, positivos / positive, outwards
 * @param {(v: number) => string} formatar
 * @param {RotulosDivergentes} rotulos
 * @returns {Classes}
 */
export function classesDivergentes(limites, formatar, rotulos) {
  const [a, b, c] = limites;
  return (tema) => {
    const { negativo, neutro, positivo } = paletas(tema).divergente;
    return [
      {
        gt: c,
        label: `${rotulos.acima}, mais de ${formatar(c)}`,
        color: positivo[2],
        variavel: "--color-chart-diverging-positive-3",
      },
      {
        gt: b,
        lte: c,
        label: `${rotulos.acima}, de ${formatar(b)} a ${formatar(c)}`,
        color: positivo[1],
        variavel: "--color-chart-diverging-positive-2",
      },
      {
        gt: a,
        lte: b,
        label: `${rotulos.acima}, de ${formatar(a)} a ${formatar(b)}`,
        color: positivo[0],
        variavel: "--color-chart-diverging-positive-1",
      },
      {
        gte: -a,
        lte: a,
        label: `${rotulos.igual}, até ${formatar(a)}`,
        color: neutro,
        variavel: "--color-chart-diverging-neutral",
      },
      {
        gte: -b,
        lt: -a,
        label: `${rotulos.abaixo}, de ${formatar(a)} a ${formatar(b)}`,
        color: negativo[0],
        variavel: "--color-chart-diverging-negative-1",
      },
      {
        gte: -c,
        lt: -b,
        label: `${rotulos.abaixo}, de ${formatar(b)} a ${formatar(c)}`,
        color: negativo[1],
        variavel: "--color-chart-diverging-negative-2",
      },
      {
        lt: -c,
        label: `${rotulos.abaixo}, mais de ${formatar(c)}`,
        color: negativo[2],
        variavel: "--color-chart-diverging-negative-3",
      },
    ];
  };
}

/**
 * PT: A classe em que um valor cai, ou nenhuma.
 * EN: The class a value falls into, if any.
 *
 * @param {Classe[]} classes
 * @param {number} valor
 * @returns {Classe | undefined}
 */
export function classeDoValor(classes, valor) {
  return classes.find(
    (classe) =>
      (classe.gt === undefined || valor > classe.gt) &&
      (classe.gte === undefined || valor >= classe.gte) &&
      (classe.lt === undefined || valor < classe.lt) &&
      (classe.lte === undefined || valor <= classe.lte),
  );
}
