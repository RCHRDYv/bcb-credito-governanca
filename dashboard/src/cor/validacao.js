/**
 * PT: Validação das paletas de gráfico: contraste, luminosidade, croma e
 *     daltonismo, medidos e nunca julgados a olho.
 *
 *     Cada paleta tem um papel, e cada papel tem os seus critérios:
 *     - **categórica,** para identidade (qual série): cores de matizes
 *       diferentes, que precisam ser distintas entre si também para quem
 *       tem daltonismo;
 *     - **sequencial,** para magnitude (quanto): uma matiz só, do claro ao
 *       escuro, com passos visíveis;
 *     - **divergente,** para desvio contra uma referência (para que lado):
 *       dois braços sequenciais de matizes opostas e um meio neutro.
 *
 *     Os limites seguem o método de visualização de dados usado no projeto,
 *     e o contraste segue a WCAG 2.2: 3:1 para elemento gráfico.
 *
 * EN: Chart palette validation. Categorical, sequential and diverging
 *     palettes each have their own measured criteria; contrast follows
 *     WCAG 2.2 (3:1 for graphical objects).
 */

import { razaoDeContraste } from "./contraste.js";
import { diferenca, TIPOS } from "./daltonismo.js";
import { oklch } from "./oklab.js";

/** @typedef {import("./daltonismo.js").TipoDeDaltonismo} TipoDeDaltonismo */
/** @typedef {"claro" | "escuro"} Tema */
/** @typedef {"passa" | "alerta" | "reprova"} Estado */

/**
 * @typedef {object} Criterio
 * @property {string} id Identificador estável, para os testes / stable id
 * @property {string} nome Nome em português, para a tela / display name
 * @property {Estado} estado
 * @property {string} detalhe O número medido e o que ele significa / measured value
 */

/**
 * @typedef {object} Resultado
 * @property {boolean} aprovada Nenhum critério reprovado / no failing criterion
 * @property {Criterio[]} criterios
 */

/**
 * @typedef {object} Opcoes
 * @property {Tema} tema
 * @property {string} superficie Fundo opaco onde o gráfico é desenhado / opaque chart surface
 * @property {"adjacentes" | "todos"} [pares] Pares comparados na categórica / pairs compared
 */

/**
 * PT: Os limites, num lugar só.
 *     - `faixa`: luminosidade OKLCH aceita em cada tema. Fora dela, a cor
 *       fica escura ou clara demais para ser lida como matiz.
 *     - `cromaMinimo`: abaixo disso a cor parece cinza.
 *     - `daltonismo`: distância mínima entre cores vizinhas simuladas. O
 *       alvo é 8; entre 6 e 8 a paleta só vale com rótulo direto ou textura.
 *     - `visaoNormal`: distância mínima sem simulação, para quem enxerga
 *       todas as cores também distinguir as vizinhas.
 *     - `contrasteGrafico`: WCAG 2.2, critério 1.4.11.
 *     - `passoMinimo`, `pontaClara` e `matizUnica`: para as rampas.
 * EN: All thresholds in one place.
 */
export const LIMITES = Object.freeze({
  faixa: { claro: [0.43, 0.77], escuro: [0.48, 0.67] },
  cromaMinimo: 0.1,
  daltonismo: { alvo: 8, piso: 6 },
  visaoNormal: 15,
  contrasteGrafico: 3,
  passoMinimo: 0.06,
  pontaClara: 2,
  matizUnica: 40,
  simetria: 0.06,
  neutroCromaMaximo: 0.02,
});

/** @type {TipoDeDaltonismo[]} */
const TIPOS_QUE_REPROVAM = ["protanopia", "deuteranopia"];

const numero = (/** @type {number} */ valor, casas = 1) =>
  valor.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });

