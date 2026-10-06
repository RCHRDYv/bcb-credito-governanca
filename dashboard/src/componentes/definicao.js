/**
 * PT: A definição de um número, a um clique do próprio número (RF-G07).
 *
 *     Um botão pequeno, com o ícone de informação, fica junto do rótulo. Ele
 *     abre um popover nativo (ADR 0017, decisão 3) com o que a ontologia diz:
 *     a explicação em palavras comuns, quando existe, a definição oficial, a
 *     fonte e a confiança. Quando a regra foi fixada pelo projeto, o popover
 *     diz isso e leva ao ADR.
 *
 *     O popover nativo fecha com o Esc e com um clique fora, e o navegador
 *     devolve o foco ao botão. Ele abre junto do botão, e não no meio da
 *     tela, para não cobrir o número que a pessoa está lendo.
 *
 * EN: A number's definition, one click away from the number. A small info
 *     button opens a native popover with the plain explanation, the official
 *     definition, source and confidence, or the ADR that set the rule. Esc
 *     and outside clicks close it, and it opens next to its button.
 */

import { elemento } from "../dom.js";
import { t } from "../textos/index.js";
import { icone } from "./icones.js";

/** @typedef {import("../dados/definicoes.js").Definicao} Definicao */
/** @typedef {import("../textos/index.js").ChaveDeTexto} ChaveDeTexto */

/** @type {Record<string, ChaveDeTexto>} */
const CONFIANCA = {
  verbatim: "definicao.confianca-verbatim",
  parafraseado: "definicao.confianca-parafraseado",
  inferido: "definicao.confianca-inferido",
  lacuna: "definicao.confianca-lacuna",
};

let contador = 0;

/**
 * PT: O conteúdo do popover, pela origem da definição.
 * EN: The popover content, by where the definition comes from.
 *
 * @param {Definicao} definicao
 * @returns {Node[]}
 */
function conteudo(definicao) {
  if (definicao.tipo === "adr") {
    return [
      elemento("p", {
        classe: "definicao__texto",
        texto: t("definicao.do-projeto", { adr: definicao.rotulo }),
      }),
      elemento("a", {
        classe: "definicao__link",
        texto: t("definicao.ler-o-adr"),
        atributos: { href: definicao.endereco, target: "_blank", rel: "noopener" },
      }),
    ];
  }
  /** @type {Node[]} */
  const partes = [];
  if (definicao.explicacao) {
    partes.push(elemento("p", { classe: "definicao__texto", texto: definicao.explicacao }));
    if (definicao.explicacaoFonte) {
      partes.push(
        elemento("p", {
          classe: "definicao__fonte",
          texto: t("definicao.fonte-da-explicacao", { fonte: definicao.explicacaoFonte }),
        }),
      );
    }
  }
  partes.push(
    elemento("p", { classe: "definicao__rotulo", texto: t("definicao.oficial") }),
    elemento("p", {
      classe: "definicao__oficial",
      texto: definicao.definicao ?? t("definicao.sem-definicao-oficial"),
    }),
  );
  const confianca = definicao.confianca ? CONFIANCA[definicao.confianca] : undefined;
  partes.push(
    elemento("p", {
      classe: "definicao__fonte",
      texto: [definicao.fonte, confianca ? t(confianca) : null].filter(Boolean).join(" · "),
    }),
  );
  return partes;
}

/**
 * PT: Põe o popover junto do botão, abaixo dele, sem sair da tela.
 * EN: Places the popover below its button, inside the viewport.
 *
 * @param {HTMLElement} botao
 * @param {HTMLElement} caixa
 */
function posicionar(botao, caixa) {
  const alvo = botao.getBoundingClientRect();
  const margem = 8;
  const largura = caixa.offsetWidth;
  const esquerda = Math.min(
    Math.max(margem, alvo.left),
    Math.max(margem, window.innerWidth - largura - margem),
  );
  const abaixo = alvo.bottom + margem;
  const cabe = abaixo + caixa.offsetHeight <= window.innerHeight - margem;
  const topo = cabe ? abaixo : Math.max(margem, alvo.top - caixa.offsetHeight - margem);
  caixa.style.setProperty("left", `${esquerda}px`);
  caixa.style.setProperty("top", `${topo}px`);
}

/**
 * PT: O botão de definição e o popover dele. Os dois vão juntos para a
 *     página, logo depois do rótulo do número.
 * EN: The definition button and its popover, placed right after the label.
 *
 * @param {object} opcoes
 * @param {string} opcoes.rotulo O nome do número, para o botão e o título / the number's name
 * @param {Definicao} opcoes.definicao
 * @returns {HTMLSpanElement}
 */
export function definicao({ rotulo, definicao: origem }) {
  contador += 1;
  const id = `definicao-${contador}`;
  const caixa = elemento(
    "div",
    {
      classe: "definicao__caixa",
      atributos: { id, popover: "auto", role: "dialog", "aria-label": rotulo },
    },
    [elemento("p", { classe: "definicao__titulo", texto: rotulo }), ...conteudo(origem)],
  );
  const botao = elemento(
    "button",
    {
      classe: "definicao__botao",
      atributos: {
        type: "button",
        popovertarget: id,
        "aria-label": t("definicao.o-que-e", { rotulo }),
      },
    },
    [icone("info-circle")],
  );
  caixa.addEventListener("toggle", (evento) => {
    if (/** @type {ToggleEvent} */ (evento).newState === "open") posicionar(botao, caixa);
  });
  return elemento("span", { classe: "definicao" }, [botao, caixa]);
}
