/**
 * PT: As peças do chat: a pergunta, a resposta, a abstenção e a entrada.
 *
 *     - **Pergunta:** numa bolha azul 60.
 *     - **Resposta:** em vidro regular, nesta ordem: o número em tamanho
 *       grande, a frase curta, as ressalvas num aviso de informação, e o
 *       SQL recolhido atrás de "Ver o SQL". Número sem o SQL não entra.
 *     - **Abstenção:** quando o dado não permite responder, diz isso e diz o
 *       que faltaria.
 *     - **Entrada:** uma cápsula de vidro com o botão circular de enviar.
 *
 *     A conversa é um registro que leitores de tela acompanham com calma.
 *     O chat só aparece nas visões que o preveem, e o cliente do Space, com
 *     o destaque de cor do SQL, entra na #51.
 *
 * EN: Chat pieces: question, answer (number, sentence, caveats, collapsed
 *     SQL), abstention and input. The Space client arrives with #51.
 */

import { elemento } from "../dom.js";
import { t } from "../textos/index.js";
import { aviso } from "./aviso.js";
import { icone } from "./icones.js";

let contador = 0;

/**
 * PT: A conversa: um registro que anuncia as mensagens novas.
 * EN: The conversation, a polite live log.
 *
 * @param {Node[]} mensagens
 * @returns {HTMLDivElement}
 */
export function conversa(mensagens) {
  return elemento(
    "div",
    { classe: "conversa", atributos: { role: "log", "aria-label": t("chat.conversa") } },
    mensagens,
  );
}

/**
 * PT: A pergunta de quem usa o dashboard.
 * EN: The visitor's question.
 *
 * @param {string} texto
 * @returns {HTMLParagraphElement}
 */
export function perguntaDoChat(texto) {
  return elemento("p", { classe: "chat-pergunta" }, [
    elemento("span", { classe: "visualmente-oculto", texto: `${t("chat.pergunta")}: ` }),
    texto,
  ]);
}

/**
 * @typedef {object} Resposta
 * @property {string} numero Já formatado, tirado do resultado da consulta / formatted
 * @property {string} frase
 * @property {string[]} [ressalvas]
 * @property {string} sql
 */

/**
 * PT: A resposta, com o número vindo do resultado da consulta, e nunca do
 *     texto do modelo (RF-C03).
 * EN: The answer; the number comes from the query result.
 *
 * @param {Resposta} resposta
 * @returns {HTMLElement}
 */
export function respostaDoChat({ numero, frase, ressalvas = [], sql }) {
  return elemento(
    "article",
    { classe: "chat-resposta", atributos: { "aria-label": t("chat.resposta") } },
    [
      elemento("p", { classe: "chat-resposta__numero", texto: numero }),
      elemento("p", { classe: "chat-resposta__frase", texto: frase }),
      ...ressalvas.map((texto) => aviso({ tipo: "informacao", texto })),
      elemento("details", { classe: "chat-resposta__sql" }, [
        elemento("summary", {}, [
          icone("chevron-right"),
          elemento("span", { texto: t("chat.ver-o-sql") }),
        ]),
        elemento("pre", {}, [elemento("code", { texto: sql })]),
      ]),
    ],
  );
}

/**
 * @typedef {object} Abstencao
 * @property {string} motivo Por que o dado não permite responder / why not
 * @property {string} faltaria O que seria preciso / what would be needed
 */

/**
 * PT: A abstenção: sem número, com o motivo e o que faltaria.
 * EN: The abstention: no number, the reason and what is missing.
 *
 * @param {Abstencao} abstencao
 * @returns {HTMLElement}
 */
export function abstencaoDoChat({ motivo, faltaria }) {
  return elemento(
    "article",
    {
      classe: "chat-resposta chat-resposta--abstencao",
      atributos: { "aria-label": t("chat.resposta") },
    },
    [
      elemento("p", { classe: "chat-resposta__titulo", texto: t("chat.abstencao") }),
      elemento("p", { classe: "chat-resposta__frase", texto: motivo }),
      elemento("p", { classe: "chat-resposta__frase", texto: faltaria }),
    ],
  );
}

/**
 * @typedef {object} OpcoesDaEntrada
 * @property {(pergunta: string) => void} [aoEnviar]
 * @property {boolean} [desativada]
 */

/**
 * PT: A entrada do chat. Enviar com o campo vazio não faz nada.
 * EN: The chat input; empty submissions are ignored.
 *
 * @param {OpcoesDaEntrada} [opcoes]
 * @returns {HTMLFormElement}
 */
export function entradaDoChat({ aoEnviar, desativada = false } = {}) {
  contador += 1;
  const id = `pergunta-${contador}`;
  const campo = elemento("input", {
    classe: "chat-entrada__campo",
    atributos: { id, type: "text", placeholder: t("chat.exemplo"), autocomplete: "off" },
  });
  campo.disabled = desativada;
  const enviar = elemento(
    "button",
    {
      classe: "chat-entrada__enviar",
      atributos: { type: "submit", "aria-label": t("chat.enviar") },
    },
    [icone("arrow-up")],
  );
  enviar.disabled = desativada;

  const formulario = elemento("form", { classe: "chat-entrada" }, [
    elemento("label", {
      classe: "visualmente-oculto",
      texto: t("chat.rotulo-da-entrada"),
      atributos: { for: id },
    }),
    campo,
    enviar,
  ]);
  formulario.addEventListener("submit", (evento) => {
    // PT: nada é enviado pelo navegador; a pergunta vai pelo cliente do chat
    // EN: the browser never submits; the chat client sends the question
    evento.preventDefault();
    const pergunta = campo.value.trim();
    if (!pergunta) return;
    aoEnviar?.(pergunta);
    campo.value = "";
  });
  return formulario;
}