/**
 * PT: Os pares de índices comparados: só vizinhos, para barras e linhas,
 *     ou todos, para mapa e dispersão, em que qualquer cor pode encostar em
 *     qualquer outra.
 * EN: Index pairs compared: neighbors only, or all pairs.
 *
 * @param {number} n
 * @param {"adjacentes" | "todos"} modo
 * @returns {[number, number][]}
 */
function paresDe(n, modo) {
  /** @type {[number, number][]} */
  const pares = [];
  for (let i = 0; i < n; i += 1) {
    for (let j = i + 1; j < n; j += 1) {
      if (modo === "todos" || j === i + 1) pares.push([i, j]);
    }
  }
  return pares;
}

/**
 * @typedef {object} Par
 * @property {number} valor Distância em OKLab x100 / distance
 * @property {string} a
 * @property {string} b
 * @property {TipoDeDaltonismo | "visao-normal"} tipo
 */

/**
 * PT: O par mais próximo entre os pares dados, sob os tipos de visão dados.
 * EN: The closest pair under the given vision types.
 *
 * @param {[string, string][]} pares
 * @param {(TipoDeDaltonismo | undefined)[]} tipos
 * @returns {Par}
 */
function parMaisProximo(pares, tipos) {
  /** @type {Par} */
  let pior = { valor: Number.POSITIVE_INFINITY, a: "", b: "", tipo: "visao-normal" };
  for (const tipo of tipos) {
    for (const [a, b] of pares) {
      const valor = diferenca(a, b, tipo);
      if (valor < pior.valor) pior = { valor, a, b, tipo: tipo ?? "visao-normal" };
    }
  }
  return pior;
}

/**
 * PT: Critério de daltonismo: reprova abaixo do piso, alerta entre o piso
 *     e o alvo. A tritanopia aparece no detalhe, e não reprova, como no
 *     método de origem: é rara e o modelo é menos preciso para ela.
 * EN: CVD criterion; tritanopia is reported, not gating.
 *
 * @param {[string, string][]} pares
 * @returns {Criterio}
 */
function criterioDaltonismo(pares) {
  const pior = parMaisProximo(pares, TIPOS_QUE_REPROVAM);
  const tritan = parMaisProximo(pares, ["tritanopia"]);
  const { alvo, piso } = LIMITES.daltonismo;
  /** @type {Estado} */
  const estado = pior.valor >= alvo ? "passa" : pior.valor >= piso ? "alerta" : "reprova";
  return {
    id: "daltonismo",
    nome: "Distância com daltonismo",
    estado,
    detalhe: `pior par ${pior.a} e ${pior.b}: ${numero(pior.valor)} na ${pior.tipo}; tritanopia ${numero(tritan.valor)}`,
  };
}

/**
 * PT: Critério de contraste de cada cor contra a superfície do gráfico.
 * EN: Contrast of each color against the chart surface.
 *
 * @param {string[]} cores
 * @param {string} superficie
 * @param {number} minimo
 * @param {string} nome
 * @returns {Criterio}
 */
function criterioContraste(cores, superficie, minimo, nome) {
  const razoes = cores.map((cor) => ({ cor, razao: razaoDeContraste(cor, superficie) }));
  const abaixo = razoes.filter(({ razao }) => razao < minimo);
  const menor = razoes.reduce((a, b) => (b.razao < a.razao ? b : a));
  return {
    id: "contraste",
    nome,
    estado: abaixo.length ? "reprova" : "passa",
    detalhe: abaixo.length
      ? `abaixo de ${numero(minimo)}:1: ${abaixo.map(({ cor, razao }) => `${cor} (${numero(razao, 2)}:1)`).join(", ")}`
      : `menor ${menor.cor}, ${numero(menor.razao, 2)}:1`,
  };
}

/**
 * PT: Valida uma paleta categórica.
 * EN: Validates a categorical palette.
 *
 * @param {string[]} cores Na ordem em que as séries recebem as cores / in slot order
 * @param {Opcoes} opcoes
 * @returns {Resultado}
 */
