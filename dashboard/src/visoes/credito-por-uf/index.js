/**
 * PT: Tela 1: onde está o crédito PJ, e onde ele é escasso por empresa
 *     (#69, pergunta Q14).
 *
 *     A disposição saiu das revisões de 2026-10-01 e 2026-10-05. No
 *     computador, é o mapa em tela cheia (opção C da revisão de 2026-10-05):
 *     o território ocupa o centro, na altura toda, e os painéis ficam dos
 *     lados, sem rolagem da página (ADR 0022).
 *     1. **À esquerda, os filtros:** a modalidade e a forma de ver o
 *        território.
 *     2. **À esquerda, embaixo, o que o território mostra:** o título, a
 *        fonte, o resumo do recorte e as ressalvas (RF-104).
 *     3. **No centro, o território,** em quatro formas: o mapa ou a grade
 *        pela distância até a mediana, a matriz dessa distância em cada UF e
 *        modalidade, e a tabela com os mesmos números (RF-G06), com o
 *        download em CSV. A legenda em escala fica logo abaixo do desenho.
 *     4. **À direita, a oportunidade:** um número de destaque, o crédito que
 *        faltaria para as UFs abaixo da mediana chegarem a ela, com a
 *        ressalva da demanda numa linha (RF-G08).
 *     5. **À direita, embaixo, o ranking** do crédito que faltaria, UF por
 *        UF. Com uma UF escolhida, o painel com o perfil dela toma o lugar
 *        do ranking, e fechar o painel traz o ranking de volta.
 *     A matriz e a tabela pedem largura e ocupam também a coluna da direita,
 *     que volta só com o painel da UF quando uma UF é escolhida.
 *
 *     O estado mora num `Filtros` (ADR 0017): a modalidade, a UF escolhida e
 *     a forma do território. Cada parte escuta as mudanças e se atualiza sem
 *     recriar os gráficos, a não ser na troca de forma, que troca o gráfico.
 *
 * EN: Screen 1. On desktop, a full-screen map (ADR 0022): the territory
 *     (map, tile grid, heatmap or table) fills the centre; filters and the
 *     territory's title, summary and legend sit on the left; the opportunity
 *     number and the gap ranking on the right, where the chosen state's
 *     profile takes the ranking's place.
 */

import { aviso } from "../../componentes/aviso.js";
import { campoDeSelecao } from "../../componentes/campo-de-selecao.js";
import { controleSegmentado } from "../../componentes/controle-segmentado.js";
import { definicao } from "../../componentes/definicao.js";
import { vazio } from "../../componentes/estados.js";
import { painelDeDetalhe } from "../../componentes/painel-de-detalhe.js";
import { definicaoDaColuna, definicaoDaModalidade } from "../../dados/definicoes.js";
import { elemento } from "../../dom.js";
import { Filtros } from "../../estado/filtros.js";
import { dataBase, numero, reais } from "../../formatos.js";
import { areaDoGrafico, cartaoDeGrafico } from "../../graficos/cartao.js";
import { numeroDeDestaque } from "../../graficos/numero-de-destaque.js";
import { graficos } from "../../graficos/sob-demanda.js";
import { ufPelaSigla } from "../../graficos/ufs.js";
import { t } from "../../textos/index.js";
import { classesDeEspaco, distancia, legendaDeEspaco, posicao } from "./cor.js";
import {
  celulasDaMatriz,
  linhas,
  modalidades,
  oportunidade,
  resumo,
  TODAS,
  ufsPorCarteira,
} from "./dados.js";
import { perfilDaUf } from "./perfil.js";
import { botaoDoCsv, tabelaDaTela } from "./tabela.js";
import "../palco.css";
import "./credito-por-uf.css";

/** @typedef {import("./dados.js").LinhaDaVisao} LinhaDaVisao */
/** @typedef {import("./carga.js").DadosDaTela} DadosDaTela */
/** @typedef {import("../../textos/index.js").ChaveDeTexto} ChaveDeTexto */
/** @typedef {import("../../componentes/painel-de-detalhe.js").ItemDoDetalhe} ItemDoDetalhe */

/** @typedef {"mapa" | "grade" | "matriz" | "tabela"} Forma */

/**
 * @typedef {object} ValoresDosFiltros
 * @property {string} modalidade `TODAS` ou o código / or a modality code
 * @property {string | null} uf A UF escolhida / chosen state
 * @property {Forma} desenho A forma de ver o território / territory form
 */

