/**
 * PT: Os gráficos chegam depois do texto (#89).
 *
 *     O ECharts é a maior parte do código do site. Se a visão o importasse
 *     direto, nenhum número apareceria antes de ele chegar e rodar, e no
 *     celular isso levava a página para baixo da meta de desempenho do
 *     RNF-02. Com a carga sob demanda, a visão monta os cartões, os números e
 *     as ressalvas assim que os dados chegam, e o ECharts começa a baixar só
 *     depois de esse texto aparecer na tela. Cada gráfico se desenha quando
 *     ele termina de carregar.
 *
 * EN: Charts arrive after the text. Views load ECharts on demand, so their
 *     cards, numbers and caveats render as soon as data arrives, and ECharts
 *     starts downloading only once that text is on screen.
 */

/** @typedef {typeof import("./desenhos.js")} Desenhos */

/** PT: o máximo de espera pelo texto / EN: longest wait for the text */
const LIMITE_DA_ESPERA = 1000;

/**
 * PT: Espera o texto da visão chegar à tela. O navegador avisa a maior
 *     pintura de conteúdo (LCP) quando ela chega à tela, e a espera termina
 *     no primeiro aviso, depois do pedido, de um elemento da área principal,
 *     onde a visão é montada. A barra de topo fica de fora: com a thread
 *     ocupada, ela pode ser pintada só depois do pedido. Sem esse aviso, como
 *     no Safari,
 *     espera dois quadros: o segundo só começa depois de o primeiro ser
 *     pintado. O tempo limite cobre a aba escondida, que não pinta, e a
 *     página em que nada maior aparece.
 * EN: Waits for the view's text to reach the screen: the first
 *     largest-contentful-paint entry after the call for an element inside
 *     <main>, or two frames where that entry is not supported, with a timeout
 *     for hidden tabs.
 *
 * @returns {Promise<void>}
 */
function depoisDoTexto() {
  return new Promise((resolver) => {
    const inicio = performance.now();
    /** @type {PerformanceObserver | null} */
    let vigia = null;
    let feito = false;
    const seguir = () => {
      if (feito) return;
      feito = true;
      vigia?.disconnect();
      clearTimeout(limite);
      resolver();
    };
    const limite = setTimeout(seguir, LIMITE_DA_ESPERA);
    if (PerformanceObserver.supportedEntryTypes?.includes("largest-contentful-paint")) {
      vigia = new PerformanceObserver((lista) => {
        const daVisao = /** @type {LargestContentfulPaint[]} */ (lista.getEntries()).some(
          (entrada) => entrada.startTime >= inicio && entrada.element?.closest("main"),
        );
        if (daVisao) seguir();
      });
      vigia.observe({ type: "largest-contentful-paint", buffered: true });
    } else {
      requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(seguir, 0)));
    }
  });
}

/** @type {Promise<Desenhos> | null} */
let carga = null;

/**
 * PT: Os gráficos do ECharts. O primeiro pedido espera o texto da visão
 *     chegar à tela e busca o módulo; os seguintes recebem o mesmo módulo.
 * EN: The ECharts charts. The first call waits for the view's text to reach
 *     the screen and loads the module; later calls get the same module.
 *
 * @returns {Promise<Desenhos>}
 */
export function graficos() {
  carga ??= depoisDoTexto().then(() => import("./desenhos.js"));
  return carga;
}
