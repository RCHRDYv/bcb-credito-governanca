/**
 * PT: Testes da tabela das UFs, da grade do cartograma (#63, RF-103) e da
 *     malha versionada (#67).
 *
 *     A grade foi revisada em 2026-09-27, depois que a primeira versão pôs
 *     estados em posições erradas. A regra: todo par de UFs vizinhas na
 *     grade precisa apontar, de uma para a outra, a menos de 60 graus da
 *     direção real. A direção real sai dos centroides de cada UF, calculados
 *     da malha de qualidade mínima da API de malhas do IBGE, em graus de
 *     longitude e latitude, com duas casas. Com uma casa só, o par Amazonas e
 *     Rondônia, que fica em 59,5 graus, passaria do limite por arredondamento.
 *
 * EN: UF table and tile-grid tests. Every pair of grid neighbours must point
 *     within 60 degrees of the real direction between IBGE mesh centroids.
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { UFS, ufPelaSigla, ufPeloCodigo } from "../../src/graficos/ufs.js";

/**
 * PT: Centroides das UFs, [longitude, latitude], da malha do IBGE.
 * EN: State centroids from the IBGE mesh.
 *
 * @type {Record<string, [number, number]>}
 */
const CENTROIDES = {
  RO: [-62.84, -10.91],
  AC: [-70.47, -9.21],
  AM: [-64.65, -4.15],
  RR: [-61.39, 2.08],
  PA: [-53.07, -3.98],
  AP: [-51.96, 1.45],
  TO: [-48.33, -10.15],
  MA: [-45.29, -5.08],
  PI: [-42.97, -7.39],
  CE: [-39.61, -5.09],
  RN: [-36.67, -5.84],
  PB: [-36.83, -7.12],
  PE: [-38.01, -8.33],
  AL: [-36.62, -9.52],
  SE: [-37.44, -10.58],
  BA: [-41.72, -12.48],
  MG: [-44.67, -18.46],
  ES: [-40.67, -19.57],
  RJ: [-42.67, -22.2],
  SP: [-48.73, -22.27],
  PR: [-51.62, -24.64],
  SC: [-50.47, -27.25],
  RS: [-53.32, -29.71],
  MS: [-54.85, -20.33],
  MT: [-55.91, -12.95],
  GO: [-49.63, -16.04],
  DF: [-47.8, -15.78],
};

// PT: a longitude encolhe com o cosseno da latitude média do país, cerca de 15° sul
// EN: longitude shrinks with the cosine of the mean latitude, about 15° S
const ESCALA = Math.cos((15 * Math.PI) / 180);
const DESVIO_MAXIMO = 60;

describe("tabela das UFs", () => {
  it("tem as 27 UFs, com siglas e códigos únicos / 27 unique states", () => {
    expect(UFS).toHaveLength(27);
    expect(new Set(UFS.map((uf) => uf.sigla)).size).toBe(27);
    expect(new Set(UFS.map((uf) => uf.codigo)).size).toBe(27);
    expect(Object.keys(CENTROIDES).sort()).toEqual(UFS.map((uf) => uf.sigla).sort());
  });

  it("acha a UF pela sigla e pelo código / finds by abbreviation and code", () => {
    expect(ufPelaSigla("DF").nome).toBe("Distrito Federal");
    expect(ufPeloCodigo("35").sigla).toBe("SP");
    expect(() => ufPelaSigla("XX")).toThrow();
  });
});

describe("grade do cartograma", () => {
  it("põe cada UF numa célula própria / one cell per state", () => {
    const celulas = UFS.map((uf) => `${uf.linha},${uf.coluna}`);
    expect(new Set(celulas).size).toBe(27);
  });

  it(`mantém cada vizinho a menos de ${DESVIO_MAXIMO} graus da direção real`, () => {
    const desvios = [];
    for (const a of UFS) {
      for (const b of UFS) {
        const vizinhas =
          a.sigla < b.sigla &&
          Math.max(Math.abs(a.linha - b.linha), Math.abs(a.coluna - b.coluna)) === 1;
        if (!vizinhas) continue;
        const naGrade = [b.coluna - a.coluna, a.linha - b.linha];
        const [xa, ya] = CENTROIDES[a.sigla];
        const [xb, yb] = CENTROIDES[b.sigla];
        const noMapa = [(xb - xa) * ESCALA, yb - ya];
        const cosseno =
          (naGrade[0] * noMapa[0] + naGrade[1] * noMapa[1]) /
          (Math.hypot(...naGrade) * Math.hypot(...noMapa));
        const graus = (Math.acos(cosseno) * 180) / Math.PI;
        if (graus > DESVIO_MAXIMO) desvios.push(`${a.sigla}-${b.sigla}: ${graus.toFixed(0)}°`);
      }
    }
    expect(desvios).toEqual([]);
  });
});

/**
 * PT: A malha versionada pela #67 traz, por UF, o código do IBGE e a sigla,
 *     tirada de dim_uf na ontologia. O site usa a tabela de `ufs.js` para ir
 *     do código à sigla. Este teste cruza as duas fontes: se uma mudar sem a
 *     outra, o mapa pintaria a UF errada.
 * EN: The versioned mesh carries the IBGE code and the abbreviation from the
 *     ontology; the site maps code to abbreviation through `ufs.js`. This
 *     cross-checks both sources.
 */
describe("malha das UFs versionada (#67)", () => {
  const caminho = fileURLToPath(new URL("../../public/geo/ufs.json", import.meta.url));
  /** @type {{ features: { properties: { codarea: string, sigla: string } }[] }} */
  const malha = JSON.parse(readFileSync(caminho, "utf-8"));

  it("tem uma feição por UF da tabela / one feature per state", () => {
    const codigos = malha.features.map((f) => f.properties.codarea).sort();
    expect(codigos).toEqual(UFS.map((uf) => uf.codigo).sort());
  });

  it("dá a mesma sigla que a tabela para cada código / same abbreviation per code", () => {
    const divergentes = malha.features
      .filter((f) => ufPeloCodigo(f.properties.codarea).sigla !== f.properties.sigla)
      .map((f) => f.properties.codarea);
    expect(divergentes).toEqual([]);
  });
});
