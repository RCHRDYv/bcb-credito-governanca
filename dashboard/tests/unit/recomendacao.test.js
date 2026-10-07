/**
 * PT: Testes da Tela 4 (#71) contra o `decisao.json` de verdade. Os números
 *     conferidos aqui são os do resumo de `docs/recomendacao.md`, que sai do
 *     mesmo mart: o site só agrupa e soma.
 * EN: Screen 4 tests against the real decision file; numbers are the
 *     report's summary.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  celulasAvaliadas,
  celulasDoQuadrante,
  custoDeErrar,
  foraDaMatriz,
  maiorErroDaReconstrucao,
  resumoPorQuadrante,
} from "../../src/visoes/recomendacao/dados.js";

const PASTA = join(dirname(fileURLToPath(import.meta.url)), "../../public/data/");
const decisao = JSON.parse(readFileSync(`${PASTA}decisao.json`, "utf8"));
const celulas = celulasAvaliadas(decisao);
const bi = (/** @type {number} */ v) => Math.round(v / 1e8) / 10;

describe("o resumo da recomendação / recommendation summary", () => {
  const resumo = Object.fromEntries(resumoPorQuadrante(celulas).map((r) => [r.quadrante, r]));

  it("bate com docs/recomendacao.md / matches the report", () => {
    expect(resumo.entrar).toMatchObject({ celulas: 35, alertas: 10 });
    expect(bi(resumo.entrar.carteira)).toBe(485.5);
    expect(bi(resumo.entrar.custoDeNaoEntrar)).toBe(141.1);
    expect(bi(resumo.entrar.custoDoRisco)).toBe(0.8);
    expect(resumo.observar).toMatchObject({ celulas: 35, alertas: 14 });
    expect(bi(resumo.observar.carteira)).toBe(369.2);
    expect(bi(resumo.observar.custoDeNaoEntrar)).toBe(106.3);
    expect(bi(resumo.observar.custoDoRisco)).toBe(2.3);
    expect(resumo["nao-entrar"]).toMatchObject({ celulas: 30, alertas: 10 });
    expect(bi(resumo["nao-entrar"].carteira)).toBe(574.9);
    expect(bi(resumo["nao-entrar"].custoDoRisco)).toBe(4.9);
    expect(resumo.manter).toMatchObject({ celulas: 47, alertas: 10 });
    expect(bi(resumo.manter.carteira)).toBe(1436.2);
    expect(bi(resumo.manter.custoDoRisco)).toBe(3.5);
  });

  it("as fora da matriz são 162 e somam R$ 44,2 bi / left-out cells", () => {
    const fora = foraDaMatriz(decisao);
    expect(fora.reduce((s, f) => s + f.celulas, 0)).toBe(162);
    expect(bi(fora.reduce((s, f) => s + f.carteira, 0))).toBe(44.2);
    expect(fora[0]).toMatchObject({
      motivo: "carteira abaixo do corte de materialidade",
      celulas: 161,
    });
    expect(fora[1]).toMatchObject({
      motivo: "modalidade com poucas UFs acima do corte",
      celulas: 1,
    });
    expect(bi(fora[1].carteira)).toBeCloseTo(1.6, 1);
  });

  it("todas as 309 células estão numa das duas partes / every cell is counted once", () => {
    const fora = foraDaMatriz(decisao).reduce((s, f) => s + f.celulas, 0);
    expect(celulas.length + fora).toBe(decisao.colunas.uf.length);
  });
});

describe("a ordem das células / cell order", () => {
  it("onde entrar começa por SP em Financiamentos, como no relatório / report's first row", () => {
    const [primeira] = celulasDoQuadrante(celulas, "entrar");
    expect(primeira).toMatchObject({ uf: "SP", modalidade: "Financiamentos" });
    expect(bi(/** @type {number} */ (primeira.custoDeNaoEntrar))).toBe(34.1);
  });

  it("o desvio do risco é a variação da UF menos a do país / risk deviation", () => {
    for (const c of celulas) expect(c.desvioDoRisco).toBeCloseTo(c.variacao - c.variacaoPais, 12);
  });
});

describe("o custo de errar e a fronteira / cost of being wrong and data limits", () => {
  it("soma as duas direções do ADR 0014 / both directions", () => {
    const custo = custoDeErrar(resumoPorQuadrante(celulas));
    expect(bi(custo.naoEntrar)).toBe(141.1);
    expect(bi(custo.risco)).toBe(7.2);
  });

  it("o maior erro da reconstrução é o de docs/recomendacao.md / reconstruction error", () => {
    const erro = JSON.parse(readFileSync(`${PASTA}erro_da_reconstrucao.json`, "utf8"));
    expect(maiorErroDaReconstrucao(erro) * 100).toBeCloseTo(2.3, 2);
  });
});
