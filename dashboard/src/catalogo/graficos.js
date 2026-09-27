/**
 * PT: As seções de gráfico do catálogo: as paletas e os componentes.
 *
 *     As paletas mostram cada cor nos dois temas e a mesma faixa vista por
 *     quem tem daltonismo. Os componentes aparecem com dado real do projeto,
 *     de `exemplos.json`, que o `scripts/gerar_exemplos_do_catalogo.py` gera
 *     a partir dos marts: nenhum número desta página é digitado à mão.
 *
 *     Os gráficos só podem ser desenhados com o elemento já na página,
 *     porque o tema de cada um vem do `color-scheme` do lugar onde ele está.
 *     Por isso a seção devolve o elemento e uma função que desenha depois.
 *
 * EN: Catalog chart sections: palettes (with color vision deficiency
 *     simulation) and chart components with real project data. Charts are
 *     drawn after the section is on the page, since each chart's theme comes
 *     from where it sits.
 */

import { simular, TIPOS } from "../cor/daltonismo.js";
import { elemento } from "../dom.js";
import { dataBase, numero, reais, taxa } from "../formatos.js";
import { areaDoGrafico, cartaoDeGrafico, erroDoGrafico } from "../graficos/cartao.js";
import { cartograma } from "../graficos/cartograma.js";
import { classesDivergentes, classesSequenciais } from "../graficos/escalas.js";
import { temaDoElemento } from "../graficos/grafico.js";
import { carregarMalha, mapaPorUf } from "../graficos/mapa-por-uf.js";
import { matriz } from "../graficos/matriz.js";
import { numeroDeDestaque } from "../graficos/numero-de-destaque.js";
import { ranking } from "../graficos/ranking.js";
import { serieTemporal } from "../graficos/serie-temporal.js";
import { paletas } from "../graficos/tema.js";
import { ufPelaSigla } from "../graficos/ufs.js";
import { t } from "../textos/index.js";
import exemplos from "./exemplos.json" with { type: "json" };
import { comEstilo, ladoALado, secao } from "./secoes.js";

/** @typedef {import("../tokens.js").Tema} Tema */
/** @typedef {import("../textos/index.js").ChaveDeTexto} ChaveDeTexto */

const ENDERECO_DA_MALHA = "./geo/ufs.json";

/** @type {Record<import("../cor/daltonismo.js").TipoDeDaltonismo, ChaveDeTexto>} */
const NOME_DO_TIPO = {
  protanopia: "catalogo.protanopia",
  deuteranopia: "catalogo.deuteranopia",
  tritanopia: "catalogo.tritanopia",
};

// -----------------------------------------------------------------------------
// PT: Paletas
// EN: Palettes
// -----------------------------------------------------------------------------

/**
 * PT: Uma linha de amostras, com o nome da visão ao lado.
 * EN: A row of swatches, labeled by vision type.
 *
 * @param {string} rotulo
 * @param {string[]} cores
 * @returns {HTMLElement}
 */
function faixa(rotulo, cores) {
  return elemento("div", { classe: "faixa" }, [
    elemento("span", { classe: "faixa__rotulo", texto: rotulo }),
    elemento(
      "span",
      { classe: "faixa__cores" },
      cores.map((cor) =>
        comEstilo(elemento("span", { classe: "faixa__cor", atributos: { title: cor } }), {
          "background-color": cor,
        }),
      ),
    ),
  ]);
}

/**
 * PT: Uma paleta: a faixa sem daltonismo e as três simuladas.
 * EN: One palette: the plain row and the three simulated ones.
 *
 * @param {ChaveDeTexto} nome
 * @param {string[]} cores
 * @returns {HTMLElement}
 */
function paleta(nome, cores) {
  return elemento("div", { classe: "paleta-de-grafico" }, [
    elemento("h4", { classe: "paleta-de-grafico__nome", texto: t(nome) }),
    faixa(t("catalogo.sem-daltonismo"), cores),
    ...TIPOS.map((tipo) =>
      faixa(
        t(NOME_DO_TIPO[tipo]),
        cores.map((cor) => simular(cor, tipo)),
      ),
    ),
  ]);
}

/**
 * PT: Seção das paletas de gráfico, nos dois temas.
 * EN: Chart palettes section, in both themes.
 *
 * @returns {HTMLElement}
 */
export function secaoPaletasDeGrafico() {
  return secao(
    "paletas-de-grafico",
    "catalogo.paletas-de-grafico",
    "catalogo.paletas-de-grafico-explicacao",
    [
      ladoALado((tema) => {
        const { categorica, sequencial, divergente, outros } = paletas(tema);
        return [
          paleta("catalogo.paleta-categorica", [...categorica, outros]),
          paleta("catalogo.paleta-sequencial", sequencial),
          paleta("catalogo.paleta-divergente", [
            ...[...divergente.negativo].reverse(),
            divergente.neutro,
            ...divergente.positivo,
          ]),
        ];
      }),
    ],
  );
}

// -----------------------------------------------------------------------------
// PT: Componentes
// EN: Components
// -----------------------------------------------------------------------------

