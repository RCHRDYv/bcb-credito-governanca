/**
 * PT: Testes da Tela 3 (#72) contra os arquivos de verdade, os de
 *     `public/data/`. Os números do Brasil conferidos aqui são os de
 *     `docs/previsao.md`: o site não projeta, só separa, recorta e tira
 *     médias do que o script da previsão gravou.
 * EN: Screen 3 tests against the real exported files; Brazil's numbers are
 *     the ones in `docs/previsao.md`.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  erroRecente,
  FORA_DA_ESCOLHA,
  janelaDosTestes,
  recortar,
  SERIE_INICIAL,
  serieDaProjecao,
  seriesDisponiveis,
  testesDaSerie,
} from "../../src/visoes/projecao/dados.js";
import { sobreOModelo } from "../../src/visoes/projecao/modelos.js";
import { csv, faixaCurta, reaisCurtos } from "../../src/visoes/projecao/tabela.js";

const PASTA = join(dirname(fileURLToPath(import.meta.url)), "../../public/data/");
const ler = (/** @type {string} */ nome) => JSON.parse(readFileSync(`${PASTA}${nome}`, "utf8"));
const projecao = ler("projecao_da_carteira.json");
const backtest = ler("backtest_da_projecao.json");
const testes = ler("testes_da_projecao.json");

describe("as séries da Tela 3 / screen series", () => {
  const series = seriesDisponiveis(projecao, (tipo, recorte) => `${tipo} ${recorte}`);

  it("tem o país, as modalidades e as 27 UFs, sem as de fora / has the choosable series", () => {
    expect(series).toHaveLength(41 - FORA_DA_ESCOLHA.size);
    expect(series[0].chave).toBe(SERIE_INICIAL);
    expect(series.filter((s) => s.tipo === "modalidade")).toHaveLength(13 - FORA_DA_ESCOLHA.size);
    expect(series.filter((s) => s.tipo === "uf")).toHaveLength(27);
  });

  it("a série fora da escolha é a que tem valor negativo / left-out series is the negative one (#101)", () => {
    const colunas = projecao.colunas;
    const negativas = new Set(
      colunas.limite_inferior.flatMap((/** @type {number | null} */ v, /** @type {number} */ i) =>
        v !== null && v < 0 ? [`${colunas.tipo_de_recorte[i]}:${colunas.recorte[i]}`] : [],
      ),
    );
    expect(negativas).toEqual(new Set(FORA_DA_ESCOLHA));
    for (const s of series) expect(FORA_DA_ESCOLHA.has(s.chave)).toBe(false);
  });

  it("põe o país, depois as modalidades, depois as UFs / orders by type", () => {
    const tipos = series.map((s) => s.tipo);
    expect(tipos.indexOf("uf")).toBeGreaterThan(tipos.lastIndexOf("modalidade"));
  });
});

describe("a projeção do Brasil / Brazil's forecast", () => {
  const serie = serieDaProjecao(projecao, SERIE_INICIAL);

  it("tem 31 meses realizados e 3 projetados / 31 actual and 3 projected months", () => {
    expect(serie.meses).toHaveLength(31);
    expect(serie.meses[0]).toBe("2024-01-31");
    expect(serie.meses.at(-1)).toBe("2026-07-31");
    expect(serie.projetados.map((p) => p.mes)).toEqual(["2026-08-31", "2026-09-30", "2026-10-31"]);
  });

  it("bate com docs/previsao.md / matches the report", () => {
    expect(serie.modelo).toBe("deriva");
    const [ago, set, out] = serie.projetados;
    expect(ago.valor / 1e12).toBeCloseTo(2.926, 3);
    expect(ago.inferior / 1e12).toBeCloseTo(2.878, 3);
    expect(ago.superior / 1e12).toBeCloseTo(2.973, 3);
    expect(set.valor / 1e12).toBeCloseTo(2.941, 3);
    expect(out.valor / 1e12).toBeCloseTo(2.957, 3);
    expect(out.inferior / 1e12).toBeCloseTo(2.872, 3);
    expect(out.superior / 1e12).toBeCloseTo(3.042, 3);
  });

  it("recorta o período sem mexer na projeção / cuts the period", () => {
    const curto = recortar(serie, "12-meses");
    expect(curto.meses).toHaveLength(12);
    expect(curto.meses[0]).toBe("2025-08-31");
    expect(curto.projetados).toEqual(serie.projetados);
    expect(recortar(serie, "desde-2024").meses).toHaveLength(31);
  });
});

