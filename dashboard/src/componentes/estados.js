/**
 * PT: Os estados de carregamento e de exceção.
 *
 *     - **Carregando:** barras em cápsula com um brilho passando, no lugar
 *       do conteúdo. Nunca um indicador girando no meio da tela.
 *     - **Vazio:** explica por que está vazio e como sair disso.
 *     - **Erro:** diz o problema e oferece tentar de novo.
 *     - **Chat acordando:** um orbe de vidro que respira devagar, com o
 *       aviso de que as outras telas continuam funcionando.
 *
 *     Com movimento reduzido, o brilho e a respiração param.
 *
 * EN: Loading and exception states: shimmering capsule bars, empty with a
 *     way out, error with retry, and the chat waking up.
 */

import { elemento } from "../dom.js";
import { t } from "../textos/index.js";
import { botao } from "./botao.js";

/**
 * PT: Carregando: três barras, e o texto só para leitores de tela.
 * EN: Loading: three bars, with text for screen readers only.
 *
 * @param {string} [rotulo] O que está carregando / what is loading
 * @returns {HTMLDivElement}
 */
export function carregando(rotulo = t("estado.carregando")) {
  return elemento(
    "div",
    { classe: "carregando", atributos: { role: "status", "aria-busy": "true" } },
    [
      elemento("span", { classe: "visualmente-oculto", texto: rotulo }),
      ...[1, 2, 3].map(() =>
        elemento("span", { classe: "carregando__barra", atributos: { "aria-hidden": "true" } }),
      ),
    ],
  );
}

/**
 * @typedef {object} OpcoesDoEstado
 * @property {string} titulo
 * @property {string} texto Por que e como sair / why, and the way out
 */

/**
 * PT: Vazio: por que está vazio e como sair disso.
 * EN: Empty: why, and how to get out of it.
 *
 * @param {OpcoesDoEstado} opcoes
 * @returns {HTMLDivElement}
 */
export function vazio({ titulo, texto }) {
  return elemento("div", { classe: "estado" }, [
    elemento("p", { classe: "estado__titulo", texto: titulo }),
    elemento("p", { classe: "estado__texto", texto }),
  ]);
}

/**
 * PT: Erro: o problema e o botão de tentar de novo. É anunciado com
 *     urgência, porque aparece no lugar de algo que a pessoa esperava.
 * EN: Error with a retry button, announced assertively.
 *
 * @param {OpcoesDoEstado & { aoTentarDeNovo: () => void }} opcoes
 * @returns {HTMLDivElement}
 */
export function erro({ titulo, texto, aoTentarDeNovo }) {
  return elemento("div", { classe: "estado estado--erro", atributos: { role: "alert" } }, [
    elemento("p", { classe: "estado__titulo", texto: titulo }),
    elemento("p", { classe: "estado__texto", texto }),
    botao({
      texto: t("estado.tentar-de-novo"),
      variante: "secundario",
      icone: "refresh",
      aoClicar: () => aoTentarDeNovo(),
    }),
  ]);
}

/**
 * PT: O chat acordando, enquanto o Space sai do repouso.
 * EN: The chat waking up while the Space starts.
 *
 * @returns {HTMLDivElement}
 */
export function chatAcordando() {
  return elemento("div", { classe: "estado estado--acordando", atributos: { role: "status" } }, [
    elemento("span", { classe: "estado__orbe", atributos: { "aria-hidden": "true" } }),
    elemento("p", { classe: "estado__titulo", texto: t("estado.chat-acordando") }),
    elemento("p", { classe: "estado__texto", texto: t("estado.chat-acordando-texto") }),
  ]);
}