// PT: os cartões ficam dentro dos painéis de tema, que têm título h3 / EN: cards sit under the h3 panel label
const origem = {
  dataBase: dataBase(exemplos.data_base),
  fonte: t("catalogo.fonte-dos-exemplos"),
  nivel: /** @type {const} */ ("h4"),
};
const porUf = exemplos.por_uf;
const carteiraPorEmpresa = Object.fromEntries(
  porUf.uf.map((sigla, i) => [sigla, porUf.carteira_por_empresa[i]]),
);
const desvioEmPontos = Object.fromEntries(
  porUf.uf.map((sigla, i) => [sigla, porUf.desvio_do_risco[i] * 100]),
);
const classesDaCarteira = classesSequenciais(Object.values(carteiraPorEmpresa), (v) => reais(v));
const classesDoDesvio = classesDivergentes([0.1, 0.5, 1], (v) => `${numero(v, 1)} p.p.`, {
  acima: t("grafico.acima-do-pais"),
  abaixo: t("grafico.abaixo-do-pais"),
  igual: t("grafico.igual-ao-pais"),
});
const pontosPercentuais = (/** @type {number} */ v) =>
  `${v > 0 ? "+" : v < 0 ? "−" : ""}${numero(Math.abs(v), 2)} p.p.`;

/**
 * PT: A projeção ilustrativa da série: repete o último mês, com um
 *     intervalo de dois desvios das variações mensais, que cresce com a
 *     raiz do horizonte. Serve só para mostrar a notação até a #27.
 * EN: The illustrative projection: last value carried forward, with a
 *     two-standard-deviation band of monthly changes growing with sqrt(h).
 *
 * @param {string[]} meses
 * @param {number[]} valores
 * @returns {import("../graficos/serie-temporal.js").Projecao}
 */
function projecaoIlustrativa(meses, valores) {
  const variacoes = valores.slice(1).map((v, i) => v - valores[i]);
  const media = variacoes.reduce((a, b) => a + b, 0) / variacoes.length;
  const desvio = Math.sqrt(
    variacoes.reduce((a, b) => a + (b - media) ** 2, 0) / (variacoes.length - 1),
  );
  const ultimo = valores.at(-1) ?? 0;
  const [ano, mes] = (meses.at(-1) ?? "").split("-").map(Number);
  const futuros = [1, 2, 3].map((h) => {
    const data = new Date(Date.UTC(ano, mes + h, 0));
    return data.toISOString().slice(0, 10);
  });
  return {
    meses: futuros,
    valor: futuros.map(() => ultimo),
    inferior: futuros.map((_, i) => ultimo - 2 * desvio * Math.sqrt(i + 1)),
    superior: futuros.map((_, i) => ultimo + 2 * desvio * Math.sqrt(i + 1)),
    rotulo: t("catalogo.projecao-ilustrativa"),
  };
}

/**
 * @typedef {object} Peca
 * @property {HTMLElement} elemento O cartão, para ir na página / the card
 * @property {() => Promise<unknown>} desenhar Desenha o gráfico / draws it
 */

/**
 * PT: As peças de um tema, na ordem em que aparecem.
 * EN: One theme's pieces, in display order.
 *
 * @param {Promise<boolean>} malhaCarregada
 * @returns {Peca[]}
 */
