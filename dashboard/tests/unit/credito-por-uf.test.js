/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes da Tela 1 (#69) contra os arquivos de dados de verdade, os de
 *     `public/data/`: as linhas de cada recorte, o resumo, o ranking, a
 *     matriz, a cor, a escala, o perfil da UF e o CSV. Os números conferidos
 *     aqui são os que o mart exportou (RF-101); o site só soma, conta e
 *     ordena (ADR 0007).
 * EN: Screen 1 tests against the real exported data files.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { Filtros } from "../../src/estado/filtros.js";
import { classeDoValor } from "../../src/graficos/escalas.js";
import {
  classesDeEspaco,
  distancia,
  legendaDeEspaco,
  marcasDaEscala,
  posicao,
} from "../../src/visoes/credito-por-uf/cor.js";
import {
  celulasDaMatriz,
  linhas,
  modalidades,
  oportunidade,
  posicaoDaUf,
  resumo,
  TODAS,
  ufsPorCarteira,
} from "../../src/visoes/credito-por-uf/dados.js";
import { perfilDaUf } from "../../src/visoes/credito-por-uf/perfil.js";
import { csv, tabelaDaTela } from "../../src/visoes/credito-por-uf/tabela.js";

const PASTA = join(dirname(fileURLToPath(import.meta.url)), "../../public/data/");
const ler = (/** @type {string} */ nome) => JSON.parse(readFileSync(`${PASTA}${nome}`, "utf8"));
const dados = { porUf: ler("carteira_por_uf.json"), decisao: ler("decisao.json") };
const colunas = dados.porUf.colunas;
const soma = (/** @type {(number | null)[]} */ valores) =>
  valores.reduce((total, v) => /** @type {number} */ (total) + (v ?? 0), 0);

describe("as linhas da Tela 1 / screen rows", () => {
  const todas = linhas(dados, TODAS);

  it("trazem as 27 UFs em todas as modalidades, com os números do mart / 27 states, mart numbers", () => {
    expect(todas).toHaveLength(27);
    const sp = todas.find((l) => l.uf === "SP");
    const i = colunas.uf.indexOf("SP");
    expect(sp?.carteira).toBe(colunas.carteira_pj[i]);
    expect(sp?.carteiraPorEmpresa).toBe(colunas.carteira_por_empresa[i]);
    expect(sp?.custo).toBe(colunas.custo_de_nao_entrar[i]);
  });

  it("dão a oportunidade somada igual à soma do mart / summed gap matches the mart", () => {
    const r = resumo(todas);
    expect(r.custo).toBe(soma(colunas.custo_de_nao_entrar));
    expect(r.carteira).toBe(soma(colunas.carteira_pj));
    expect(r.abaixo).toBe(
      colunas.custo_de_nao_entrar.filter((/** @type {number | null} */ v) => v !== null).length,
    );
    expect(r.comparadas).toBe(27);
  });

  it("põem no ranking só as UFs abaixo da mediana, pelo crédito que faltaria / ranking items", () => {
    const itens = oportunidade(todas);
    expect(itens).toHaveLength(resumo(todas).abaixo);
    expect(itens.every((item) => item.valor > 0)).toBe(true);
  });

  it("dão a posição 1 à UF de menor carteira por empresa / rank 1 is the lowest", () => {
    const menor = [...todas].sort(
      (a, b) =>
        /** @type {number} */ (a.carteiraPorEmpresa) - /** @type {number} */ (b.carteiraPorEmpresa),
    )[0];
    expect(posicaoDaUf(todas, menor.uf)).toEqual({ posicao: 1, de: 27 });
  });

  it("marcam quem fica fora da comparação numa modalidade pequena / out-of-comparison states", () => {
    const rurais = linhas(dados, "08");
    expect(rurais.some((l) => l.situacao !== "comparada")).toBe(true);
    for (const linha of rurais.filter((l) => l.situacao !== "comparada")) {
      expect(linha.indice).toBeNull();
      expect(linha.custo).toBeNull();
    }
  });

  it("ordenam as modalidades pela carteira e contam as comparadas / modality list", () => {
    const lista = modalidades(dados.decisao);
    expect(lista.length).toBeGreaterThan(0);
    for (let i = 1; i < lista.length; i += 1) {
      expect(lista[i - 1].carteira).toBeGreaterThanOrEqual(lista[i].carteira);
    }
  });

  it("ordenam as UFs da matriz pela carteira, com SP na frente / heatmap order", () => {
    const ordem = ufsPorCarteira(dados.porUf);
    expect(ordem).toHaveLength(27);
    expect(ordem[0]).toBe("SP");
    expect(celulasDaMatriz(dados.decisao).length).toBe(dados.decisao.colunas.uf.length);
  });
});

describe("a cor da Tela 1 / screen colors", () => {
  const classes = classesDeEspaco()("claro");

  it("pinta mais forte quanto mais abaixo da mediana / stronger below the median", () => {
    const forte = classeDoValor(classes, distancia(0.5));
    const fraca = classeDoValor(classes, distancia(1.5));
    expect(forte?.variavel).toBe("--color-chart-sequential-5");
    expect(fraca?.variavel).toBe("--color-chart-sequential-1");
    expect(classeDoValor(classes, distancia(1))?.variavel).toBe("--color-chart-sequential-3");
  });

  it("diz a posição em relação à mediana numa frase curta / position phrase", () => {
    expect(posicao(0.69)).toBe("31% abaixo da mediana");
    expect(posicao(1.12)).toBe("12% acima da mediana");
    expect(posicao(1.001)).toBe("na mediana");
  });

  it("monta a escala de menos espaço, à esquerda, a mais espaço, à direita / scale direction", () => {
    expect(marcasDaEscala()).toEqual(["+30%", "+10%", "−10%", "−30%"]);
    const escala = legendaDeEspaco(classes);
    const extremos = [...escala.querySelectorAll(".escala__extremos span")].map(
      (s) => s.textContent,
    );
    expect(extremos).toEqual(["Menos espaço", "Mais espaço"]);
    const barra = /** @type {HTMLElement} */ (escala.querySelector(".escala__barra"));
    expect(barra.style.backgroundImage).toContain("var(--color-chart-sequential-1) 10%");
    expect(barra.style.backgroundImage).toContain("var(--color-chart-sequential-5) 90%");
  });
});

describe("a tabela e o CSV / table and CSV", () => {
  const todas = linhas(dados, TODAS);
  const opcoes = {
    linhasDaVisao: todas,
    todas: true,
    escolhida: "MG",
    legenda: "Carteira PJ por empresa",
    situacao: () => "",
    arquivo: "teste.csv",
  };

  it("lista as 27 UFs, com a de mais espaço em cima e a escolhida marcada / table rows", () => {
    const el = tabelaDaTela(opcoes);
    const botoes = [...el.querySelectorAll("[data-uf]")];
    expect(botoes).toHaveLength(27);
    expect(
      posicaoDaUf(todas, /** @type {string} */ (botoes[0].getAttribute("data-uf")))?.posicao,
    ).toBe(1);
    expect(el.querySelector('[data-uf="MG"]')?.getAttribute("aria-pressed")).toBe("true");
  });

  it("gera o CSV com ponto e vírgula, vírgula decimal e uma linha por UF / CSV format", () => {
    const texto = csv(todas, true, () => "");
    const linhasDoCsv = texto.trim().split("\r\n");
    expect(linhasDoCsv).toHaveLength(28);
    expect(linhasDoCsv[0].split(";")[0]).toBe("UF");
    const sp = linhasDoCsv.find((l) => l.startsWith("São Paulo;"));
    expect(sp).toMatch(/^São Paulo;\d+;0,\d{6};/);
  });
});

describe("o perfil da UF / state profile", () => {
  const todas = linhas(dados, TODAS);
  const mg = /** @type {import("../../src/visoes/credito-por-uf/dados.js").LinhaDaVisao} */ (
    todas.find((l) => l.uf === "MG")
  );

  it("traz a carteira, a posição e as modalidades da UF / profile content", () => {
    /** @type {string[]} */
    const escolhidas = [];
    const perfil = perfilDaUf({
      linha: mg,
      linhasDaVisao: todas,
      decisao: dados.decisao,
      todas: true,
      modalidade: TODAS,
      subtitulo: "Todas as modalidades · jul/2026",
      nota: "",
      comDefinicao: () => undefined,
      aoEscolherModalidade: (codigo) => escolhidas.push(codigo),
    });
    expect(perfil.titulo).toBe("Minas Gerais");
    expect(perfil.itens.map((item) => item.chave)).toContain("Carteira PJ");
    const lugar = posicaoDaUf(todas, "MG");
    expect(perfil.itens.some((item) => item.valor === `${lugar?.posicao}ª menor de 27`)).toBe(true);
    const botao = /** @type {HTMLButtonElement} */ (
      perfil.complemento &&
        /** @type {HTMLElement} */ (perfil.complemento).querySelector("[data-modalidade]")
    );
    botao.click();
    expect(escolhidas).toHaveLength(1);
  });
});

describe("o estado dos filtros / filter state", () => {
  it("avisa uma vez só, com as chaves que mudaram de fato / fires once with changed keys", () => {
    const filtros = new Filtros({
      modalidade: TODAS,
      uf: /** @type {string | null} */ (null),
      desenho: "mapa",
    });
    /** @type {string[][]} */
    const avisos = [];
    filtros.aoMudar((evento) => avisos.push(/** @type {string[]} */ (evento.detail.chaves)));
    filtros.definir({ uf: "MG", modalidade: "04", desenho: "mapa" });
    filtros.definir({ uf: "MG" });
    expect(avisos).toEqual([["uf", "modalidade"]]);
    expect(filtros.valores).toEqual({ modalidade: "04", uf: "MG", desenho: "mapa" });
  });

  it("aceita as quatro formas do território / four territory forms", () => {
    const filtros = new Filtros({ desenho: "mapa" });
    for (const forma of ["grade", "matriz", "tabela", "mapa"]) {
      filtros.definir({ desenho: forma });
      expect(filtros.valores.desenho).toBe(forma);
    }
  });
});