/**
 * PT: O que o território desenhou, com o jeito de se atualizar e de sair.
 * EN: What the territory drew, with how it updates and leaves.
 *
 * @typedef {object} FormaDesenhada
 * @property {(chaves: string[]) => void} atualizar
 * @property {() => void} destruir
 */

/**
 * PT: Abaixo desta largura, a grade é o padrão, porque no mapa o DF, Sergipe
 *     e os estados pequenos do Nordeste quase somem (decidido em 2026-10-01).
 *     É o primeiro ponto de quebra do Carbon, o `md`. Nela, a matriz fica de
 *     pé, com as UFs nas linhas.
 * EN: Below this width the tile grid is the default, and the heatmap stands
 *     upright, with states as rows.
 */
const TELA_ESTREITA = "(max-width: 671px)";

/**
 * PT: As formas que pedem largura. Na tela única, elas ocupam também a
 *     coluna da direita, e a oportunidade e o ranking saem de cena; com uma
 *     UF escolhida, a coluna volta, só com o painel da UF. O mapa em tela
 *     cheia vale para o mapa e a grade (revisão de 2026-10-05).
 * EN: Forms that need width take the right column too on the single screen;
 *     with a chosen state, the column returns with the state panel only.
 */
const FORMAS_LARGAS = new Set(["matriz", "tabela"]);

/** @type {Record<Exclude<LinhaDaVisao["situacao"], "comparada">, ChaveDeTexto>} */
const MOTIVO = {
  "abaixo-do-corte": "tela1.motivo-abaixo-do-corte",
  "poucas-ufs": "tela1.motivo-poucas-ufs",
  "sem-carteira": "tela1.motivo-sem-carteira",
};

/**
 * PT: Uma área de rolagem com nome, que recebe foco para quem usa o teclado.
 * EN: A named scroll area, focusable for keyboard users.
 *
 * @param {HTMLElement} el
 * @param {string} classe
 * @param {string} rotulo
 */
function comRolagem(el, classe, rotulo) {
  el.classList.add(classe);
  el.setAttribute("tabindex", "0");
  el.setAttribute("role", "region");
  el.setAttribute("aria-label", rotulo);
}

/**
 * PT: Monta a Tela 1 no elemento. Devolve a função que desmonta a tela e
 *     libera os gráficos, para a navegação chamar ao trocar de visão.
 * EN: Builds Screen 1; returns the teardown the router calls.
 *
 * @param {HTMLElement} el
 * @param {DadosDaTela} dados
 * @returns {() => void}
 */
