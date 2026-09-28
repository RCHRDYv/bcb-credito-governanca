/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes das peças do chat (#64).
 * EN: Chat piece tests.
 */

import { describe, expect, it, vi } from "vitest";
import {
  abstencaoDoChat,
  conversa,
  entradaDoChat,
  perguntaDoChat,
  respostaDoChat,
} from "../../../src/componentes/chat.js";

describe("conversa()", () => {
  it("é um registro com nome / a named log", () => {
    const el = conversa([perguntaDoChat("Quanto?")]);
    expect(el.getAttribute("role")).toBe("log");
    expect(el.getAttribute("aria-label")).toBeTruthy();
  });
});

describe("respostaDoChat()", () => {
  it("põe número, frase, ressalvas e o SQL recolhido, nessa ordem / ordered parts", () => {
    const el = respostaDoChat({
      numero: "R$ 128,8 mil",
      frase: "em jul/2026.",
      ressalvas: ["A UF é a da sede."],
      sql: "select 1",
    });
    const filhos = [...el.children].map((filho) => filho.className);
    expect(filhos).toEqual([
      "chat-resposta__numero",
      "chat-resposta__frase",
      "aviso aviso--informacao",
      "chat-resposta__sql",
    ]);
    const detalhes = /** @type {HTMLDetailsElement} */ (el.querySelector("details"));
    expect(detalhes.open).toBe(false);
    expect(detalhes.querySelector("summary")?.textContent).toBe("Ver o SQL");
    expect(detalhes.querySelector("pre code")?.textContent).toBe("select 1");
  });
});

describe("abstencaoDoChat()", () => {
  it("diz que não dá para responder, o motivo e o que faltaria, sem número", () => {
    const el = abstencaoDoChat({ motivo: "Sem instituição.", faltaria: "O dado por banco." });
    expect(el.textContent).toContain("Não dá para responder");
    expect(el.textContent).toContain("Sem instituição.");
    expect(el.textContent).toContain("O dado por banco.");
    expect(el.querySelector(".chat-resposta__numero")).toBeNull();
  });
});

describe("entradaDoChat()", () => {
  it("tem rótulo e botão com nome / labelled input and named button", () => {
    const el = entradaDoChat();
    const campo = /** @type {HTMLInputElement} */ (el.querySelector("input"));
    expect(el.querySelector(`label[for="${campo.id}"]`)).not.toBeNull();
    expect(el.querySelector('button[type="submit"]')?.getAttribute("aria-label")).toBeTruthy();
  });

  it("envia a pergunta, limpa o campo e ignora campo vazio / submits and ignores empty", () => {
    const aoEnviar = vi.fn();
    const el = entradaDoChat({ aoEnviar });
    document.body.replaceChildren(el);
    const campo = /** @type {HTMLInputElement} */ (el.querySelector("input"));
    el.requestSubmit();
    expect(aoEnviar).not.toHaveBeenCalled();
    campo.value = "  Qual a carteira em SP?  ";
    el.requestSubmit();
    expect(aoEnviar).toHaveBeenCalledWith("Qual a carteira em SP?");
    expect(campo.value).toBe("");
  });

  it("desativa o campo e o botão / disables both", () => {
    const el = entradaDoChat({ desativada: true });
    expect(/** @type {HTMLInputElement} */ (el.querySelector("input")).disabled).toBe(true);
    expect(/** @type {HTMLButtonElement} */ (el.querySelector("button")).disabled).toBe(true);
  });
});
