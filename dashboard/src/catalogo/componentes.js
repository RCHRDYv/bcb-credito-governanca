/**
 * PT: As seções dos componentes de interface no catálogo (#64): controles,
 *     dados e avisos, chat e estados, nos dois temas.
 *
 *     A tabela, a dica e o chat usam números reais de `exemplos.json`, que
 *     sai dos marts. O chat ainda não existe (#51), e o exemplo dele fica
 *     marcado como ilustrativo. O cabeçalho do gráfico aparece na seção de
 *     gráficos, em cada cartão.
 *
 * EN: Catalog sections for interface components, in both themes, with real
 *     numbers where they exist. The chat example is marked illustrative.
 */

import { alertaAntecipado } from "../componentes/alerta-antecipado.js";
import { aviso } from "../componentes/aviso.js";
import { botao } from "../componentes/botao.js";
import { campo } from "../componentes/campo.js";
import {
  abstencaoDoChat,
  conversa,
  entradaDoChat,
  perguntaDoChat,
  respostaDoChat,
} from "../componentes/chat.js";
import { grupoDeChips } from "../componentes/chips.js";
import { controleSegmentado } from "../componentes/controle-segmentado.js";
import { comDica, corpoDaDica } from "../componentes/dica.js";
import { carregando, chatAcordando, erro, vazio } from "../componentes/estados.js";
import { etiquetaDeQuadrante, quadranteDoMart } from "../componentes/etiqueta-de-quadrante.js";
import { tabela } from "../componentes/tabela.js";
import { elemento } from "../dom.js";
import { dataBase, pontos, reais, vezes } from "../formatos.js";
import { t } from "../textos/index.js";
import exemplos from "./exemplos.json" with { type: "json" };
import { ladoALado, secao } from "./secoes.js";

/** @typedef {import("../tokens.js").Tema} Tema */
/** @typedef {import("../textos/index.js").ChaveDeTexto} ChaveDeTexto */
/** @typedef {(typeof exemplos.matriz.celulas)[number]} Celula */

/**
 * PT: Um bloco do catálogo: o nome do componente e os exemplos em linha.
 * EN: A catalog block: component name and examples in a row.
 *
 * @param {ChaveDeTexto} nome
 * @param {Node[]} exemplosDoBloco
 * @param {ChaveDeTexto} [nota]
 * @returns {HTMLElement}
 */
function bloco(nome, exemplosDoBloco, nota) {
  return elemento("div", { classe: "bloco-de-componente" }, [
    elemento("h4", { classe: "bloco-de-componente__nome", texto: t(nome) }),
    elemento("div", { classe: "bloco-de-componente__exemplos" }, exemplosDoBloco),
    ...(nota ? [elemento("p", { classe: "catalogo__nota", texto: t(nota) })] : []),
  ]);
}

/**
 * PT: Os dois painéis de tema com o campo de luz atrás, para o vidro dos
 *     componentes aparecer como aparece na página.
 * EN: Both theme panels with the light field behind.
 *
 * @param {(tema: Tema) => Node[]} montar
 * @returns {HTMLElement}
 */
function painelComCampoDeLuz(montar) {
  return ladoALado(montar, { campoDeLuz: true });
}

// -----------------------------------------------------------------------------
// PT: Controles
// EN: Controls
// -----------------------------------------------------------------------------

/**
 * PT: Seção dos controles.
 * EN: Controls section.
 *
 * @returns {HTMLElement}
 */
