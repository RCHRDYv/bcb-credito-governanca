/**
 * PT: Tela 3: para onde a carteira aponta (#72, pergunta Q27).
 *
 *     A projeção de três meses de cada série vem do script da previsão (#27,
 *     #98), que escolhe um campeão por série no backtest. A disposição é a
 *     das Telas 1 e 2, no modelo "Palco em tela única" (ADR 0022), aprovada
 *     no mockup de 2026-10-06 (opção A):
 *     1. **À esquerda, os filtros:** a série (o país, as 13 modalidades e as
 *        27 UFs), o período e a forma de ver, gráfico ou tabela.
 *     2. **À esquerda, embaixo, o que a série mostra:** o último dado, o
 *        método escolhido em termos comuns, a projeção mês a mês com a faixa
 *        provável e como a projeção é feita.
 *     3. **No centro, a série,** com o realizado em linha sólida, a projeção
 *        tracejada e a faixa hachurada (RF-301), ou a tabela, com o CSV.
 *     4. **À direita, o teste:** um dos 4 testes recentes por vez, com o que
 *        a projeção dizia contra o que aconteceu, o erro médio contra o de
 *        repetir o último mês e quantas vezes a faixa acertou (RF-302).
 *     5. **À direita, embaixo, como saber se a projeção é boa,** com as
 *        ressalvas.
 *
 *     Na tela, os termos são os comuns: "tendência", "faixa provável" e
 *     "repetir o último mês". MASE e MAPE ficam no relatório.
 *
 * EN: Screen 3: where the portfolio is heading. Same single-screen stage as
 *     Screens 1 and 2: filters and the series summary on the left; the
 *     series with its projection, or the table, in the centre; one recent
 *     backtest test at a time and the caveats on the right.
 */

import { aviso } from "../../componentes/aviso.js";
import { campoDeSelecao } from "../../componentes/campo-de-selecao.js";
import { controleSegmentado } from "../../componentes/controle-segmentado.js";
import { elemento } from "../../dom.js";
import { Filtros } from "../../estado/filtros.js";
import { dataBase, mesCurto, reais, taxa } from "../../formatos.js";
import { areaDoGrafico, cartaoDeGrafico, erroDoGrafico } from "../../graficos/cartao.js";
import { graficos } from "../../graficos/sob-demanda.js";
import { ufPelaSigla } from "../../graficos/ufs.js";
import { t } from "../../textos/index.js";
import {
  erroRecente,
  janelaDosTestes,
  MUDARAM_DE_NIVEL,
  REPETIR,
  recortar,
  SERIE_INICIAL,
  serieDaProjecao,
  seriesDisponiveis,
  testesDaSerie,
} from "./dados.js";
import { sobreOModelo } from "./modelos.js";
import { botaoDoCsv, reaisCurtos, tabelaDaSerie, tabelaMesAMes } from "./tabela.js";
import "../palco.css";
import "./projecao.css";

/** @typedef {import("./carga.js").DadosDaTela} DadosDaTela */
/** @typedef {import("./dados.js").Periodo} Periodo */
/** @typedef {import("./dados.js").TipoDeRecorte} TipoDeRecorte */
/** @typedef {import("./dados.js").SerieDaProjecao} SerieDaProjecao */
/** @typedef {import("../../textos/index.js").ChaveDeTexto} ChaveDeTexto */
/** @typedef {import("../../graficos/grafico.js").Grafico} Grafico */

/** @typedef {"grafico" | "tabela"} Forma */

/**
 * @typedef {object} ValoresDosFiltros
 * @property {string} serie `tipo:recorte`
 * @property {Periodo} periodo
 * @property {Forma} forma
 * @property {string} teste A data do teste mostrado / shown test date
 */

/** @type {Record<TipoDeRecorte, ChaveDeTexto>} */
const GRUPO = {
  pais: "tela3.grupo-pais",
  modalidade: "tela3.grupo-modalidades",
  uf: "tela3.grupo-ufs",
};

/**
 * PT: Monta a Tela 3 no elemento. Devolve a função que desmonta a tela e
 *     libera os gráficos, para a navegação chamar ao trocar de visão.
 * EN: Builds Screen 3; returns the teardown the router calls.
 *
 * @param {HTMLElement} el
 * @param {DadosDaTela} dados
 * @returns {() => void}
 */
