/**
 * PT: Etiqueta de alerta antecipado: cápsula em amarelo 10, com o texto em
 *     amarelo 80 e o ícone de sino (ADR 0014, decisão 6).
 *
 *     Marca a célula em que a distância entre ativo problemático e carteira
 *     inadimplida abriu mais que a do país: a piora que o atraso ainda não
 *     mostra. Não muda o quadrante. O amarelo de atenção não é usado para
 *     mais nada na mesma tela.
 *
 * EN: Early-warning tag: yellow 10 capsule with yellow 80 text and a bell.
 */

import { elemento } from "../dom.js";
import { t } from "../textos/index.js";
import { icone } from "./icones.js";

/**
 * PT: Monta a etiqueta.
 * EN: Builds the tag.
 *
 * @returns {HTMLSpanElement}
 */
export function alertaAntecipado() {
  return elemento("span", { classe: "etiqueta etiqueta--alerta" }, [
    icone("bell-ringing"),
    elemento("span", { texto: t("alerta-antecipado.nome") }),
  ]);
}