export function secaoControles() {
  const modalidades = exemplos.carteira_por_modalidade.series
    .filter((serie) => serie.codigo !== "outros")
    .slice(0, 4);
  return secao("controles", "catalogo.controles", "catalogo.controles-explicacao", [
    painelComCampoDeLuz(() => [
      bloco("catalogo.botoes", [
        botao({ texto: t("catalogo.exemplo-aplicar"), icone: "arrow-right" }),
        botao({ texto: t("catalogo.exemplo-exportar"), variante: "secundario", icone: "download" }),
        botao({ texto: t("chat.ver-o-sql"), variante: "sutil" }),
        botao({ texto: t("catalogo.desativado"), desativado: true }),
        botao({ texto: t("catalogo.exemplo-aplicar"), carregando: true }),
      ]),
      bloco("catalogo.controle-segmentado", [
        controleSegmentado({
          rotulo: t("catalogo.exemplo-visao"),
          opcoes: [
            { valor: "credito", texto: t("catalogo.visao-credito") },
            { valor: "risco", texto: t("catalogo.visao-risco") },
            { valor: "recomendacao", texto: t("catalogo.visao-recomendacao") },
          ],
          valor: "recomendacao",
        }),
      ]),
      bloco("catalogo.chips", [
        grupoDeChips({
          rotulo: t("catalogo.exemplo-modalidades"),
          opcoes: modalidades.map((serie) => ({ valor: serie.codigo, texto: serie.nome })),
          selecionados: [modalidades[0].codigo],
        }),
      ]),
      bloco("catalogo.campos", [
        campo({
          rotulo: t("catalogo.campo-estado"),
          exemplo: t("catalogo.exemplo-sp"),
          ajuda: t("catalogo.ajuda-estado"),
        }),
        campo({ rotulo: t("catalogo.campo-modalidade"), valor: modalidades[0].nome }),
        campo({ rotulo: t("catalogo.campo-estado"), valor: "XX", erro: t("catalogo.erro-estado") }),
        campo({
          rotulo: t("catalogo.campo-pergunta"),
          exemplo: t("catalogo.chat-indisponivel"),
          desativado: true,
        }),
      ]),
    ]),
  ]);
}

// -----------------------------------------------------------------------------
// PT: Dados e avisos
// EN: Data and notices
// -----------------------------------------------------------------------------

/**
 * PT: As duas células com mais carteira de cada quadrante, da maior para a
 *     menor, para a tabela mostrar os quatro.
 * EN: The two largest cells of each quadrant.
 *
 * @returns {Celula[]}
 */
function celulasDaTabela() {
  /** @type {Map<string, Celula[]>} */
  const porQuadrante = new Map();
  for (const celula of exemplos.matriz.celulas) {
    porQuadrante.set(celula.quadrante, [...(porQuadrante.get(celula.quadrante) ?? []), celula]);
  }
  return [...porQuadrante.values()]
    .flatMap((celulas) =>
      [...celulas].sort((a, b) => b.carteira_ativa - a.carteira_ativa).slice(0, 2),
    )
    .sort((a, b) => b.carteira_ativa - a.carteira_ativa);
}

/**
 * PT: O conteúdo da dica de uma célula: o nome e os números dela.
 * EN: A cell's tooltip content.
 *
 * @param {Celula} celula
 * @returns {(Node | string)[]}
 */
function conteudoDaDica(celula) {
  return [
    elemento("strong", { texto: `${celula.uf} · ${celula.modalidade}` }),
    elemento("br"),
    `${t("matriz.eixo-espaco-curto")}: ${vezes(celula.indice_de_espaco)}`,
    elemento("br"),
    `${t("matriz.eixo-risco-curto")}: ${pontos(celula.desvio_do_risco)}`,
  ];
}

/**
 * PT: Seção dos dados e avisos.
 * EN: Data and notices section.
 *
 * @returns {HTMLElement}
 */
