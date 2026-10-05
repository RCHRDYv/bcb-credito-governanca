/**
 * PT: Painel de detalhe (RF-G05): os números de um elemento escolhido.
 *
 *     Lista de chave e valor, com os números à direita e com unidade, em
 *     vidro regular, como o guia pede. No computador, o painel fica ao lado
 *     do conteúdo, sem janela por cima. No celular, vira uma folha que sobe
 *     de baixo quando um elemento é escolhido, como o modelo de página do
 *     celular desenha, e o botão de fechar a recolhe.
 *
 *     Sem elemento escolhido, o painel diz como escolher um. A troca de
 *     conteúdo é anunciada com calma a leitores de tela.
 *
 * EN: Detail panel: key-value list with right-aligned numbers and units.
 *     Beside the content on desktop, a bottom sheet on phones. With nothing
 *     chosen it says how to choose; changes are announced politely.
 */

import { elemento } from "../dom.js";
import { t } from "../textos/index.js";
import { icone } from "./icones.js";

/**
 * @typedef {object} ItemDoDetalhe
 * @property {string} chave O nome do número / the number's name
 * @property {string} valor Já formatado, com unidade / formatted, with unit
 * @property {Node} [apoio] Vai ao lado do nome, como a definição / next to the name
 */

/**
 * @typedef {object} ConteudoDoDetalhe
 * @property {string} titulo O elemento escolhido, como o nome da UF / chosen element
 * @property {string} [subtitulo] O recorte, como a modalidade / the cut
 * @property {ItemDoDetalhe[]} itens
 * @property {string} [nota] Ressalva sobre o elemento / caveat
 * @property {Node} [complemento] Vai depois da lista, como as modalidades de uma UF / goes after the list
 */

/**
 * @typedef {object} PainelDeDetalhe
 * @property {HTMLElement} elemento
 * @property {(conteudo: ConteudoDoDetalhe) => void} mostrar
 * @property {() => void} limpar Volta ao texto de como escolher / back to the hint
 */

/**
 * PT: Monta o painel, vazio.
 * EN: Builds the panel, empty.
 *
 * @param {object} opcoes
 * @param {string} opcoes.dica Como escolher um elemento / how to choose one
 * @param {() => void} [opcoes.aoFechar] Quando a pessoa fecha / when closed
 * @returns {PainelDeDetalhe}
 */
export function painelDeDetalhe({ dica, aoFechar }) {
  const corpo = elemento("div", { classe: "detalhe__corpo", atributos: { "aria-live": "polite" } });
  const fechar = elemento(
    "button",
    {
      classe: "detalhe__fechar",
      atributos: { type: "button", "aria-label": t("detalhe.fechar"), hidden: "" },
    },
    [icone("x")],
  );
  const el = elemento(
    "aside",
    { classe: "detalhe", atributos: { "aria-label": t("detalhe.rotulo") } },
    [fechar, corpo],
  );

  /**
   * @param {ConteudoDoDetalhe} conteudo
   * @returns {Node[]}
   */
  const conteudoDe = ({ titulo, subtitulo, itens, nota, complemento }) => {
    const lista = elemento(
      "dl",
      { classe: "detalhe__lista" },
      itens.flatMap((item) => [
        elemento("dt", { classe: "detalhe__chave" }, [
          item.chave,
          ...(item.apoio ? [item.apoio] : []),
        ]),
        elemento("dd", { classe: "detalhe__valor", texto: item.valor }),
      ]),
    );
    return [
      elemento("h2", { classe: "detalhe__titulo", texto: titulo }),
      ...(subtitulo ? [elemento("p", { classe: "detalhe__subtitulo", texto: subtitulo })] : []),
      lista,
      ...(complemento ? [complemento] : []),
      ...(nota ? [elemento("p", { classe: "detalhe__nota", texto: nota })] : []),
    ];
  };

  const limpar = () => {
    el.classList.remove("detalhe--aberto");
    fechar.hidden = true;
    corpo.replaceChildren(elemento("p", { classe: "detalhe__dica", texto: dica }));
  };

  fechar.addEventListener("click", () => {
    limpar();
    aoFechar?.();
  });

  /** @param {ConteudoDoDetalhe} conteudo */
  const mostrar = (conteudo) => {
    corpo.replaceChildren(...conteudoDe(conteudo));
    fechar.hidden = false;
    el.classList.add("detalhe--aberto");
  };

  limpar();
  return { elemento: el, mostrar, limpar };
}
