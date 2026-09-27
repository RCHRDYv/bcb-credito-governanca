/**
 * PT: Testes do acesso aos textos da interface (RNF-13).
 * EN: Tests for interface text access.
 */

import { describe, expect, it } from "vitest";
import { t } from "../../src/textos/index.js";
import { ptBR } from "../../src/textos/pt-BR.js";

describe("t()", () => {
  it("devolve o texto da chave / returns the text for a key", () => {
    expect(t("produto.nome")).toBe("Crédito PJ");
  });

  it("falha com chave desconhecida / throws on an unknown key", () => {
    // @ts-expect-error chave que não existe, de propósito / unknown key, on purpose
    expect(() => t("chave.que.nao.existe")).toThrow(/chave.que.nao.existe/);
  });
});

describe("arquivo de tradução / translation file", () => {
  it("não tem texto vazio / has no empty text", () => {
    for (const [chave, texto] of Object.entries(ptBR)) {
      expect(texto.trim(), chave).not.toBe("");
    }
  });
});