export function validarCategorica(cores, { tema, superficie, pares = "adjacentes" }) {
  const [minimo, maximo] = LIMITES.faixa[tema];
  const medidas = cores.map((cor) => ({ cor, ...oklch(cor) }));
  const foraDaFaixa = medidas.filter(({ L }) => L < minimo || L > maximo);
  const semCroma = medidas.filter(({ C }) => C < LIMITES.cromaMinimo);
  const comparados = paresDe(cores.length, pares).map(
    ([i, j]) => /** @type {[string, string]} */ ([cores[i], cores[j]]),
  );
  const normal = parMaisProximo(comparados, [undefined]);

  /** @type {Criterio[]} */
  const criterios = [
    {
      id: "faixa",
      nome: "Faixa de luminosidade",
      estado: foraDaFaixa.length ? "reprova" : "passa",
      detalhe: foraDaFaixa.length
        ? `fora de ${numero(minimo, 2)} a ${numero(maximo, 2)}: ${foraDaFaixa.map(({ cor, L }) => `${cor} (${numero(L, 3)})`).join(", ")}`
        : `todas entre ${numero(minimo, 2)} e ${numero(maximo, 2)}`,
    },
    {
      id: "croma",
      nome: "Croma mínimo",
      estado: semCroma.length ? "reprova" : "passa",
      detalhe: semCroma.length
        ? `abaixo de ${numero(LIMITES.cromaMinimo, 2)}, parece cinza: ${semCroma.map(({ cor, C }) => `${cor} (${numero(C, 3)})`).join(", ")}`
        : `todas com ${numero(LIMITES.cromaMinimo, 2)} ou mais`,
    },
    criterioDaltonismo(comparados),
    {
      id: "visao-normal",
      nome: "Distância sem daltonismo",
      estado: normal.valor >= LIMITES.visaoNormal ? "passa" : "reprova",
      detalhe: `pior par ${normal.a} e ${normal.b}: ${numero(normal.valor)}`,
    },
    criterioContraste(cores, superficie, LIMITES.contrasteGrafico, "Contraste com o fundo"),
  ];
  return { aprovada: criterios.every(({ estado }) => estado !== "reprova"), criterios };
}

/**
 * PT: Valida uma rampa de uma matiz só, do valor baixo ao alto. A ponta que
 *     encosta no fundo precisa de pelo menos 2:1: a classe é lida também
 *     pela legenda, pela dica e pela tabela, então a rampa pode se aproximar
 *     do fundo, mas não sumir nele.
 * EN: Validates a one-hue ramp, from low to high value.
 *
 * @param {string[]} cores Do valor mais baixo ao mais alto / low to high
 * @param {Opcoes} opcoes
 * @returns {Resultado}
 */
export function validarSequencial(cores, { superficie }) {
  const L = cores.map((cor) => oklch(cor).L);
  const crescente = L.every((valor, i) => i === 0 || valor > L[i - 1]);
  const decrescente = L.every((valor, i) => i === 0 || valor < L[i - 1]);
  const passos = L.slice(1).map((valor, i) => Math.abs(valor - L[i]));
  const menorPasso = Math.min(...passos);
  const ponta = cores[0];
  const contrasteDaPonta = razaoDeContraste(ponta, superficie);
  const matizes = cores.map((cor) => oklch(cor).h);
  let espalhamento = Math.max(...matizes) - Math.min(...matizes);
  if (espalhamento > 180) espalhamento = 360 - espalhamento;

  /** @type {Criterio[]} */
  const criterios = [
    {
      id: "monotonica",
      nome: "Luminosidade em ordem",
      estado: crescente || decrescente ? "passa" : "reprova",
      detalhe: `L: ${L.map((valor) => numero(valor, 3)).join(", ")}`,
    },
    {
      id: "passo",
      nome: "Passo entre degraus",
      estado: menorPasso >= LIMITES.passoMinimo ? "passa" : "reprova",
      detalhe: `menor passo ${numero(menorPasso, 3)}, mínimo ${numero(LIMITES.passoMinimo, 2)}`,
    },
    {
      id: "ponta",
      nome: "Ponta junto ao fundo",
      estado: contrasteDaPonta >= LIMITES.pontaClara ? "passa" : "reprova",
      detalhe: `${ponta}, ${numero(contrasteDaPonta, 2)}:1 contra o fundo`,
    },
    {
      id: "matiz",
      nome: "Uma matiz só",
      estado: espalhamento <= LIMITES.matizUnica ? "passa" : "reprova",
      detalhe: `variação de matiz de ${numero(espalhamento, 0)} graus`,
    },
  ];
  return { aprovada: criterios.every(({ estado }) => estado !== "reprova"), criterios };
}

