/**
 * PT: Campo de texto em vidro, com o rótulo sempre fora do campo.
 *
 *     O rótulo nunca é o texto de exemplo, porque o exemplo some quando a
 *     pessoa começa a digitar. O texto de ajuda e a mensagem de erro ficam
 *     embaixo, ligados ao campo por `aria-describedby`. O erro diz o problema
 *     e como resolver, com ícone, e marca o campo com `aria-invalid`.
 *
 * EN: Glass text field with the label always outside. Help and error text
 *     sit below, linked by `aria-describedby`; errors set `aria-invalid`.
 */

import { elemento } from "../dom.js";
import { icone } from "./icones.js";

let contador = 0;

/**
 * @typedef {object} OpcoesDoCampo
 * @property {string} rotulo
 * @property {string} [valor]
 * @property {string} [exemplo] Texto de exemplo dentro do campo / placeholder
 * @property {string} [ajuda]
 * @property {string} [erro] Diz o problema e a saída / problem and way out
 * @property {boolean} [desativado]
 * @property {string} [nome] Atributo `name` / name attribute
 */

/**
 * PT: Monta o campo.
 * EN: Builds the field.
 *
 * @param {OpcoesDoCampo} opcoes
 * @returns {HTMLDivElement}
 */
export function campo({ rotulo, valor = "", exemplo, ajuda, erro, desativado = false, nome }) {
  contador += 1;
  const id = `campo-${contador}`;
  const descricoes = [];
  const embaixo = [];
  if (ajuda) {
    descricoes.push(`${id}-ajuda`);
    embaixo.push(
      elemento("p", { classe: "campo__ajuda", texto: ajuda, atributos: { id: `${id}-ajuda` } }),
    );
  }
  if (erro) {
    descricoes.push(`${id}-erro`);
    embaixo.push(
      elemento("p", { classe: "campo__erro", atributos: { id: `${id}-erro` } }, [
        icone("alert-circle"),
        elemento("span", { texto: erro }),
      ]),
    );
  }

  const entrada = elemento("input", {
    classe: "campo__entrada",
    atributos: {
      id,
      type: "text",
      ...(nome ? { name: nome } : {}),
      ...(exemplo ? { placeholder: exemplo } : {}),
      ...(descricoes.length ? { "aria-describedby": descricoes.join(" ") } : {}),
      ...(erro ? { "aria-invalid": "true" } : {}),
    },
  });
  entrada.value = valor;
  entrada.disabled = desativado;

  return elemento("div", { classe: `campo${erro ? " campo--erro" : ""}` }, [
    elemento("label", { classe: "campo__rotulo", texto: rotulo, atributos: { for: id } }),
    entrada,
    ...embaixo,
  ]);
}