function pecas(malhaCarregada) {
  const mapaEl = areaDoGrafico("grafico--mapa");
  const mapaCartao = cartaoDeGrafico({ titulo: t("catalogo.exemplo-mapa"), ...origem }, [mapaEl]);

  const cartogramaEl = areaDoGrafico("grafico--cartograma");
  const divergenteEl = areaDoGrafico("grafico--cartograma");
  const matrizEl = elemento("div");
  const serieEl = areaDoGrafico("grafico--serie");
  const rankingEl = areaDoGrafico("grafico--ranking");

  const taxaDoPais = exemplos.taxa_do_pais;
  const dezMaiores = porUf.uf
    .map((sigla, i) => ({ rotulo: ufPelaSigla(sigla).nome, valor: porUf.carteira_por_empresa[i] }))
    .sort((a, b) => b.valor - a.valor)
    .slice(0, 10);

  return [
    {
      elemento: mapaCartao,
      desenhar: async () => {
        if (await malhaCarregada) {
          return mapaPorUf(mapaEl, {
            valores: carteiraPorEmpresa,
            classes: classesDaCarteira,
            formatar: (v) => reais(v),
          });
        }
        mapaEl.replaceWith(erroDoGrafico(t("grafico.erro-da-malha")));
        return undefined;
      },
    },
    {
      elemento: elemento("div", { classe: "cartograma" }, [
        cartaoDeGrafico({ titulo: t("catalogo.exemplo-mapa"), ...origem }, [cartogramaEl]),
        elemento("p", { classe: "catalogo__nota", texto: t("catalogo.nota-do-cartograma") }),
      ]),
      desenhar: () =>
        cartograma(cartogramaEl, {
          valores: carteiraPorEmpresa,
          classes: classesDaCarteira,
          formatar: (v) => reais(v),
        }),
    },
    {
      elemento: elemento("div", { classe: "cartograma" }, [
        cartaoDeGrafico(
          {
            titulo: t("catalogo.exemplo-cartograma-divergente"),
            dataBase: `jan/2026 a ${origem.dataBase}`,
            fonte: origem.fonte,
            nivel: origem.nivel,
          },
          [divergenteEl],
        ),
      ]),
      desenhar: () =>
        cartograma(divergenteEl, {
          valores: desvioEmPontos,
          classes: classesDoDesvio,
          formatar: pontosPercentuais,
        }),
    },
    {
      elemento: cartaoDeGrafico(
        {
          ...origem,
          titulo: t("catalogo.exemplo-matriz"),
          dataBase: `jan/2026 a ${origem.dataBase}`,
        },
        [matrizEl],
      ),
      desenhar: () => matriz(matrizEl, { celulas: exemplos.matriz.celulas }),
    },
    {
      elemento: elemento("div", {}, [
        cartaoDeGrafico(
          {
            titulo: t("catalogo.exemplo-serie"),
            dataBase: `${dataBase(taxaDoPais.meses[0])} a ${origem.dataBase}`,
            fonte: origem.fonte,
            nivel: origem.nivel,
          },
          [serieEl],
        ),
        elemento("p", { classe: "catalogo__nota", texto: t("catalogo.nota-da-projecao") }),
      ]),
      desenhar: () =>
        serieTemporal(serieEl, {
          nome: t("catalogo.exemplo-serie"),
          meses: taxaDoPais.meses,
          valores: taxaDoPais.taxa,
          formatar: (v) => taxa(v),
          projecao: projecaoIlustrativa(taxaDoPais.meses, taxaDoPais.taxa),
        }),
    },
    {
      elemento: cartaoDeGrafico({ titulo: t("catalogo.exemplo-ranking"), ...origem }, [rankingEl]),
      desenhar: () =>
        ranking(rankingEl, {
          itens: dezMaiores,
          formatar: (v) => reais(v),
          referencia: {
            valor: porUf.mediana_carteira_por_empresa,
            rotulo: t("catalogo.mediana-das-ufs"),
          },
        }),
    },
    {
      elemento: cartaoDeGrafico({ titulo: t("catalogo.exemplo-destaque"), ...origem }, [
        numeroDeDestaque({
          valor: reais(exemplos.destaque.carteira_ativa),
          rotulo: t("catalogo.exemplo-destaque-rotulo", {
            celulas: String(exemplos.destaque.celulas),
          }),
        }),
      ]),
      desenhar: async () => undefined,
    },
  ];
}

/**
 * PT: Seção dos componentes de gráfico, nos dois temas, mais a
 *     demonstração da troca de tema no mesmo gráfico.
 * EN: Chart components section in both themes, plus the theme-switch demo.
 *
 * @returns {{ elemento: HTMLElement, desenhar: () => Promise<void> }}
 */
export function secaoGraficos() {
  const malhaCarregada = carregarMalha(ENDERECO_DA_MALHA).then(
    () => true,
    () => false,
  );

  /** @type {Peca[]} */
  const todas = [];
  const paineis = ladoALado(() => {
    const doTema = pecas(malhaCarregada);
    todas.push(...doTema);
    return [
      elemento(
        "div",
        { classe: "graficos" },
        doTema.map((peca) => peca.elemento),
      ),
    ];
  });

  const demonstracaoEl = areaDoGrafico("grafico--serie");
  const botao = elemento("button", {
    classe: "botao-de-tema",
    texto: t("catalogo.trocar-tema"),
    atributos: { type: "button", "data-teste": "trocar-tema" },
  });
  botao.addEventListener("click", () => {
    const atual = temaDoElemento(document.documentElement);
    document.documentElement.dataset.tema = atual === "escuro" ? "claro" : "escuro";
  });
  const demonstracao = elemento("div", { classe: "demonstracao-de-tema" }, [
    elemento("h3", { texto: t("catalogo.troca-de-tema") }),
    elemento("p", { classe: "secao__explicacao", texto: t("catalogo.troca-de-tema-explicacao") }),
    botao,
    cartaoDeGrafico(
      {
        titulo: t("catalogo.exemplo-serie"),
        dataBase: `${dataBase(exemplos.taxa_do_pais.meses[0])} a ${origem.dataBase}`,
        fonte: origem.fonte,
        nivel: "h4",
      },
      [demonstracaoEl],
    ),
  ]);
  demonstracaoEl.dataset.teste = "grafico-da-demonstracao";

  const elementoDaSecao = secao("graficos", "catalogo.graficos", "catalogo.graficos-explicacao", [
    paineis,
    demonstracao,
  ]);

  return {
    elemento: elementoDaSecao,
    desenhar: async () => {
      await Promise.all([
        ...todas.map((peca) => peca.desenhar()),
        serieTemporal(demonstracaoEl, {
          nome: t("catalogo.exemplo-serie"),
          meses: exemplos.taxa_do_pais.meses,
          valores: exemplos.taxa_do_pais.taxa,
          formatar: (v) => taxa(v),
        }),
      ]);
    },
  };
}
