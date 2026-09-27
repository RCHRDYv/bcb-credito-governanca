/**
 * PT: Aviso: vidro levemente tingido pela cor do estado, com o ícone num
 *     círculo.
 *
 *     - **Informação,** para ressalvas, como a de que a UF é a da sede.
 *     - **Atenção,** para o que muda a leitura, como a quebra de critério.
 *       O círculo é amarelo, com o glifo escuro, como faz o Carbon.
 *     - **Erro,** quando algo não funcionou. O texto diz o problema e a
 *       saída, e nunca só "algo deu errado".
 *
 *     Não se empilham mais de dois avisos, e o que cabe num rótulo não vira
 *     aviso. Um aviso que aparece depois que a página abriu é anunciado a
 *     leitores de tela: o de erro com urgência, os outros com calma.
 *
 * EN: Notice tinted by its state color, with the icon in a circle. Notices
 *     that appear after load are announced (errors assertively).
 */

import { elemento } from "../dom.js";
import { icone } from "./icones.js";

/** @typedef {"informacao" | "atencao" | "erro"} TipoDeAviso */

/** @type {Record<TipoDeAviso, import("./icones.js").NomeDoIcone>} */
const ICONES = {
  informacao: "info-circle",
  atencao: "alert-triangle",
  erro: "circle-x",
};

/**
 * @typedef {object} OpcoesDoAviso
 * @property {TipoDeAviso} tipo
 * @property {string} texto
 * @property {boolean} [anunciar] Se aparece depois que a página abriu / announced
 */

/**
 * PT: Monta o aviso.
 * EN: Builds the notice.
 *
 * @param {OpcoesDoAviso} opcoes
 * @returns {HTMLDivElement}
 */
export function aviso({ tipo, texto, anunciar = false }) {
  /** @type {Record<string, string>} */
  const papel = anunciar ? { role: tipo === "erro" ? "alert" : "status" } : {};
  return elemento("div", { classe: `aviso aviso--${tipo}`, atributos: papel }, [
    elemento("span", { classe: "aviso__icone" }, [icone(ICONES[tipo])]),
    elemento("p", { classe: "aviso__texto", texto }),
  ]);
}
