/**
 * PT: O estado dos filtros de uma visão (ADR 0017, decisão 1).
 *
 *     Um objeto simples, com os valores atuais, e um `EventTarget` que avisa
 *     quem escuta sempre que algum valor muda. Não há reatividade automática:
 *     a visão escuta o evento `mudou` e redesenha o que depende do valor que
 *     mudou. O evento traz a lista das chaves alteradas, para cada parte da
 *     tela decidir se precisa reagir.
 *
 * EN: A view's filter state: plain values plus an `EventTarget` that fires
 *     `mudou` with the changed keys whenever a value changes. No automatic
 *     reactivity: the view listens and redraws what depends on it.
 */

/**
 * @template {Record<string, unknown>} V
 * @typedef {CustomEvent<{ chaves: (keyof V)[], valores: Readonly<V> }>} EventoDeMudanca
 */

/**
 * @template {Record<string, unknown>} V
 */
export class Filtros extends EventTarget {
  /** @type {V} */
  #valores;

  /**
   * @param {V} iniciais Os valores com que a visão abre / initial values
   */
  constructor(iniciais) {
    super();
    this.#valores = { ...iniciais };
  }

  /**
   * PT: Uma cópia dos valores atuais, que não muda o estado se for alterada.
   * EN: A copy of the current values.
   *
   * @returns {Readonly<V>}
   */
  get valores() {
    return Object.freeze({ ...this.#valores });
  }

  /**
   * PT: Muda um ou mais valores e avisa, uma vez só, as chaves que mudaram
   *     de fato. Um valor igual ao atual não dispara o aviso.
   * EN: Changes one or more values and fires once with the keys that
   *     actually changed.
   *
   * @param {Partial<V>} mudancas
   * @returns {void}
   */
  definir(mudancas) {
    /** @type {(keyof V)[]} */
    const chaves = [];
    for (const chave of /** @type {(keyof V)[]} */ (Object.keys(mudancas))) {
      const valor = /** @type {V[keyof V]} */ (mudancas[chave]);
      if (!Object.is(this.#valores[chave], valor)) {
        this.#valores[chave] = valor;
        chaves.push(chave);
      }
    }
    if (chaves.length > 0) {
      this.dispatchEvent(new CustomEvent("mudou", { detail: { chaves, valores: this.valores } }));
    }
  }

  /**
   * PT: Escuta as mudanças. Devolve a função que para de escutar.
   * EN: Listens for changes; returns the function that stops listening.
   *
   * @param {(evento: EventoDeMudanca<V>) => void} ouvinte
   * @returns {() => void}
   */
  aoMudar(ouvinte) {
    const funcao = /** @type {EventListener} */ (ouvinte);
    this.addEventListener("mudou", funcao);
    return () => this.removeEventListener("mudou", funcao);
  }
}