export function render(el, dados) {
  const { projecao, backtest, testes, ontologia } = dados;
  const fonte = t("tela3.fonte");

  const nomear = (/** @type {TipoDeRecorte} */ tipo, /** @type {string} */ recorte) => {
    if (tipo === "pais") return t("tela3.brasil");
    if (tipo === "uf") return ufPelaSigla(recorte).nome;
    return ontologia.conceitos.find((c) => c.codigo === recorte)?.rotulo ?? recorte;
  };
  const opcoes = seriesDisponiveis(projecao, nomear);
  const nomes = new Map(opcoes.map((o) => [o.chave, o.nome]));
  const testesIniciais = testesDaSerie(testes, SERIE_INICIAL);

  /** @type {Filtros<ValoresDosFiltros>} */
  const filtros = new Filtros({
    serie: SERIE_INICIAL,
    periodo: /** @type {Periodo} */ ("12-meses"),
    forma: /** @type {Forma} */ ("grafico"),
    teste: testesIniciais.at(-1)?.data ?? "",
  });

  const serieInteira = () => serieDaProjecao(projecao, filtros.valores.serie);
  const serieNoPeriodo = () => recortar(serieInteira(), filtros.valores.periodo);
  const testesAtuais = () => testesDaSerie(testes, filtros.valores.serie);
  const nomeDaSerie = () => nomes.get(filtros.valores.serie) ?? filtros.valores.serie;
  const ateQuando = () => dataBase(serieInteira().projetados.at(-1)?.mes ?? projecao.data_base);
  const janela = () =>
    t(
      filtros.valores.periodo === "12-meses" ? "tela3.janela-12-meses" : "tela3.janela-desde-2024",
      { ate: ateQuando() },
    );

  // ------------------------------------------------------------ filtros

  const seletor = campoDeSelecao({
    rotulo: t("tela3.filtro-serie"),
    opcoes: opcoes.map((o) => ({ valor: o.chave, texto: o.nome, grupo: t(GRUPO[o.tipo]) })),
    valor: filtros.valores.serie,
    aoMudar: (valor) => filtros.definir({ serie: valor }),
  });
  const controleDoPeriodo = controleSegmentado({
    rotulo: t("tela3.periodo"),
    opcoes: [
      { valor: "12-meses", texto: t("tela3.periodo-12-meses") },
      { valor: "desde-2024", texto: t("tela3.periodo-desde-2024") },
    ],
    valor: filtros.valores.periodo,
    aoMudar: (valor) => filtros.definir({ periodo: /** @type {Periodo} */ (valor) }),
  });
  const controleDaForma = controleSegmentado({
    rotulo: t("tela3.forma"),
    opcoes: [
      { valor: "grafico", texto: t("tela3.grafico") },
      { valor: "tabela", texto: t("tela1.tabela") },
    ],
    valor: filtros.valores.forma,
    aoMudar: (valor) => filtros.definir({ forma: /** @type {Forma} */ (valor) }),
  });
  const barra = elemento("div", { classe: "visao__filtros" }, [
    seletor,
    controleDoPeriodo,
    controleDaForma,
  ]);

  // ------------------------------------------------------------ a série

  const resumoDaSerie = elemento("dl", { classe: "visao__resumo" });
  const mesAMes = elemento("div", { classe: "projecao__bloco" });
  const como = elemento("div", { classe: "projecao__como" });
  const cartaoDaSerie = cartaoDeGrafico(
    {
      titulo: t("tela3.titulo-serie", { serie: nomeDaSerie() }),
      dataBase: janela(),
      fonte,
      nivel: "h2",
    },
    [resumoDaSerie, mesAMes, como],
  );
  const idDoTitulo = /** @type {HTMLElement} */ (
    cartaoDaSerie.querySelector(".cartao-grafico__titulo")
  ).id;

  const desenharSobreASerie = () => {
    const serie = serieInteira();
    const ultimo = serie.meses.length - 1;
    const modelo = sobreOModelo(serie.modelo);
    resumoDaSerie.replaceChildren(
      elemento("dt", { texto: t("tela3.ultimo-dado", { mes: dataBase(serie.meses[ultimo]) }) }),
      elemento("dd", { texto: reaisCurtos(serie.valores[ultimo]) }),
      elemento("dt", { texto: t("tela3.metodo") }),
      elemento("dd", { texto: modelo.nome }),
    );
    mesAMes.replaceChildren(
      elemento("h3", { classe: "projecao__subtitulo", texto: t("tela3.mes-a-mes") }),
      tabelaMesAMes(serie.projetados),
      elemento("p", { classe: "projecao__nota", texto: t("tela3.faixa-explicacao") }),
    );
    como.replaceChildren(
      elemento("h3", { classe: "projecao__subtitulo", texto: t("tela3.como-titulo") }),
      elemento("p", { texto: t("tela3.como-texto") }),
      elemento("p", { texto: modelo.como }),
    );
  };

  // ------------------------------------------------------------ palco

  const formaEl = elemento("div", { classe: "visao__forma" });
  const palco = elemento(
    "div",
    { classe: "visao__palco", atributos: { role: "region", "aria-labelledby": idDoTitulo } },
    [formaEl],
  );
  /** @type {Grafico | null} */
  let graficoDaSerie = null;
  let pedidoDaSerie = 0;

  const desenharPalco = async () => {
    pedidoDaSerie += 1;
    const meu = pedidoDaSerie;
    graficoDaSerie?.destruir();
    graficoDaSerie = null;
    const serie = serieNoPeriodo();
    formaEl.className = `visao__forma visao__forma--${filtros.valores.forma}`;
    if (filtros.valores.forma === "tabela") {
      const legenda = t("tela3.legenda-tabela", { serie: nomeDaSerie() });
      const recorte = filtros.valores.serie.replace(":", "-");
      formaEl.replaceChildren(
        elemento("div", { classe: "visao__acoes" }, [
          botaoDoCsv(serieInteira(), `projecao-carteira-pj-${recorte}-${projecao.data_base}.csv`),
        ]),
        tabelaDaSerie(serie, legenda),
      );
      return;
    }
    const area = areaDoGrafico("grafico--projecao");
    formaEl.replaceChildren(area);
    try {
      const { serieTemporal } = await graficos();
      if (meu !== pedidoDaSerie) return;
      const grafico = await serieTemporal(area, {
        nome: t("tela3.realizado"),
        meses: serie.meses,
        valores: serie.valores,
        formatar: (v) => reais(v, 2),
        projecao: {
          meses: serie.projetados.map((p) => p.mes),
          valor: serie.projetados.map((p) => p.valor),
          inferior: serie.projetados.map((p) => p.inferior),
          superior: serie.projetados.map((p) => p.superior),
          rotulo: t("tela3.projecao"),
          rotuloDaOrigem: t("tela3.ultimo-dado-marco"),
          intervalo: (de, ate) => t("tela3.faixa-na-dica", { de, ate }),
        },
      });
      if (meu !== pedidoDaSerie) {
        grafico.destruir();
        return;
      }
      graficoDaSerie = grafico;
    } catch {
      if (meu === pedidoDaSerie) formaEl.replaceChildren(erroDoGrafico(t("tela2.serie-erro")));
    }
  };

  // ------------------------------------------------------------ teste

  const datasDosTestes = testesIniciais.map((teste) => teste.data);
  const controleDoTeste = controleSegmentado({
    rotulo: t("tela3.data-do-teste"),
    opcoes: datasDosTestes.map((data) => ({ valor: data, texto: mesCurto(data) })),
    valor: filtros.valores.teste,
    aoMudar: (valor) => filtros.definir({ teste: valor }),
  });
  const areaDoTeste = areaDoGrafico("grafico--teste");
  const fraseDoErro = elemento("p", { classe: "projecao__frase" });
  const acertos = elemento("p", { classe: "projecao__nota" });
  // PT: nas cinco séries que mudaram de patamar, a ressalva fica junto do
  //     erro, que ela explica
  // EN: in the five level-change series, the caveat sits next to the error
  const avisoDoNivel = elemento("div", { classe: "visao__vazio" });
  const cartaoDoTeste = cartaoDeGrafico(
    {
      titulo: t("tela3.titulo-teste", { mes: dataBase(filtros.valores.teste) }),
      dataBase: t("tela3.subtitulo-teste"),
      fonte,
      nivel: "h2",
    },
    [controleDoTeste, areaDoTeste, fraseDoErro, acertos, avisoDoNivel],
  );
  cartaoDoTeste.classList.add("projecao__teste");

  const desenharErro = () => {
    const erro = erroRecente(backtest, testesAtuais(), filtros.valores.serie);
    fraseDoErro.textContent =
      erro.modelo === REPETIR
        ? t("tela3.erro-frase-repetir", { erro: taxa(erro.erro, 2) })
        : t("tela3.erro-frase", { erro: taxa(erro.erro, 2), repetir: taxa(erro.erroDeRepetir, 2) });
    acertos.textContent = t("tela3.acertos", {
      n: String(erro.acertos),
      total: String(erro.casos),
    });
    avisoDoNivel.replaceChildren(
      ...(MUDARAM_DE_NIVEL.has(filtros.valores.serie)
        ? [aviso({ tipo: "atencao", texto: t("tela3.aviso-mudanca-de-nivel"), variante: "linha" })]
        : []),
    );
  };

  /** @type {Grafico | null} */
  let graficoDoTeste = null;
  let pedidoDoTeste = 0;

  const desenharTeste = async () => {
    pedidoDoTeste += 1;
    const meu = pedidoDoTeste;
    graficoDoTeste?.destruir();
    graficoDoTeste = null;
    const titulo = cartaoDoTeste.querySelector(".cartao-grafico__titulo");
    if (titulo) {
      titulo.textContent = t("tela3.titulo-teste", { mes: dataBase(filtros.valores.teste) });
    }
    const recentes = testesAtuais();
    const teste = recentes.find((r) => r.data === filtros.valores.teste);
    if (!teste) return;
    const janelaDoTeste = janelaDosTestes(serieInteira(), recentes);
    try {
      const { serieTemporal } = await graficos();
      if (meu !== pedidoDoTeste) return;
      const grafico = await serieTemporal(areaDoTeste, {
        nome: t("tela3.aconteceu"),
        meses: janelaDoTeste.meses,
        valores: janelaDoTeste.valores,
        formatar: (v) => reais(v, 2),
        projecao: {
          meses: teste.projetados.map((p) => p.mes),
          valor: teste.projetados.map((p) => p.valor),
          inferior: teste.projetados.map((p) => p.inferior),
          superior: teste.projetados.map((p) => p.superior),
          rotulo: t("tela3.dizia"),
          origem: teste.data,
          rotuloDaOrigem: t("tela3.marco-do-teste"),
          intervalo: (de, ate) => t("tela3.faixa-na-dica", { de, ate }),
        },
      });
      if (meu !== pedidoDoTeste) {
        grafico.destruir();
        return;
      }
      graficoDoTeste = grafico;
    } catch {
      if (meu === pedidoDoTeste) areaDoTeste.replaceChildren(erroDoGrafico(t("tela2.serie-erro")));
    }
  };

  // ------------------------------------------------------------ qualidade

  const avisos = elemento("div", { classe: "projecao__avisos" });
  const desenharAvisos = () => {
    avisos.replaceChildren(
      aviso({ tipo: "informacao", texto: t("tela3.aviso-poucos-testes"), variante: "linha" }),
      aviso({ tipo: "informacao", texto: t("tela3.aviso-meta"), variante: "linha" }),
      aviso({ tipo: "informacao", texto: t("tela3.aviso-soma"), variante: "linha" }),
    );
  };
  const cartaoDaQualidade = elemento(
    "section",
    {
      classe: "cartao-grafico projecao__qualidade",
      atributos: { tabindex: "0", "aria-label": t("tela3.titulo-qualidade") },
    },
    [
      elemento("header", { classe: "cartao-grafico__cabecalho" }, [
        elemento("h2", { classe: "cartao-grafico__titulo", texto: t("tela3.titulo-qualidade") }),
      ]),
      elemento("div", { classe: "cartao-grafico__corpo" }, [
        elemento("p", { texto: t("tela3.qualidade-texto") }),
        avisos,
      ]),
    ],
  );

  // ------------------------------------------------------------ montagem

  const atualizarCabecalho = () => {
    const titulo = cartaoDaSerie.querySelector(".cartao-grafico__titulo");
    if (titulo) titulo.textContent = t("tela3.titulo-serie", { serie: nomeDaSerie() });
    const origem = cartaoDaSerie.querySelector(".cartao-grafico__origem");
    if (origem) origem.textContent = `${janela()} · ${fonte}`;
  };

  const raiz = elemento("div", { classe: "visao visao--palco visao--projecao" }, [
    elemento("h1", { classe: "visualmente-oculto", texto: t("tela3.titulo") }),
    elemento("div", { classe: "visao__lado visao__lado--esquerdo" }, [
      barra,
      elemento(
        "div",
        {
          classe: "visao__sobre-o-territorio",
          atributos: { tabindex: "0", role: "region", "aria-label": t("tela3.rolagem-da-serie") },
        },
        [cartaoDaSerie],
      ),
    ]),
    palco,
    elemento("div", { classe: "visao__lado visao__lado--direito" }, [
      cartaoDoTeste,
      cartaoDaQualidade,
    ]),
  ]);
  el.replaceChildren(raiz);

  desenharSobreASerie();
  desenharErro();
  desenharAvisos();
  void desenharPalco();
  void desenharTeste();

  const pararDeOuvir = filtros.aoMudar((evento) => {
    const { chaves } = evento.detail;
    if (chaves.includes("serie")) {
      desenharSobreASerie();
      desenharErro();
      desenharAvisos();
      void desenharTeste();
    }
    if (chaves.includes("teste")) void desenharTeste();
    if (chaves.some((c) => c === "serie" || c === "periodo")) atualizarCabecalho();
    if (chaves.some((c) => c === "serie" || c === "periodo" || c === "forma")) {
      void desenharPalco();
    }
  });

  return () => {
    pararDeOuvir();
    pedidoDaSerie += 1;
    pedidoDoTeste += 1;
    graficoDaSerie?.destruir();
    graficoDoTeste?.destruir();
  };
}
