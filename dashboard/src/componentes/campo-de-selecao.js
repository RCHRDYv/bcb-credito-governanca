/**
 * PT: Campo de seleção: uma opção exclusiva entre muitas.
 *
 *     O controle segmentado aceita até cinco opções. Quando a escolha tem
 *     mais que isso, como as 13 modalidades mais "todas", o guia pede outro
 *     componente: um `<select>` nativo, com o visual do campo de texto (40 px,
 *     raio de controle, vidro regular e borda forte). O nativo traz de graça
 *     o teclado, o leitor de tela e a lista do sistema no celular.
 *
 *     O rótulo fica sempre fora do campo, ligado a ele, como no campo de
 *     texto. Um elemento de apoio, como o botão de definição da opção
 *     escolhida, pode ir ao lado do rótulo.
 *
 * EN: Select field for one exclusive choice among many (more than the
 *     segmented control's five). A native `<select>` styled like the text
 *     field, with the label always outside and an optional helper next to it.
 */

import { elemento } from "../dom.js";

/**
 * @typedef {object} OpcaoDaSelecao
 * @property {string} valor
 * @property {string} texto
 */

/**
 * @typedef {object} OpcoesDoCampoDeSelecao
 * @property {string} rotulo
 * @property {OpcaoDaSelecao[]} opcoes
 * @property {string} valor A opção escolhida no começo / initial value
 * @property {(valor: string) => void} [aoMudar]
 * @property {Node} [apoio] Vai ao lado do rótulo / goes next to the label
 */

let contador = 0;

/**
 * PT: Monta o campo de seleção.
 * EN: Builds the select field.
 *
 * @param {OpcoesDoCampoDeSelecao} opcoes
 * @returns {HTMLDivElement}
 */
export function campoDeSelecao({ rotulo, opcoes, valor, aoMudar, apoio }) {
  contador += 1;
  const id = `selecao-${contador}`;
  const selecao = elemento(
    "select",
    { classe: "campo__entrada campo__entrada--selecao", atributos: { id } },
    opcoes.map((opcao) =>
      elemento("option", { texto: opcao.texto, atributos: { value: opcao.valor } }),
    ),
  );
  selecao.value = valor;
  selecao.addEventListener("change", () => aoMudar?.(selecao.value));

  const rotuloEl = elemento("label", {
    classe: "campo__rotulo",
    texto: rotulo,
    atributos: { for: id },
  });
  const cabecalho = apoio
    ? elemento("div", { classe: "campo__cabecalho" }, [rotuloEl, apoio])
    : rotuloEl;
  return elemento("div", { classe: "campo campo--selecao" }, [cabecalho, selecao]);
}