describe("os testes recentes / recent tests", () => {
  const serie = serieDaProjecao(projecao, SERIE_INICIAL);
  const recentes = testesDaSerie(testes, SERIE_INICIAL);

  it("são 4, com três meses cada / four tests of three months", () => {
    expect(recentes.map((t) => t.data)).toEqual([
      "2026-01-31",
      "2026-02-28",
      "2026-03-31",
      "2026-04-30",
    ]);
    for (const teste of recentes) expect(teste.projetados).toHaveLength(3);
  });

  it("o realizado do teste é o da série / test actuals match the series", () => {
    for (const teste of recentes) {
      teste.projetados.forEach((p, h) => {
        expect(teste.realizados[h]).toBe(serie.valores[serie.meses.indexOf(p.mes)]);
      });
    }
  });

  it("o erro do Brasil bate com docs/previsao.md / Brazil's error matches", () => {
    const erro = erroRecente(backtest, recentes, SERIE_INICIAL);
    expect(erro.modelo).toBe("deriva");
    expect(erro.erro * 100).toBeCloseTo(0.65, 2);
    expect(erro.erroDeRepetir * 100).toBeCloseTo(1.03, 2);
    expect(erro).toMatchObject({ acertos: 12, casos: 12 });
  });

  it("o erro do backtest é o dos testes recentes / backtest error is the recent tests'", () => {
    for (const { chave } of seriesDisponiveis(projecao, () => "")) {
      const recentesDaSerie = testesDaSerie(testes, chave);
      const casos = recentesDaSerie.flatMap((t) =>
        t.projetados.map((p, h) => Math.abs(p.valor - t.realizados[h]) / t.realizados[h]),
      );
      const media = casos.reduce((s, v) => s + v, 0) / casos.length;
      expect(erroRecente(backtest, recentesDaSerie, chave).erro, chave).toBeCloseTo(media, 6);
    }
  });

  it("a janela do gráfico começa dois meses antes do primeiro teste / chart window", () => {
    const janela = janelaDosTestes(serie, recentes);
    expect(janela.meses[0]).toBe("2025-11-30");
    expect(janela.meses.at(-1)).toBe("2026-07-31");
  });
});

describe("os textos da tela / screen texts", () => {
  it("todo modelo do backtest tem nome comum e frase / every model has plain texts", () => {
    for (const modelo of new Set(backtest.colunas.modelo)) {
      const texto = sobreOModelo(String(modelo));
      expect(texto.nome, String(modelo)).not.toBe("");
      expect(texto.como, String(modelo)).not.toBe("");
    }
  });

  it("a faixa curta escreve a unidade uma vez / short band writes the unit once", () => {
    const [ago] = serieDaProjecao(projecao, SERIE_INICIAL).projetados;
    expect(faixaCurta(ago)).toBe("2,88 a 2,97 tri");
    expect(faixaCurta({ mes: "", valor: 0, inferior: 183.8e9, superior: 187.43e9 })).toBe(
      "183,8 a 187,4 bi",
    );
    expect(reaisCurtos(184.8e9)).toBe("R$ 184,8 bi");
    expect(reaisCurtos(2.91e12)).toBe("R$ 2,91 tri");
  });

  it("o CSV tem uma linha por mês, com a projeção no fim / CSV rows", () => {
    const linhas = csv(serieDaProjecao(projecao, SERIE_INICIAL)).trim().split(/\r?\n/);
    expect(linhas).toHaveLength(1 + 31 + 3);
    expect(linhas.at(-1)).toMatch(/^2026-10-31/);
  });
});
