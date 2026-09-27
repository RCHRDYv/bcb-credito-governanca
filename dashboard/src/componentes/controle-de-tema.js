/**
 * PT: Controle de tema: claro, escuro ou automático, no topo da página.
 *
 *     Decidido em 2026-09-27, na #64, revendo a decisão 3 do ADR 0018:
 *     - **Automático** é o padrão, e segue o sistema do visitante;
 *     - **Claro** e **Escuro** fixam o tema pelo atributo `data-tema`;
 *     - a escolha fica guardada no navegador do visitante;
 *     - a impressão e o PDF saem sempre claros, qualquer que seja a escolha.
 *
 *     Para a página não piscar no tema errado, o `public/tema-inicial.js`
 *     aplica a escolha guardada antes da pintura, com a mesma chave daqui.
 *
 * EN: Theme control (light, dark, automatic). Automatic follows the system
 *     and is the default; the choice is stored in the browser, and printing
 *     is always light. `public/tema-inicial.js` applies it before paint.
 */

import { t } from "../textos/index.js";
import { controleSegmentado } from "./controle-segmentado.js";

/** @typedef {"claro" | "escuro" | "automatico"} EscolhaDeTema */

/** PT: a mesma chave de `public/tema-inicial.js` / EN: same key as the head script */
export const CHAVE_DO_TEMA = "credito-pj:tema";

/**
 * PT: A escolha guardada, ou automático. O armazenamento pode estar
 *     bloqueado, como em janela privada; nesse caso vale o automático.
 * EN: The stored choice, or automatic when storage is unavailable.
 *
 * @returns {EscolhaDeTema}
 */
export function escolhaGuardada() {
  try {
    const guardada = localStorage.getItem(CHAVE_DO_TEMA);
    return guardada === "claro" || guardada === "escuro" ? guardada : "automatico";
  } catch {
    return "automatico";
  }
}

/**
 * PT: Aplica e guarda a escolha. Automático tira o atributo, e o CSS volta
 *     a seguir o sistema.
 * EN: Applies and stores the choice.
 *
 * @param {EscolhaDeTema} escolha
 * @returns {void}
 */
export function aplicarTema(escolha) {
  const raiz = document.documentElement;
  if (escolha === "automatico") delete raiz.dataset.tema;
  else raiz.dataset.tema = escolha;
  try {
    if (escolha === "automatico") localStorage.removeItem(CHAVE_DO_TEMA);
    else localStorage.setItem(CHAVE_DO_TEMA, escolha);
  } catch {
    // PT: sem armazenamento, a escolha vale só nesta visita
    // EN: without storage, the choice lasts this visit only
  }
}

/**
 * PT: Monta o controle, já com a escolha guardada.
 * EN: Builds the control with the stored choice.
 *
 * @returns {HTMLDivElement}
 */
export function controleDeTema() {
  return controleSegmentado({
    rotulo: t("tema.rotulo"),
    opcoes: [
      { valor: "claro", texto: t("tema.claro") },
      { valor: "escuro", texto: t("tema.escuro") },
      { valor: "automatico", texto: t("tema.automatico") },
    ],
    valor: escolhaGuardada(),
    aoMudar: (valor) => aplicarTema(/** @type {EscolhaDeTema} */ (valor)),
  });
}