export function secaoDadosEAvisos() {
  const linhas = celulasDaTabela();
  const [primeira] = linhas;
  return secao("dados-e-avisos", "catalogo.dados-e-avisos", "catalogo.dados-e-avisos-explicacao", [
    painelComCampoDeLuz(() => [
      bloco("catalogo.etiquetas", [
        ...["entrar", "observar", "nao-entrar", "manter"].map((q) =>
          etiquetaDeQuadrante(
            /** @type {import("../componentes/etiqueta-de-quadrante.js").Quadrante} */ (q),
          ),
        ),
        alertaAntecipado(),
      ]),
      bloco("catalogo.tabela", [
        tabela({
          legenda: t("catalogo.tabela-legenda", { data: dataBase(exemplos.data_base) }),
          linhas,
          colunas: [
            { titulo: t("catalogo.coluna-uf"), celula: (c) => c.uf },
            { titulo: t("catalogo.coluna-modalidade"), celula: (c) => c.modalidade },
            {
              titulo: t("catalogo.coluna-carteira"),
              tipo: "numero",
              celula: (c) => reais(c.carteira_ativa),
            },
            {
              titulo: t("catalogo.coluna-espaco"),
              tipo: "numero",
              celula: (c) => vezes(c.indice_de_espaco),
            },
            {
              titulo: t("catalogo.coluna-risco"),
              tipo: "numero",
              celula: (c) => pontos(c.desvio_do_risco),
            },
            {
              titulo: t("catalogo.coluna-quadrante"),
              celula: (c) => etiquetaDeQuadrante(quadranteDoMart(c.quadrante)),
            },
            {
              titulo: t("catalogo.coluna-alerta"),
              celula: (c) => (c.alerta_antecipado ? alertaAntecipado() : ""),
            },
          ],
        }),
      ]),
      bloco(
        "catalogo.dica",
        [
          corpoDaDica(conteudoDaDica(primeira)),
          comDica(
            botao({ texto: `${primeira.uf} · ${primeira.modalidade}`, variante: "sutil" }),
            conteudoDaDica(primeira),
          ),
        ],
        "catalogo.dica-nota",
      ),
      bloco("catalogo.avisos", [
        aviso({ tipo: "informacao", texto: t("catalogo.aviso-uf-da-sede") }),
        aviso({ tipo: "atencao", texto: t("catalogo.aviso-quebra") }),
        aviso({ tipo: "erro", texto: t("catalogo.aviso-erro") }),
      ]),
    ]),
  ]);
}

// -----------------------------------------------------------------------------
// PT: Chat
// EN: Chat
// -----------------------------------------------------------------------------

/**
 * PT: Seção do chat, com o exemplo marcado como ilustrativo. O número da
 *     resposta é real, do mart de decisão; o SQL mostrado é um exemplo sobre
 *     o esquema estrela, que não foi executado.
 * EN: Chat section; the example is marked illustrative.
 *
 * @returns {HTMLElement}
 */
export function secaoChat() {
  const {
    uf,
    carteira_por_empresa: carteira,
    mediana_carteira_por_empresa: mediana,
    modalidade,
  } = exemplos.por_uf;
  const sp = carteira[uf.indexOf("SP")];
  return secao("chat", "catalogo.chat", "catalogo.chat-explicacao", [
    painelComCampoDeLuz(() => [
      elemento("p", { classe: "selo-ilustrativo", texto: t("catalogo.chat-ilustrativo") }),
      conversa([
        perguntaDoChat(t("catalogo.chat-pergunta", { modalidade })),
        respostaDoChat({
          numero: reais(sp),
          frase: t("catalogo.chat-frase", {
            data: dataBase(exemplos.data_base),
            mediana: reais(mediana),
          }),
          ressalvas: [t("catalogo.aviso-uf-da-sede")],
          sql: t("catalogo.chat-sql"),
        }),
        perguntaDoChat(t("catalogo.chat-pergunta-sem-dado")),
        abstencaoDoChat({
          motivo: t("catalogo.chat-motivo"),
          faltaria: t("catalogo.chat-faltaria"),
        }),
      ]),
      entradaDoChat(),
    ]),
  ]);
}

// -----------------------------------------------------------------------------
// PT: Estados
// EN: States
// -----------------------------------------------------------------------------

/**
 * PT: Seção dos estados de carregamento e de exceção.
 * EN: Loading and exception states section.
 *
 * @returns {HTMLElement}
 */
export function secaoEstados() {
  return secao("estados", "catalogo.estados", "catalogo.estados-explicacao", [
    painelComCampoDeLuz(() => [
      bloco("catalogo.estado-carregando", [carregando()]),
      bloco("catalogo.estado-vazio", [
        vazio({ titulo: t("catalogo.vazio-titulo"), texto: t("catalogo.vazio-texto") }),
      ]),
      bloco("catalogo.estado-erro", [
        erro({
          titulo: t("catalogo.erro-titulo"),
          texto: t("catalogo.erro-texto"),
          aoTentarDeNovo: () => undefined,
        }),
      ]),
      bloco("catalogo.estado-chat-acordando", [chatAcordando()]),
    ]),
  ]);
}