export function render(el, dados) {
  const estreita = window.matchMedia(TELA_ESTREITA);
  /** @type {Filtros<ValoresDosFiltros>} */
  const filtros = new Filtros({
    modalidade: TODAS,
    uf: /** @type {string | null} */ (null),
    desenho: /** @type {Forma} */ (estreita.matches || !dados.malha ? "grade" : "mapa"),
  });
  const data = dataBase(dados.porUf.data_base);
  const todasAsModalidades = modalidades(dados.decisao);
  const nomes = new Map(todasAsModalidades.map((m) => [m.codigo, m.nome]));
  const classes = classesDeEspaco();
  const fonte = t("tela1.fonte");
  const corte = reais(dados.corte, 0);

  const todas = () => filtros.valores.modalidade === TODAS;
  const recorte = () =>
    todas()
      ? t("tela1.todas-as-modalidades")
      : (nomes.get(filtros.valores.modalidade) ?? filtros.valores.modalidade);
  const recorteNoTitulo = () => (todas() ? t("tela1.todas-no-titulo") : recorte());
  const arquivo = () => (todas() ? "carteira_por_uf.json" : "decisao.json");
  const linhasAtuais = () => linhas(dados, filtros.valores.modalidade);
  const motivo = (/** @type {LinhaDaVisao} */ linha) =>
    linha.situacao === "comparada" ? "" : t(MOTIVO[linha.situacao], { corte });

  /**
   * @param {string} rotulo
   * @param {string} coluna
   * @returns {Node | undefined}
   */
  const comDefinicao = (rotulo, coluna) => {
    const origem = definicaoDaColuna(dados.ontologia, arquivo(), coluna);
    return origem ? definicao({ rotulo, definicao: origem }) : undefined;
  };

  const opcoesDaTabela = () => ({
    linhasDaVisao: linhasAtuais(),
    todas: todas(),
    escolhida: filtros.valores.uf,
    legenda: t("tela1.legenda-tabela", { recorte: recorteNoTitulo(), data }),
    situacao: motivo,
    arquivo: `credito-pj-por-uf-${filtros.valores.modalidade}-${dados.porUf.data_base}.csv`,
  });

  // ------------------------------------------------------------ filtros

  const apoioDaModalidade = elemento("span", { classe: "visao__apoio" });
  const atualizarApoio = () => {
    const origem = todas()
      ? null
      : definicaoDaModalidade(dados.ontologia, filtros.valores.modalidade);
    apoioDaModalidade.replaceChildren(
      ...(origem ? [definicao({ rotulo: recorte(), definicao: origem })] : []),
    );
  };
  const seletor = campoDeSelecao({
    rotulo: t("tela1.filtro-modalidade"),
    opcoes: [
      { valor: TODAS, texto: t("tela1.todas-as-modalidades") },
      ...todasAsModalidades.map((m) => ({
        valor: m.codigo,
        texto: m.comparadas > 0 ? m.nome : t("tela1.opcao-sem-comparacao", { nome: m.nome }),
      })),
    ],
    valor: TODAS,
    aoMudar: (valor) => filtros.definir({ modalidade: valor }),
    apoio: apoioDaModalidade,
  });
  const selecao = /** @type {HTMLSelectElement} */ (seletor.querySelector("select"));
  // PT: a forma fica na barra de filtros, junto da modalidade, como na
  //     revisão de 2026-10-05; sem a malha, o mapa sai das opções
  // EN: the form switch sits in the filter bar; without the mesh, no map
  const controleDaForma = controleSegmentado({
    rotulo: t("tela1.desenho"),
    opcoes: [
      ...(dados.malha ? [{ valor: "mapa", texto: t("tela1.mapa") }] : []),
      { valor: "grade", texto: t("tela1.grade") },
      { valor: "matriz", texto: t("tela1.matriz") },
      { valor: "tabela", texto: t("tela1.tabela") },
    ],
    valor: filtros.valores.desenho,
    aoMudar: (valor) => filtros.definir({ desenho: /** @type {Forma} */ (valor) }),
  });
  const barra = elemento("div", { classe: "visao__filtros" }, [seletor, controleDaForma]);

  // ------------------------------------------------------------ oportunidade

  /**
   * PT: O resumo do recorte: a carteira e a mediana, a régua das cores. Quantas
   *     UFs ficam abaixo da mediana já está no rótulo da oportunidade.
   * EN: The cut's summary: portfolio and median, the colors' yardstick.
   *
   * @returns {ItemDoDetalhe[]}
   */
  const itensDoResumo = () => {
    const r = resumo(linhasAtuais());
    return [
      {
        chave: t("tela1.resumo-carteira"),
        valor: reais(r.carteira),
        apoio: comDefinicao(t("tela1.resumo-carteira"), todas() ? "carteira_pj" : "carteira_ativa"),
      },
      {
        chave: t("tela1.resumo-mediana"),
        valor: r.mediana === null ? "–" : reais(r.mediana),
        apoio: comDefinicao(t("tela1.resumo-mediana"), "mediana_carteira_por_empresa"),
      },
    ];
  };

  const corpoDoDestaque = elemento("div", { classe: "visao__oportunidade" });
  const cartaoDestaque = cartaoDeGrafico(
    {
      titulo: t("tela1.titulo-destaque", { recorte: recorteNoTitulo() }),
      dataBase: data,
      fonte,
      nivel: "h2",
    },
    [corpoDoDestaque],
  );
  const desenharDestaque = () => {
    const r = resumo(linhasAtuais());
    corpoDoDestaque.replaceChildren(
      r.abaixo > 0
        ? numeroDeDestaque({
            valor: reais(r.custo),
            rotulo: t("tela1.destaque-rotulo", { abaixo: String(r.abaixo) }),
          })
        : vazio({
            titulo: t("tela1.vazio-titulo"),
            texto: t("tela1.vazio-texto", { corte, minimo: String(dados.minimoDeUfs) }),
          }),
      aviso({ tipo: "informacao", texto: t("tela1.ressalva-demanda"), variante: "linha" }),
    );
  };
  const oportunidadeEl = elemento("div", { classe: "visao__destaque" }, [cartaoDestaque]);

  // ------------------------------------------------------------ território

  const tituloDoTerritorio = () =>
    filtros.valores.desenho === "matriz"
      ? t("tela1.titulo-matriz")
      : t("tela1.titulo-territorio", { recorte: recorteNoTitulo() });
  // PT: o resumo do recorte mora junto do título do território, porque é a
  //     régua do que o mapa pinta: a mediana e quantas UFs ficam abaixo dela
  // EN: the cut's summary sits with the territory title: it is the yardstick
  //     the map paints against
  const resumoDoTerritorio = elemento("dl", { classe: "visao__resumo" });
  const desenharResumo = () =>
    resumoDoTerritorio.replaceChildren(
      ...itensDoResumo().flatMap((item) => [
        elemento("dt", {}, [item.chave, ...(item.apoio ? [item.apoio] : [])]),
        elemento("dd", { texto: item.valor }),
      ]),
    );
  const cartaoTerritorio = cartaoDeGrafico(
    { titulo: tituloDoTerritorio(), dataBase: data, fonte, nivel: "h2" },
    [
      resumoDoTerritorio,
      ...(dados.malha
        ? []
        : [aviso({ tipo: "atencao", texto: t("tela1.sem-malha"), variante: "linha" })]),
      aviso({ tipo: "informacao", texto: t("tela1.aviso-sede"), variante: "linha" }),
    ],
  );
  const idDoTitulo = /** @type {HTMLElement} */ (
    cartaoTerritorio.querySelector(".cartao-grafico__titulo")
  ).id;
  const territorio = elemento("div", { classe: "visao__sobre-o-territorio" }, [cartaoTerritorio]);
  const formaEl = elemento("div", { classe: "visao__forma" });
  formaEl.addEventListener("click", (evento) => {
    const botao = /** @type {HTMLElement} */ (evento.target).closest("[data-uf]");
    if (botao) filtros.definir({ uf: botao.getAttribute("data-uf") });
  });
  // PT: o palco do território: no computador, o centro da tela, na altura
  //     toda, nomeado pelo título que fica no painel ao lado
  // EN: the territory stage, named by the title in the side panel
  const palco = elemento(
    "div",
    { classe: "visao__palco", atributos: { role: "region", "aria-labelledby": idDoTitulo } },
    [formaEl],
  );

  /** @type {FormaDesenhada | null} */
  let atual = null;
  let geracao = 0;

  const dicaDaUf = (/** @type {string} */ sigla) => {
    const linha = linhasAtuais().find((l) => l.uf === sigla);
    if (!linha) return null;
    if (linha.indice === null) return motivo(linha);
    return `${t("tela1.por-empresa", { valor: reais(/** @type {number} */ (linha.carteiraPorEmpresa)) })}, ${posicao(linha.indice)}`;
  };
  const corDoTerritorio = () => {
    const linhasDaVisao = linhasAtuais();
    return {
      valores: Object.fromEntries(
        linhasDaVisao.map((l) => [l.uf, l.indice === null ? null : distancia(l.indice)]),
      ),
      classes,
      formatar: (/** @type {number} */ v) => `${numero(Math.abs(v) * 100, 0)}%`,
      rotuloSemValor: linhasDaVisao.some((l) => l.indice === null)
        ? t("tela1.sem-comparacao")
        : undefined,
    };
  };

  /**
   * PT: O mapa ou a grade, que mudam de cor com a modalidade.
   * EN: The map or the tile grid, recolored by modality.
   *
   * @param {"mapa" | "grade"} tipo
   * @returns {Promise<FormaDesenhada>}
   */
  const desenharUfs = async (tipo) => {
    const area = areaDoGrafico(tipo === "mapa" ? "grafico--mapa" : "grafico--cartograma");
    formaEl.replaceChildren(
      tipo === "mapa" ? area : elemento("div", { classe: "cartograma" }, [area]),
    );
    // PT: a legenda entra junto com a área, antes de o ECharts chegar, para
    //     o desenho não empurrar a página quando aparece (#92)
    // EN: the legend goes in with the area, before ECharts, so nothing shifts
    const cor = corDoTerritorio();
    const legendaPronta = legendaDeEspaco(cor.classes("claro"), cor.rotuloSemValor);
    area.after(legendaPronta);
    const opcoes = {
      ...cor,
      legendaPronta,
      dica: dicaDaUf,
      aoSelecionar: (/** @type {string} */ sigla) => filtros.definir({ uf: sigla }),
      selecionada: filtros.valores.uf,
      legenda: legendaDeEspaco,
    };
    const { cartograma, mapaPorUf, registrarMalha } = await graficos();
    let grafico;
    if (tipo === "mapa" && dados.malha) {
      registrarMalha(dados.malha);
      grafico = await mapaPorUf(area, opcoes);
    } else {
      grafico = await cartograma(area, opcoes);
    }
    return {
      atualizar: (chaves) => {
        if (chaves.includes("modalidade")) grafico.mudar(corDoTerritorio());
        if (chaves.includes("uf") || chaves.includes("modalidade")) {
          grafico.selecionar(filtros.valores.uf);
        }
      },
      destruir: () => grafico.destruir(),
    };
  };

  const modalidadesDaMatriz = todasAsModalidades
    .filter((m) => m.comparadas > 0)
    .map((m) => ({
      chave: m.codigo,
      rotulo: t(/** @type {ChaveDeTexto} */ (`modalidade-curta.${m.codigo}`)),
    }));
  const ufsDaMatriz = ufsPorCarteira(dados.porUf).map((sigla) => ({ chave: sigla, rotulo: sigla }));
  const celulasDaTela = celulasDaMatriz(dados.decisao).map((c) => {
    const modalidade = nomes.get(c.codigo) ?? c.codigo;
    const uf = ufPelaSigla(c.uf).nome;
    return {
      uf: c.uf,
      codigo: c.codigo,
      valor: c.indice === null ? null : distancia(c.indice),
      dica:
        c.indice === null
          ? t("tela1.dica-celula-fora", { uf, modalidade })
          : t("tela1.dica-celula", { uf, modalidade, posicao: posicao(c.indice) }),
    };
  });

  /**
   * PT: A matriz de UF por modalidade. No computador, deitada, com as
   *     modalidades nas linhas e as UFs nas colunas, para caber no cartão
   *     (ADR 0022); no celular, de pé. A modalidade escolhida e a UF ficam
   *     em destaque.
   * EN: The state-by-modality heatmap, lying down on desktop and upright on
   *     phones, with the chosen modality and state highlighted.
   *
   * @returns {Promise<FormaDesenhada>}
   */
  const desenharMatriz = async () => {
    const deitada = !estreita.matches;
    const area = areaDoGrafico("grafico--matriz-de-calor");
    formaEl.replaceChildren(area);
    const selecionada = () => {
      const uf = filtros.valores.uf;
      const modalidade = todas() ? null : filtros.valores.modalidade;
      return deitada ? { linha: modalidade, coluna: uf } : { linha: uf, coluna: modalidade };
    };
    const { matrizDeCalor } = await graficos();
    const grafico = await matrizDeCalor(area, {
      linhas: deitada ? modalidadesDaMatriz : ufsDaMatriz,
      colunas: deitada ? ufsDaMatriz : modalidadesDaMatriz,
      celulas: celulasDaTela.map((c) => ({
        linha: deitada ? c.codigo : c.uf,
        coluna: deitada ? c.uf : c.codigo,
        valor: c.valor,
        dica: c.dica,
      })),
      classes,
      rotuloSemValor: t("tela1.sem-comparacao"),
      legenda: legendaDeEspaco,
      aoSelecionar: (linha, coluna) =>
        filtros.definir(
          deitada ? { modalidade: linha, uf: coluna } : { uf: linha, modalidade: coluna },
        ),
      selecionada: selecionada(),
    });
    return {
      atualizar: (chaves) => {
        if (chaves.includes("uf") || chaves.includes("modalidade")) {
          grafico.selecionar(selecionada());
        }
      },
      destruir: () => grafico.destruir(),
    };
  };

  /**
   * PT: A tabela, com o download em CSV em cima, só nesta forma (revisão de
   *     2026-10-05). Ela se redesenha a cada mudança e guarda a rolagem.
   * EN: The table, with the CSV download above it, in this form only. It is
   *     redrawn on every change, keeping its scroll position.
   *
   * @returns {FormaDesenhada}
   */
  const desenharTabela = () => {
    const desenhar = () => {
      const topo = formaEl.querySelector(".visao__tabela")?.scrollTop ?? 0;
      const opcoes = opcoesDaTabela();
      const nova = tabelaDaTela(opcoes);
      formaEl.replaceChildren(
        elemento("div", { classe: "visao__acoes" }, [botaoDoCsv(opcoes)]),
        nova,
      );
      nova.scrollTop = topo;
    };
    desenhar();
    return { atualizar: desenhar, destruir: () => {} };
  };

  const desenharTerritorio = async () => {
    geracao += 1;
    const minha = geracao;
    atual?.destruir();
    atual = null;
    const tipo = filtros.valores.desenho;
    formaEl.className = `visao__forma visao__forma--${tipo}`;
    raiz.classList.toggle("visao--forma-larga", FORMAS_LARGAS.has(tipo));
    atualizarTitulos();
    const origem = cartaoTerritorio.querySelector(".cartao-grafico__origem");
    if (origem) {
      origem.textContent = `${data} · ${tipo === "mapa" ? t("tela1.fonte-com-malha") : fonte}`;
    }
    const nova =
      tipo === "tabela"
        ? desenharTabela()
        : tipo === "matriz"
          ? await desenharMatriz()
          : await desenharUfs(tipo);
    if (minha !== geracao) {
      nova.destruir();
      return;
    }
    atual = nova;
  };

  // PT: a matriz troca de orientação quando a janela cruza a largura estreita
  // EN: the heatmap flips orientation when the window crosses the narrow width
  const aoCruzarALargura = () => {
    if (filtros.valores.desenho === "matriz") void desenharTerritorio();
  };
  estreita.addEventListener("change", aoCruzarALargura);

  // ------------------------------------------------------------ ranking

  const areaRanking = areaDoGrafico("grafico--ranking");
  const vazioDoRanking = elemento("div", { classe: "visao__vazio" });
  const cartaoRanking = cartaoDeGrafico(
    {
      titulo: t("tela1.titulo-ranking", { recorte: recorteNoTitulo() }),
      dataBase: data,
      fonte,
      nivel: "h2",
    },
    [areaRanking, vazioDoRanking],
  );
  // PT: o ranking rola dentro do próprio cartão, para não ser ele quem
  //     decide a altura da página (revisão visual da #69)
  // EN: the ranking scrolls inside its card instead of setting page height
  const rolagemDoRanking = /** @type {HTMLElement} */ (
    cartaoRanking.querySelector(".cartao-grafico__corpo")
  );
  cartaoRanking.classList.add("cartao-grafico--preenche");
  comRolagem(rolagemDoRanking, "visao__rolagem", t("tela1.rolagem-do-ranking"));
  const mostrarVazio = () => {
    const semItens = oportunidade(linhasAtuais()).length === 0;
    areaRanking.hidden = semItens;
    vazioDoRanking.replaceChildren(
      ...(semItens
        ? [
            vazio({
              titulo: t("tela1.vazio-titulo"),
              texto: t("tela1.vazio-texto", { corte, minimo: String(dados.minimoDeUfs) }),
            }),
          ]
        : []),
    );
  };
  /** @type {import("../../graficos/ranking.js").GraficoDoRanking | null} */
  let graficoRanking = null;

  /**
   * PT: Rola o ranking até a barra da UF escolhida, sem animação: a rolagem
   *     suave era cancelada pelo redesenho do gráfico que acontece na mesma
   *     hora.
   * EN: Scrolls the ranking to the chosen state's bar, instantly.
   *
   * @param {string | null} sigla
   */
  const mostrarNoRanking = (sigla) => {
    const y = sigla && graficoRanking ? graficoRanking.posicaoDe(sigla) : null;
    if (y === null) return;
    rolagemDoRanking.scrollTo({ top: Math.max(0, y - rolagemDoRanking.clientHeight / 2) });
  };

  // ------------------------------------------------------------ painel

  const painel = painelDeDetalhe({
    dica: t("tela1.detalhe-dica"),
    aoFechar: () => filtros.definir({ uf: null }),
  });

  const retrato = () => {
    const colunas = dados.porUf.colunas;
    return {
      mes: dataBase(`${String(colunas.retrato_do_cnpj[0])}-01`),
      meses: String(colunas.meses_ate_o_retrato[0]),
    };
  };

  const mostrarDetalhe = () => {
    const { uf } = filtros.valores;
    const linhasDaVisao = linhasAtuais();
    const linha = uf ? linhasDaVisao.find((l) => l.uf === uf) : undefined;
    // PT: na tela única, o painel toma o lugar do ranking só com uma UF
    // EN: on the single screen, the panel replaces the ranking only with a state
    raiz.classList.toggle("visao--com-uf", Boolean(linha));
    if (!linha) {
      painel.limpar();
      return;
    }
    const { mes, meses } = retrato();
    painel.mostrar(
      perfilDaUf({
        linha,
        linhasDaVisao,
        decisao: dados.decisao,
        todas: todas(),
        modalidade: filtros.valores.modalidade,
        subtitulo: `${recorte()} · ${data}`,
        nota:
          linha.situacao === "comparada" ? t("tela1.nota-retrato", { mes, meses }) : motivo(linha),
        comDefinicao,
        aoEscolherModalidade: (codigo) => filtros.definir({ modalidade: codigo }),
      }),
    );
  };

  // ------------------------------------------------------------ montagem

  function atualizarTitulos() {
    for (const [cartao, titulo] of /** @type {[HTMLElement, string][]} */ ([
      [cartaoDestaque, t("tela1.titulo-destaque", { recorte: recorteNoTitulo() })],
      [cartaoTerritorio, tituloDoTerritorio()],
      [cartaoRanking, t("tela1.titulo-ranking", { recorte: recorteNoTitulo() })],
    ])) {
      const el = cartao.querySelector(".cartao-grafico__titulo");
      if (el) el.textContent = titulo;
    }
  }

  // PT: cada lado é uma coluna com a própria altura, para a esquerda não
  //     esperar pela direita
  // EN: each side is a column with its own height
  const raiz = elemento("div", { classe: "visao visao--palco visao--credito-por-uf" }, [
    elemento("h1", { classe: "visualmente-oculto", texto: t("tela1.titulo") }),
    elemento("div", { classe: "visao__lado visao__lado--esquerdo" }, [barra, territorio]),
    palco,
    elemento("div", { classe: "visao__lado visao__lado--direito" }, [
      oportunidadeEl,
      elemento("div", { classe: "visao__ranking" }, [cartaoRanking]),
      painel.elemento,
    ]),
  ]);
  el.replaceChildren(raiz);

  atualizarApoio();
  desenharDestaque();
  desenharResumo();
  mostrarVazio();
  mostrarDetalhe();
  void desenharTerritorio();

  // PT: o ranking se desenha quando o cartão aparece. No celular ele fica bem
  //     abaixo do mapa, e desenhá-lo na abertura pesava na carga (#89)
  // EN: the ranking draws when its card shows up; on phones it sits far below
  let desmontada = false;
  let rankingPedido = false;
  const desenharRanking = async () => {
    if (rankingPedido) return;
    rankingPedido = true;
    const { ranking } = await graficos();
    const grafico = await ranking(areaRanking, {
      itens: oportunidade(linhasAtuais()),
      formatar: (v) => reais(v),
      aoSelecionar: (sigla) => filtros.definir({ uf: sigla }),
    });
    if (desmontada) {
      grafico.destruir();
      return;
    }
    graficoRanking = grafico;
    if (filtros.valores.uf) grafico.selecionar(filtros.valores.uf);
  };
  const vigiaDoRanking =
    "IntersectionObserver" in window
      ? new IntersectionObserver((entradas) => {
          if (!entradas.some((entrada) => entrada.isIntersecting)) return;
          vigiaDoRanking?.disconnect();
          void desenharRanking();
        })
      : null;
  if (vigiaDoRanking) vigiaDoRanking.observe(cartaoRanking);
  else void desenharRanking();

  const pararDeOuvir = filtros.aoMudar((evento) => {
    const { chaves } = evento.detail;
    if (chaves.includes("modalidade")) {
      selecao.value = filtros.valores.modalidade;
      atualizarTitulos();
      atualizarApoio();
      desenharDestaque();
      desenharResumo();
      mostrarVazio();
      graficoRanking?.mudar({ itens: oportunidade(linhasAtuais()) });
    }
    if (chaves.includes("desenho")) void desenharTerritorio();
    else atual?.atualizar(chaves);
    if (chaves.includes("uf") || chaves.includes("modalidade")) {
      graficoRanking?.selecionar(filtros.valores.uf);
      mostrarNoRanking(filtros.valores.uf);
    }
    mostrarDetalhe();
  });

  return () => {
    desmontada = true;
    vigiaDoRanking?.disconnect();
    pararDeOuvir();
    estreita.removeEventListener("change", aoCruzarALargura);
    geracao += 1;
    atual?.destruir();
    graficoRanking?.destruir();
  };
}
