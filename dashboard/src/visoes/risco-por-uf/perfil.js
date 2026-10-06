/**
 * PT: O perfil de uma UF, no painel de detalhe da Tela 2 (#70).
 *
 *     Responde o que a pessoa pergunta ao escolher uma UF: em que quadrante
 *     ela está, quanto a inadimplência subiu, contra quanto subiu no país,
 *     quanto isso pesa em reais e se o ativo problemático já avisa uma piora
 *     que o atraso ainda não mostra. Embaixo, a série mensal das duas taxas,
 *     que a tela desenha quando o arquivo dela chega. Cada número tem a
 *     definição a um clique (RF-G07).
 *
 * EN: A state's profile in Screen 2's detail panel: quadrant, the change
 *     against the country, the risk cost, the early warning and, below, the
 *     monthly series of both rates, drawn when its file arrives.
 */

import { alertaAntecipado } from "../../componentes/alerta-antecipado.js";
import { etiquetaDeQuadrante } from "../../componentes/etiqueta-de-quadrante.js";
import { elemento } from "../../dom.js";
import { numero, pontos, reais, taxa } from "../../formatos.js";
import { areaDoGrafico, erroDoGrafico } from "../../graficos/cartao.js";
import { t } from "../../textos/index.js";

/** @typedef {import("./dados.js").LinhaDoRisco} LinhaDoRisco */
/** @typedef {import("../../componentes/painel-de-detalhe.js").ConteudoDoDetalhe} ConteudoDoDetalhe */
/** @typedef {import("../../componentes/painel-de-detalhe.js").ItemDoDetalhe} ItemDoDetalhe */

/**
 * @typedef {object} OpcoesDoPerfil
 * @property {LinhaDoRisco} linha A UF escolhida / chosen state
 * @property {string} subtitulo A modalidade e a data-base / modality and date
 * @property {number} meses A janela da tendência / trend window
 * @property {string} nota A ressalva do pé do painel, vazia para a UF comparada / footer caveat
 * @property {(rotulo: string, coluna: string) => Node | undefined} comDefinicao
 */

/**
 * @typedef {object} PerfilDaUf
 * @property {ConteudoDoDetalhe} conteudo
 * @property {HTMLElement} serie Onde a tela desenha a série / where the series goes
 */

/**
 * PT: As etiquetas da UF: o quadrante e, quando há, o alerta antecipado, com
 *     a frase que diz quanto a distância até o ativo problemático abriu.
 * EN: The state's tags: quadrant and, if any, the early warning with its
 *     sentence.
 *
 * @param {LinhaDoRisco} linha
 * @param {number} meses
 * @returns {HTMLElement[]}
 */
function etiquetas(linha, meses) {
  const lista = elemento("p", { classe: "risco__etiquetas" }, [
    ...(linha.quadrante ? [etiquetaDeQuadrante(linha.quadrante)] : []),
    ...(linha.alerta ? [alertaAntecipado()] : []),
  ]);
  const explicacao =
    linha.alerta && linha.aberturaContraOPais !== null
      ? [
          elemento("p", {
            classe: "risco__alerta",
            texto: t("tela2.alerta-texto", {
              valor: `${numero(Math.abs(linha.aberturaContraOPais) * 100, 2)} p.p.`,
              meses: String(meses),
            }),
          }),
        ]
      : [];
  return linha.quadrante || linha.alerta ? [lista, ...explicacao] : [];
}

/**
 * PT: Monta o conteúdo do painel e a área da série.
 * EN: Builds the panel content and the series area.
 *
 * @param {OpcoesDoPerfil} opcoes
 * @returns {PerfilDaUf}
 */
export function perfilDaUf({ linha, subtitulo, meses, nota, comDefinicao }) {
  const m = { meses: String(meses) };
  /** @type {ItemDoDetalhe[]} */
  const itens = [];
  if (linha.taxa !== null) {
    itens.push({
      chave: t("tela2.taxa-da-uf"),
      valor: taxa(linha.taxa, 1),
      apoio: comDefinicao(t("tela2.taxa-da-uf"), "taxa_inadimplencia"),
    });
  }
  if (linha.variacao !== null) {
    itens.push({
      chave: t("tela2.variacao-da-uf", m),
      valor: pontos(linha.variacao),
      apoio: comDefinicao(t("tela2.variacao-da-uf", m), "variacao_taxa_inadimplencia"),
    });
  }
  if (linha.variacaoPais !== null) {
    itens.push({
      chave: t("tela2.variacao-do-pais"),
      valor: pontos(linha.variacaoPais),
      apoio: comDefinicao(t("tela2.variacao-do-pais"), "variacao_taxa_pais"),
    });
  }
  if (linha.custoDoRisco !== null) {
    itens.push({
      chave: t("tela2.custo-do-risco"),
      valor: reais(linha.custoDoRisco),
      apoio: comDefinicao(t("tela2.custo-do-risco"), "custo_do_risco"),
    });
  }

  const serie = elemento("div", { classe: "risco__serie" }, [
    elemento("h3", { classe: "risco__serie-titulo", texto: t("tela2.titulo-serie") }),
    elemento("p", { classe: "risco__serie-estado", texto: t("tela2.serie-carregando") }),
  ]);

  return {
    conteudo: {
      titulo: linha.nome,
      subtitulo,
      itens,
      complemento: elemento("div", { classe: "risco" }, [...etiquetas(linha, meses), serie]),
      ...(nota ? { nota } : {}),
    },
    serie,
  };
}

/**
 * PT: Troca o texto de carregando da série pelo gráfico, ou pelo erro.
 * EN: Replaces the series loading text with the chart area, or the error.
 *
 * @param {HTMLElement} serie
 * @param {"pronta" | "erro"} estado
 * @returns {HTMLElement | null} A área do gráfico, quando pronta / chart area when ready
 */
export function prepararSerie(serie, estado) {
  const aviso = serie.querySelector(".risco__serie-estado");
  if (estado === "erro") {
    aviso?.replaceWith(erroDoGrafico(t("tela2.serie-erro")));
    return null;
  }
  const area = areaDoGrafico("grafico--linhas");
  aviso?.replaceWith(area);
  return area;
}
