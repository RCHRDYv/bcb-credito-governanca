/**
 * PT: Utilitário para montar HTML sem `innerHTML`.
 *
 *     Todo texto entra por `textContent`, então nenhum texto vira HTML por
 *     acidente. As páginas e, depois, os componentes (#64) montam o DOM por
 *     aqui.
 *
 * EN: Builds DOM without `innerHTML`. Text always goes through `textContent`,
 *     so no text ever becomes HTML by accident.
 */

/**
 * @typedef {object} Opcoes
 * @property {string} [classe] Classes CSS, separadas por espaço / CSS classes
 * @property {string} [texto] Texto do elemento / element text
 * @property {Record<string, string>} [atributos] Atributos HTML / HTML attributes
 */

/**
 * PT: Cria um elemento com classe, texto, atributos e filhos.
 * EN: Creates an element with class, text, attributes and children.
 *
 * @template {keyof HTMLElementTagNameMap} Tag
 * @param {Tag} tag
 * @param {Opcoes} [opcoes]
 * @param {(Node | string)[]} [filhos]
 * @returns {HTMLElementTagNameMap[Tag]}
 */
export function elemento(tag, opcoes = {}, filhos = []) {
  const el = document.createElement(tag);
  if (opcoes.classe) {
    el.className = opcoes.classe;
  }
  if (opcoes.texto !== undefined) {
    el.textContent = opcoes.texto;
  }
  for (const [nome, valor] of Object.entries(opcoes.atributos ?? {})) {
    el.setAttribute(nome, valor);
  }
  el.append(...filhos);
  return el;
}
