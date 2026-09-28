/**
 * PT: Testes do carregador dos arquivos do contrato (#66). O `fetch` é
 *     simulado, e cada teste importa o módulo de novo, para a memória dos
 *     arquivos já carregados começar vazia. O último bloco passa os arquivos
 *     de verdade, os de `public/data/`, pelo carregador.
 * EN: Loader tests with a stubbed `fetch`; each test re-imports the module so
 *     its cache starts empty. The last block runs the real exported files
 *     through the loader.
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const PASTA_DOS_DADOS = fileURLToPath(new URL("../../public/data/", import.meta.url));

const DECISAO = {
  arquivo: "decisao.json",
  data_base: "2026-07-31",
  colunas: { uf: ["SP", "MG"], carteira_ativa: [100, 42] },
};

/**
 * PT: Uma resposta HTTP com o corpo dado / EN: an HTTP response
 *
 * @param {unknown} corpo
 * @param {number} [status]
 */
function resposta(corpo, status = 200) {
  const texto = typeof corpo === "string" ? corpo : JSON.stringify(corpo);
  return new Response(texto, { status });
}

/** PT: o módulo recém-importado / EN: a freshly imported module */
async function carregador() {
  vi.resetModules();
  return import("../../src/dados/carregar.js");
}

let buscar = vi.fn();

beforeEach(() => {
  buscar = vi.fn();
  vi.stubGlobal("fetch", buscar);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("carregar()", () => {
  it("busca o arquivo na pasta de dados e devolve o conteúdo / fetches and returns", async () => {
    buscar.mockResolvedValue(resposta(DECISAO));
    const { carregar } = await carregador();
    await expect(carregar("decisao.json")).resolves.toEqual(DECISAO);
    expect(buscar).toHaveBeenCalledWith("./data/decisao.json");
  });

  it("busca uma vez só quando duas visões pedem o mesmo arquivo / fetches once", async () => {
    buscar.mockResolvedValue(resposta(DECISAO));
    const { carregar } = await carregador();
    await Promise.all([carregar("decisao.json"), carregar("decisao.json")]);
    expect(buscar).toHaveBeenCalledTimes(1);
  });

  it("status de erro vira falha de rede / HTTP error is a network failure", async () => {
    buscar.mockResolvedValue(resposta("não achei", 404));
    const { carregar, ErroDeCarga } = await carregador();
    const falha = carregar("decisao.json");
    await expect(falha).rejects.toBeInstanceOf(ErroDeCarga);
    await expect(falha).rejects.toMatchObject({ motivo: "rede", arquivo: "decisao.json" });
  });

  it("sem conexão também é falha de rede / no connection is a network failure", async () => {
    buscar.mockRejectedValue(new TypeError("Failed to fetch"));
    const { carregar } = await carregador();
    await expect(carregar("decisao.json")).rejects.toMatchObject({ motivo: "rede" });
  });

  it("JSON quebrado é falha de formato / broken JSON is a format failure", async () => {
    buscar.mockResolvedValue(resposta("{ isto não é json"));
    const { carregar } = await carregador();
    await expect(carregar("decisao.json")).rejects.toMatchObject({ motivo: "formato" });
  });

  it("arquivo com outro nome é falha de formato / wrong file name is a format failure", async () => {
    buscar.mockResolvedValue(resposta({ ...DECISAO, arquivo: "outro.json" }));
    const { carregar } = await carregador();
    await expect(carregar("decisao.json")).rejects.toMatchObject({ motivo: "formato" });
  });

  it("arquivo sem colunas é falha de formato / missing columns is a format failure", async () => {
    buscar.mockResolvedValue(resposta({ arquivo: "decisao.json", data_base: "2026-07-31" }));
    const { carregar } = await carregador();
    await expect(carregar("decisao.json")).rejects.toMatchObject({ motivo: "formato" });
  });

  it("a falha não fica guardada, e tentar de novo busca outra vez / retry refetches", async () => {
    buscar.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    buscar.mockResolvedValueOnce(resposta(DECISAO));
    const { carregar } = await carregador();
    await expect(carregar("decisao.json")).rejects.toMatchObject({ motivo: "rede" });
    await expect(carregar("decisao.json")).resolves.toEqual(DECISAO);
    expect(buscar).toHaveBeenCalledTimes(2);
  });
});

describe("emLinhas()", () => {
  it("converte as colunas em uma linha por registro / columns to rows", async () => {
    const { emLinhas } = await carregador();
    expect(emLinhas(DECISAO)).toEqual([
      { uf: "SP", carteira_ativa: 100 },
      { uf: "MG", carteira_ativa: 42 },
    ]);
  });

  it("arquivo sem colunas dá nenhuma linha / no columns gives no rows", async () => {
    const { emLinhas } = await carregador();
    expect(emLinhas({ arquivo: "x.json", data_base: "2026-07-31", colunas: {} })).toEqual([]);
  });
});

describe("os arquivos exportados / the exported files", () => {
  /**
   * PT: Serve os arquivos de `public/data/` pelo `fetch` simulado.
   * EN: Serves `public/data/` files through the stubbed `fetch`.
   *
   * @param {string} endereco
   */
  function servirDoDisco(endereco) {
    const nome = endereco.replace("./data/", "");
    return Promise.resolve(resposta(readFileSync(`${PASTA_DOS_DADOS}${nome}`, "utf-8")));
  }

  it("cada arquivo do manifesto passa pelo carregador / every manifest file loads", async () => {
    buscar.mockImplementation(servirDoDisco);
    const { carregar, carregarManifesto, carregarOntologia, emLinhas } = await carregador();

    const manifesto = await carregarManifesto();
    expect(manifesto.arquivos.length).toBeGreaterThan(0);
    const ontologia = await carregarOntologia();
    expect(ontologia.conceitos.length).toBeGreaterThan(0);

    for (const { arquivo, linhas } of manifesto.arquivos) {
      if (arquivo === "ontologia.json") continue;
      const dados = await carregar(arquivo);
      expect(dados.data_base).toBe(manifesto.data_base);
      expect(emLinhas(dados)).toHaveLength(linhas);
    }
  });

  it("toda coluna de dado tem definição no ontologia.json / every column has a definition", async () => {
    buscar.mockImplementation(servirDoDisco);
    const { carregar, carregarManifesto, carregarOntologia } = await carregador();
    const manifesto = await carregarManifesto();
    const ontologia = await carregarOntologia();
    const refs = new Set(ontologia.conceitos.map((conceito) => conceito.ref));

    for (const { arquivo } of manifesto.arquivos) {
      if (arquivo === "ontologia.json") continue;
      const dados = await carregar(arquivo);
      for (const coluna of Object.keys(dados.colunas)) {
        const definicao = ontologia.colunas[arquivo]?.[coluna];
        expect(definicao, `${arquivo}: ${coluna}`).toBeTruthy();
        // PT: conceito com âncora precisa estar no arquivo / anchored concepts must exist
        if (definicao?.includes("#")) expect(refs.has(definicao), definicao).toBe(true);
      }
    }
  });
});
