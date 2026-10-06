/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes da Tela 2 (#70) contra os arquivos de dados de verdade, os de
 *     `public/data/`: as linhas de cada modalidade, o resumo, o ranking, a
 *     matriz, a série mensal, a cor, a escala, a mudança de critério do
 *     ativo problemático e o CSV. Os números conferidos aqui são os que o
 *     mart exportou (RF-201): o site só soma, conta, ordena e tira a
 *     diferença entre duas colunas da mesma linha.
 * EN: Screen 2 tests against the real exported data files.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { classeDoValor } from "../../src/graficos/escalas.js";
import {
  classesDoRisco,
  legendaDoRisco,
  marcasDaEscala,
} from "../../src/visoes/risco-por-uf/cor.js";
import {
  celulasDaMatriz,
  dataDaQuebra,
  janelaCruzaAQuebra,
  linhas,
  modalidades,
  ordenar,
  ranking,
  resumo,
  serieDaUf,
  ufsPorCarteira,
} from "../../src/visoes/risco-por-uf/dados.js";
import { perfilDaUf } from "../../src/visoes/risco-por-uf/perfil.js";
import { csv, tabelaDaTela } from "../../src/visoes/risco-por-uf/tabela.js";

const PASTA = join(dirname(fileURLToPath(import.meta.url)), "../../public/data/");
const ler = (/** @type {string} */ nome) => JSON.parse(readFileSync(`${PASTA}${nome}`, "utf8"));
const decisao = ler("decisao.json");
const mensal = ler("carteira_mensal_pj.json");
const ontologia = ler("ontologia.json");
/** @type {Record<string, any[]>} */
const c = decisao.colunas;
const EMPRESTIMOS = "02";

/**
 * PT: Os índices das células comparadas de uma modalidade, lidos direto do
 *     arquivo, para conferir o que a tela calcula por outro caminho.
 * EN: Compared cells of a modality, read straight from the file.
 *
 * @param {string} codigo
 * @returns {number[]}
 */
function comparadas(codigo) {
  return c.uf.map((_, i) => i).filter((i) => c.codigo_modalidade[i] === codigo && c.avaliada[i]);
}

describe("as linhas da Tela 2 / screen rows", () => {
  const emprestimos = linhas(decisao, EMPRESTIMOS);

  it("trazem as 27 UFs, todas comparadas em Empréstimos / 27 states, all compared", () => {
    expect(emprestimos).toHaveLength(27);
    expect(emprestimos.every((l) => l.situacao === "comparada")).toBe(true);
  });

  it("piorar mais que o país é o quadrante do mart, e concorda com o sinal da diferença / worsening follows the mart quadrant", () => {
    for (const { codigo } of modalidades(decisao)) {
      for (const linha of linhas(decisao, codigo)) {
        if (linha.situacao !== "comparada") {
          expect(linha.piorando).toBe(false);
          expect(linha.contraOPais).toBeNull();
          continue;
        }
        expect(linha.piorando).toBe(/** @type {number} */ (linha.contraOPais) > 0);
        expect(linha.piorando).toBe(
          linha.quadrante === "observar" || linha.quadrante === "nao-entrar",
        );
      }
    }
  });

  it("a diferença contra o país é a do mart, linha a linha / excess change matches the file", () => {
    const ma = emprestimos.find((l) => l.uf === "MA");
    const i = c.uf.findIndex((uf, k) => uf === "MA" && c.codigo_modalidade[k] === EMPRESTIMOS);
    expect(ma?.taxa).toBe(c.taxa_inadimplencia[i]);
    expect(ma?.contraOPais).toBeCloseTo(
      c.variacao_taxa_inadimplencia[i] - c.variacao_taxa_pais[i],
      9,
    );
    expect(ma?.alerta).toBe(true);
    expect(ma?.quadrante).toBe("observar");
  });

  it("a UF sem carteira na modalidade fica sem número / states without portfolio stay blank", () => {
    const importacao = linhas(decisao, "06");
    expect(importacao.find((l) => l.uf === "AC")?.situacao).toBe("sem-carteira");
  });
});

describe("o resumo e o ranking / summary and ranking", () => {
  const emprestimos = linhas(decisao, EMPRESTIMOS);
  const r = resumo(emprestimos);

  it("contam as UFs que pioraram e as com alerta, como o mart / counts match the mart", () => {
    const indices = comparadas(EMPRESTIMOS);
    const piorando = indices.filter((i) => ["observar", "não entrar"].includes(c.quadrante[i]));
    expect(r.comparadas).toBe(27);
    expect(r.piorando).toBe(piorando.length);
    expect(r.piorando).toBe(15);
    expect(r.alertas).toBe(indices.filter((i) => c.alerta_antecipado[i]).length);
    expect(r.alertas).toBe(13);
  });

  it("somam o custo do risco das UFs que pioraram / sum the risk cost of worsening states", () => {
    const esperado = comparadas(EMPRESTIMOS)
      .filter((i) => ["observar", "não entrar"].includes(c.quadrante[i]))
      .reduce((soma, i) => soma + c.custo_do_risco[i], 0);
    expect(r.custo).toBe(esperado);
    expect(r.custo / 1e9).toBeCloseTo(4.04, 2);
  });

  it("a taxa e a variação do país são as da modalidade / national rate and change", () => {
    const i = comparadas(EMPRESTIMOS)[0];
    expect(r.taxaPais).toBe(c.taxa_pais[i]);
    expect(r.variacaoPais).toBe(c.variacao_taxa_pais[i]);
  });

  it("o ranking tem as UFs que pioraram, com o marcador nas que têm alerta / ranking items", () => {
    const itens = ranking(emprestimos);
    expect(itens).toHaveLength(15);
    expect(itens.every((item) => item.valor > 0)).toBe(true);
    expect(
      itens
        .filter((item) => item.marcada)
        .map((item) => item.chave)
        .sort(),
    ).toEqual(["AM", "AP", "ES", "MA", "PB", "PR", "RO"].sort());
  });

  it("a tabela ordena da maior piora para a menor, com as de fora no fim / table order", () => {
    const ordem = ordenar(linhas(decisao, "05"));
    const valores = ordem.map((l) => l.contraOPais);
    const primeiroNulo = valores.indexOf(null);
    expect(primeiroNulo).toBeGreaterThan(0);
    expect(valores.slice(primeiroNulo).every((v) => v === null)).toBe(true);
    const numeros = /** @type {number[]} */ (valores.slice(0, primeiroNulo));
    expect(numeros).toEqual([...numeros].sort((a, b) => b - a));
  });

  it("uma modalidade sem UF comparável não tem piora nem custo / no comparable state", () => {
    const vazia = resumo(linhas(decisao, "01"));
    expect(vazia.comparadas).toBe(0);
    expect(vazia.piorando).toBe(0);
    expect(vazia.custo).toBe(0);
  });
});

describe("a matriz e as modalidades / heatmap and modalities", () => {
  it("as modalidades vêm da maior carteira para a menor / largest first", () => {
    const lista = modalidades(decisao);
    expect(lista[0].codigo).toBe(EMPRESTIMOS);
    expect(lista.map((m) => m.carteira)).toEqual(
      [...lista.map((m) => m.carteira)].sort((a, b) => b - a),
    );
  });

  it("a matriz tem uma célula por linha do arquivo, com valor só nas comparadas / one cell per row", () => {
    const celulas = celulasDaMatriz(decisao);
    expect(celulas).toHaveLength(c.uf.length);
    expect(celulas.filter((celula) => celula.contraOPais !== null)).toHaveLength(
      c.avaliada.filter(Boolean).length,
    );
  });

  it("as UFs da matriz são as 27, da maior carteira para a menor / 27 states", () => {
    const ufs = ufsPorCarteira(decisao);
    expect(ufs).toHaveLength(27);
    expect(ufs[0]).toBe("SP");
  });
});

describe("a série mensal e a mudança de critério / monthly series and the break", () => {
  it("a série da UF tem os 31 meses em ordem, com as duas taxas / 31 months, both rates", () => {
    const serie = serieDaUf(mensal, "MA", EMPRESTIMOS);
    expect(serie.meses).toHaveLength(31);
    expect(serie.meses).toEqual([...serie.meses].sort());
    expect(serie.meses.at(-1)).toBe(decisao.data_base);
    expect(serie.inadimplencia.at(-1)).toBeCloseTo(0.1247, 4);
    expect(serie.ativoProblematico.at(-1)).toBeCloseTo(0.1844, 4);
  });

  it("a data da mudança vem da ontologia / break date from the ontology", () => {
    expect(dataDaQuebra(ontologia)).toBe("2025-01-31");
  });

  it("a janela cruza a mudança só quando começa antes e termina nela ou depois (RF-203) / crossing rule", () => {
    const quebra = "2025-01-31";
    expect(janelaCruzaAQuebra("2026-01-31", "2026-07-31", quebra)).toBe(false);
    expect(janelaCruzaAQuebra("2024-12-31", "2025-06-30", quebra)).toBe(true);
    expect(janelaCruzaAQuebra("2024-07-31", "2025-01-31", quebra)).toBe(true);
    expect(janelaCruzaAQuebra("2025-01-31", "2025-07-31", quebra)).toBe(false);
    expect(janelaCruzaAQuebra("2024-01-31", "2024-07-31", quebra)).toBe(false);
    expect(janelaCruzaAQuebra("2024-12-31", "2025-06-30", null)).toBe(false);
  });

  it("a janela do arquivo de hoje não cruza a mudança, e o mensal concorda / today's window agrees with the monthly flag", () => {
    const anterior = c.data_base_anterior[0];
    const i = mensal.colunas.data_base.findIndex(
      (/** @type {string} */ d, /** @type {number} */ k) =>
        d === decisao.data_base && mensal.colunas.uf[k] === "MA",
    );
    expect(janelaCruzaAQuebra(anterior, decisao.data_base, dataDaQuebra(ontologia))).toBe(
      mensal.colunas.janela_6m_cruza_quebra_ativo_problematico[i],
    );
  });
});

describe("a cor e a escala / color and scale", () => {
  const classes = classesDoRisco()("claro");

  it("cinco faixas, com as divisas em 0,1 e 0,5 p.p. / five bands", () => {
    expect(classes).toHaveLength(5);
    const rotulo = (/** @type {number} */ v) => classeDoValor(classes, v)?.label;
    expect(rotulo(0.0008)).toBe(rotulo(-0.0008));
    expect(rotulo(0.0182)).not.toBe(rotulo(0.003));
    expect(rotulo(-0.0217)).not.toBe(rotulo(-0.003));
    expect(classeDoValor(classes, 0.0182)?.color).toBe(classes[0].color);
  });

  it("as marcas vão de melhor a pior que o país / marks from better to worse", () => {
    expect(marcasDaEscala()).toEqual(["−0,5", "−0,1", "+0,1", "+0,5"]);
  });

  it("a legenda leva o marcador de alerta só quando pedido / legend marker item on demand", () => {
    expect(
      legendaDoRisco({ comMarca: true })(classes).querySelector(".marcador-de-alerta"),
    ).not.toBeNull();
    expect(
      legendaDoRisco({ comMarca: false })(classes).querySelector(".marcador-de-alerta"),
    ).toBeNull();
  });
});

describe("o perfil e a tabela / profile and table", () => {
  const emprestimos = linhas(decisao, EMPRESTIMOS);
  const ma = /** @type {import("../../src/visoes/risco-por-uf/dados.js").LinhaDoRisco} */ (
    emprestimos.find((l) => l.uf === "MA")
  );

  it("o perfil mostra os números, o quadrante e o alerta, e reserva a série / profile content", () => {
    const { conteudo, serie } = perfilDaUf({
      linha: ma,
      subtitulo: "Empréstimos · jul/2026",
      meses: 6,
      nota: "",
      comDefinicao: () => undefined,
    });
    expect(conteudo.titulo).toBe("Maranhão");
    expect(conteudo.itens.map((item) => item.valor)).toEqual([
      "12,5%",
      "+2,28 p.p.",
      "+0,70 p.p.",
      "R$ 236,7 mi",
    ]);
    const complemento = /** @type {HTMLElement} */ (conteudo.complemento);
    expect(complemento.querySelector(".etiqueta--observar")).not.toBeNull();
    expect(complemento.querySelector(".etiqueta--alerta")).not.toBeNull();
    expect(complemento.textContent).toContain("0,38 p.p.");
    expect(complemento.contains(serie)).toBe(true);
  });

  it("a tabela tem as 27 UFs e as etiquetas de alerta das 13 / 27 rows, 13 warnings", () => {
    const el = tabelaDaTela({
      linhasDoRisco: emprestimos,
      escolhida: null,
      legenda: "Inadimplência",
      meses: 6,
      situacao: () => "",
      arquivo: "x.csv",
    });
    expect(el.querySelectorAll("tbody tr")).toHaveLength(27);
    expect(el.querySelectorAll("tbody .etiqueta--alerta")).toHaveLength(13);
  });

  it("o CSV tem o cabeçalho e uma linha por UF, com os números crus / CSV", () => {
    const texto = csv(ordenar(emprestimos), 6, () => "");
    const linhasDoCsv = texto.trim().split("\r\n");
    expect(linhasDoCsv).toHaveLength(28);
    expect(linhasDoCsv[0].split(";")).toHaveLength(12);
    expect(linhasDoCsv[1].startsWith("Piauí;")).toBe(true);
    expect(linhasDoCsv[1]).toContain(";0,018");
  });
});
