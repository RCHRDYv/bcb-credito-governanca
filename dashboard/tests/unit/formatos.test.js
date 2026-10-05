/**
 * PT: Testes da formatação brasileira de números e datas, contra o quadro
 *     de conteúdo do guia do design system (RF-G10).
 * EN: Brazilian number and date formatting, against the guide's table.
 */

import { describe, expect, it } from "vitest";
import { dataBase, mesCurto, numero, pontos, reais, taxa, vezes } from "../../src/formatos.js";

describe("formatos do guia / the guide's formats", () => {
  it("reais em bi, mi e mil / reais", () => {
    expect(reais(2_910_100_000_000)).toBe("R$ 2,9 tri");
    expect(reais(485_503_196_800)).toBe("R$ 485,5 bi");
    expect(reais(12_340_000)).toBe("R$ 12,3 mi");
    expect(reais(61_600)).toBe("R$ 61,6 mil");
    expect(reais(950)).toBe("R$ 950");
  });

  it("taxa em porcentagem / rate", () => {
    expect(taxa(0.0093)).toBe("0,93%");
  });

  it("variação de taxa em pontos percentuais, com sinal / signed p.p.", () => {
    expect(pontos(0.0015)).toBe("+0,15 p.p.");
    expect(pontos(-0.0015)).toBe("−0,15 p.p.");
    expect(pontos(0)).toBe("0,00 p.p.");
  });

  it("data-base e mês curto / dates", () => {
    expect(dataBase("2026-07-31")).toBe("jul/2026");
    expect(mesCurto("2026-07-31")).toBe("jul/26");
  });

  it("número e vezes / number and times", () => {
    expect(numero(1234.5)).toBe("1.234,5");
    expect(vezes(0.82)).toBe("0,82×");
  });
});
