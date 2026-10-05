/**
 * PT: As classes de cor dos mapas e do cartograma.
 *
 *     Um mapa não pinta cada valor com uma cor própria: ele agrupa os
 *     valores em poucas classes, e cada classe recebe um degrau da paleta.
 *     Com poucas classes, a legenda é lida sem esforço e cada cor é
 *     distinguível das vizinhas. As classes são as mesmas no mapa e no
 *     cartograma, para os dois se lerem igual.
 *
 *     Toda intensidade usa a rampa roxa, a única do design system desde a
 *     revisão da Tela 1, em 2026-10-05 (ADR 0021). Duas formas de cortar:
 *
 *     - **Em quintis,** para magnitude: cinco classes, cada uma com o mesmo
 *       número de UFs.
 *     - **Em faixas em torno de uma referência,** como a mediana: o meio e
 *       duas faixas de cada lado, com limites simétricos. O lado que quer
 *       dizer mais fica no roxo mais forte, e a legenda diz o que cada faixa
 *       significa.
 *
 * EN: Color classes for maps and the tile cartogram, all on the purple
 *     ramp: quintiles for magnitude, or five symmetric bands around a
 *     reference, with the side that means more in the strongest purple.
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
  // PT: sem nenhum valor, não há classe: tudo fica na cor neutra, como numa
  //     modalidade em que nenhuma UF passa do corte de materialidade (#69)
  // EN: no values, no classes: everything stays neutral
  if (!valores.some(Number.isFinite)) return () => [];
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
 * @typedef {object} RotulosEmCinco
 * @property {string} forteAbaixo Mais longe abaixo da referência / furthest below
 * @property {string} abaixo
 * @property {string} meio Perto da referência / near the reference
 * @property {string} acima
 * @property {string} forteAcima Mais longe acima da referência / furthest above
 */

/**
 * PT: Classes em cinco faixas em torno de uma referência, na rampa roxa: o
 *     meio, de −a a a, e duas faixas de cada lado, com o corte em b. Servem
 *     a quem tem pouco tempo, como o executivo da Tela 1, que lê cinco cores
 *     sem esforço (revisão da #69, em 2026-10-01).
 *
 *     A intensidade cresce para o lado que quer dizer mais. Por padrão é o
 *     de cima; com `maisForteAbaixo`, o de baixo, como na Tela 1, em que
 *     abaixo da mediana quer dizer mais espaço (revisão de 2026-10-05). Os
 *     rótulos vêm prontos de quem chama, porque são eles que dizem o que
 *     cada faixa significa. A ordem é a da leitura da legenda, da faixa mais
 *     forte para a mais fraca.
 * EN: Five symmetric bands around a reference on the purple ramp, the
 *     strongest purple on the side that means more (above by default, below
 *     with `maisForteAbaixo`). Labels come from the caller. Ordered from the
 *     strongest band to the weakest, as the legend reads.
 *
 * @param {[number, number]} limites Do meio para a ponta, positivos / positive, outwards
 * @param {RotulosEmCinco} rotulos
 * @param {{ maisForteAbaixo?: boolean }} [opcoes]
 * @returns {Classes}
 */
export function classesEmCincoFaixas([a, b], rotulos, { maisForteAbaixo = false } = {}) {
  return (tema) => {
    const cores = paletas(tema).sequencial;
    /** @param {number} i Do degrau mais fraco, 0, ao mais forte, 4 / weakest to strongest */
    const degrau = (i) => {
      const n = maisForteAbaixo ? cores.length - 1 - i : i;
      return { color: cores[n], variavel: `--color-chart-sequential-${n + 1}` };
    };
    const faixas = [
      { lt: -b, label: rotulos.forteAbaixo, ...degrau(0) },
      { gte: -b, lt: -a, label: rotulos.abaixo, ...degrau(1) },
      { gte: -a, lte: a, label: rotulos.meio, ...degrau(2) },
      { gt: a, lte: b, label: rotulos.acima, ...degrau(3) },
      { gt: b, label: rotulos.forteAcima, ...degrau(4) },
    ];
    return maisForteAbaixo ? faixas : faixas.reverse();
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