/**
 * @typedef {object} Divergente
 * @property {string[]} negativo Do meio para a ponta / from the middle outwards
 * @property {string} neutro O meio: sem desvio / the middle
 * @property {string[]} positivo Do meio para a ponta / from the middle outwards
 */

/**
 * PT: Valida uma paleta divergente: cada braço é uma rampa válida, os dois
 *     braços têm o mesmo número de degraus e a mesma luminosidade em cada
 *     degrau, o meio é cinza, e os polos continuam distintos com daltonismo.
 * EN: Validates a diverging palette.
 *
 * @param {Divergente} paleta
 * @param {Opcoes} opcoes
 * @returns {Resultado}
 */
export function validarDivergente({ negativo, neutro, positivo }, opcoes) {
  const bracos = [
    ["negativo", validarSequencial(negativo, opcoes)],
    ["positivo", validarSequencial(positivo, opcoes)],
  ];
  const assimetria = Math.max(
    ...negativo.map((cor, i) => Math.abs(oklch(cor).L - oklch(positivo[i] ?? cor).L)),
  );
  const croma = oklch(neutro).C;
  const polos = negativo.map(
    (cor, i) => /** @type {[string, string]} */ ([cor, positivo[i] ?? cor]),
  );
  const daltonismo = criterioDaltonismo(polos);
  const normal = parMaisProximo(polos, [undefined]);

  /** @type {Criterio[]} */
  const criterios = [
    ...bracos.map(([nome, resultado]) => {
      const falhas = /** @type {Resultado} */ (resultado).criterios.filter(
        ({ estado }) => estado === "reprova",
      );
      return /** @type {Criterio} */ ({
        id: `braco-${nome}`,
        nome: `Braço ${nome} como rampa`,
        estado: falhas.length ? "reprova" : "passa",
        detalhe: falhas.length
          ? falhas.map(({ nome: n, detalhe }) => `${n}: ${detalhe}`).join("; ")
          : "luminosidade em ordem, passos visíveis e uma matiz só",
      });
    }),
    {
      id: "simetria",
      nome: "Braços simétricos",
      estado:
        negativo.length === positivo.length && assimetria <= LIMITES.simetria ? "passa" : "reprova",
      detalhe: `${negativo.length} e ${positivo.length} degraus; maior diferença de luminosidade ${numero(assimetria, 3)}`,
    },
    {
      id: "neutro",
      nome: "Meio neutro",
      estado: croma <= LIMITES.neutroCromaMaximo ? "passa" : "reprova",
      detalhe: `${neutro}, croma ${numero(croma, 3)}`,
    },
    { ...daltonismo, id: "polos-daltonismo", nome: "Polos com daltonismo" },
    {
      id: "polos-visao-normal",
      nome: "Polos sem daltonismo",
      estado: normal.valor >= LIMITES.visaoNormal ? "passa" : "reprova",
      detalhe: `pior degrau ${normal.a} e ${normal.b}: ${numero(normal.valor)}`,
    },
  ];
  return { aprovada: criterios.every(({ estado }) => estado !== "reprova"), criterios };
}

export { TIPOS };
