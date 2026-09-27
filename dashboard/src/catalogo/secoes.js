/**
 * PT: As seções do catálogo do design system, uma função por fundação.
 *
 *     Cada seção lê os tokens gerados e aplica as variáveis CSS nos
 *     elementos. As seções cujas cores mudam com o tema montam dois painéis
 *     lado a lado, um com `color-scheme: light` e outro com `dark`: como as
 *     cores semânticas são `light-dark()`, o mesmo CSS mostra os dois temas.
 *
 *     Estilo aplicado por JavaScript usa sempre `style.setProperty`, que a
 *     política de segurança de conteúdo da #68 permite, e nunca o atributo
 *     `style` escrito como texto.
 *
 * EN: The catalog sections, one function per foundation. Theme-dependent
 *     sections render a light and a dark panel side by side; since semantic
 *     colors are `light-dark()`, the same CSS shows both themes. Styles set
 *     from JavaScript always use `style.setProperty`.
 */

import { compor, razaoDeContraste } from "../cor/contraste.js";
import { elemento } from "../dom.js";
import { t } from "../textos/index.js";
import { cor, TOKENS, token, valorLiteral } from "../tokens.js";

/**
 * @typedef {import("../tokens.js").Tema} Tema
 * @typedef {import("../tokens.js").TokenGerado} TokenGerado
 * @typedef {import("../textos/index.js").ChaveDeTexto} ChaveDeTexto
 */

// -----------------------------------------------------------------------------
// PT: Peças comuns
// EN: Shared pieces
// -----------------------------------------------------------------------------

/**
 * PT: Uma seção com título, explicação e conteúdo.
 * EN: A section with a heading, an explanation and content.
 *
 * @param {string} id
 * @param {ChaveDeTexto} titulo
 * @param {ChaveDeTexto} explicacao
 * @param {Node[]} conteudo
 * @returns {HTMLElement}
 */
function secao(id, titulo, explicacao, conteudo) {
  return elemento(
    "section",
    { classe: "secao", atributos: { "aria-labelledby": `titulo-${id}` } },
    [
      elemento("h2", { texto: t(titulo), atributos: { id: `titulo-${id}` } }),
      elemento("p", { classe: "secao__explicacao", texto: t(explicacao) }),
      ...conteudo,
    ],
  );
}

/**
 * PT: Dois painéis, claro e escuro, com o mesmo conteúdo montado para cada tema.
 * EN: Two panels, light and dark, with the same content built for each theme.
 *
 * @param {(tema: Tema) => Node[]} montar
 * @returns {HTMLElement}
 */
function ladoALado(montar) {
  /** @type {[Tema, ChaveDeTexto][]} */
  const temas = [
    ["claro", "catalogo.tema-claro"],
    ["escuro", "catalogo.tema-escuro"],
  ];
  return elemento(
    "div",
    { classe: "lado-a-lado" },
    temas.map(([tema, rotulo]) =>
      elemento("div", { classe: `tema tema--${tema}` }, [
        elemento("h3", { classe: "tema__rotulo", texto: t(rotulo) }),
        ...montar(tema),
      ]),
    ),
  );
}

/**
 * PT: Aplica uma variável CSS numa propriedade do elemento.
 * EN: Sets a CSS property from a variable.
 *
 * @template {HTMLElement} E
 * @param {E} el
 * @param {Record<string, string>} propriedades
 * @returns {E}
 */
function comEstilo(el, propriedades) {
  for (const [propriedade, valor] of Object.entries(propriedades)) {
    el.style.setProperty(propriedade, valor);
  }
  return el;
}

/**
 * PT: O nome curto do token, sem o grupo, para rótulos.
 * EN: The token's short name, for labels.
 *
 * @param {TokenGerado} item
 * @param {string} prefixo
 * @returns {string}
 */
function nomeCurto(item, prefixo) {
  return item.variavel.replace(`--${prefixo.replaceAll(".", "-")}-`, "");
}

/**
 * PT: Número no formato brasileiro, com casas fixas.
 * EN: Number in Brazilian format.
 *
 * @param {number} valor
 * @param {number} casas
 * @returns {string}
 */
function numero(valor, casas) {
  return valor.toLocaleString("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  });
}

// -----------------------------------------------------------------------------
// PT: Cores
// EN: Colors
// -----------------------------------------------------------------------------

/**
 * PT: Os grupos de cores semânticas, na ordem do guia, e se o contraste no
 *     fundo da página faz sentido para eles.
 * EN: Semantic color groups, in the guide's order.
 *
 * @type {{ titulo: ChaveDeTexto, prefixos: string[], contraste: boolean }[]}
 */
const GRUPOS_DE_COR = [
  { titulo: "catalogo.grupo.fundos", prefixos: ["color.background"], contraste: false },
  { titulo: "catalogo.grupo.bordas", prefixos: ["color.border"], contraste: true },
  { titulo: "catalogo.grupo.texto", prefixos: ["color.text"], contraste: true },
  {
    titulo: "catalogo.grupo.acao",
    prefixos: ["color.interactive", "color.link", "color.focus"],
    contraste: true,
  },
  { titulo: "catalogo.grupo.estado", prefixos: ["color.support"], contraste: true },
  { titulo: "catalogo.grupo.quadrantes", prefixos: ["color.quadrante"], contraste: true },
  { titulo: "catalogo.grupo.alerta", prefixos: ["color.alerta-antecipado"], contraste: true },
  { titulo: "catalogo.grupo.campo-de-luz", prefixos: ["color.campo-de-luz"], contraste: false },
];

/**
 * PT: O fundo em que a cor é usada, quando não é a página. O texto sobre cor
 *     forte é medido contra o botão, e o texto do alerta contra o fundo dele.
 * EN: The background a color is used on, when it is not the page.
 *
 * @type {Record<string, string>}
 */
const FUNDO_DE_USO = {
  "color.text.on-color": "color.background.brand.default",
  "color.alerta-antecipado.texto": "color.alerta-antecipado.fundo",
};

/**
 * PT: Cores sem contraste mínimo: as bordas sutis são decorativas, e o fundo
 *     do alerta é ele mesmo o fundo do texto.
 * EN: Colors with no minimum contrast.
 */
const SEM_CONTRASTE = new Set([
  "color.border.subtle",
  "color.border.subtle-em-camada",
  "color.alerta-antecipado.fundo",
]);

/**
 * PT: O contraste de uma cor contra o fundo em que ela é usada, em texto.
 * EN: A color's contrast against the background it is used on, as text.
 *
 * @param {string} caminho
 * @param {Tema} tema
 * @returns {string}
 */
function contrasteEmTexto(caminho, tema) {
  if (SEM_CONTRASTE.has(caminho)) {
    return "";
  }
  const fundo = cor(FUNDO_DE_USO[caminho] ?? "color.background.page", tema).hex;
  const valor = cor(caminho, tema);
  const opaco = valor.alpha < 1 ? compor(valor, fundo) : valor.hex;
  return `${numero(razaoDeContraste(opaco, fundo), 2)}:1`;
}

/**
 * PT: Medida com espaço antes da unidade, como no resto do projeto: 16 px.
 * EN: A measure with a space before the unit.
 *
 * @param {string} valor
 * @returns {string}
 */
function comEspaco(valor) {
  return valor.replace(/(\d)(px|ms)\b/g, "$1 $2");
}

/**
 * PT: A cor em texto: `#0f62fe`, ou `#ffffff a 62%` quando é transparente.
 * EN: The color as text.
 *
 * @param {import("../tokens.js").CorNoTema} valor
 * @returns {string}
 */
function corEmTexto(valor) {
  return valor.alpha < 1 ? `${valor.hex} a ${Math.round(valor.alpha * 100)}%` : valor.hex;
}

/**
 * PT: A tabela de cores de um tema.
 * EN: One theme's color table.
 *
 * @param {Tema} tema
 * @returns {Node[]}
 */
function tabelaDeCores(tema) {
  const cabecalho = elemento("thead", {}, [
    elemento(
      "tr",
      {},
      /** @type {ChaveDeTexto[]} */ ([
        "catalogo.coluna-cor",
        "catalogo.coluna-token",
        "catalogo.coluna-valor",
        "catalogo.coluna-contraste",
      ]).map((chave) => elemento("th", { texto: t(chave), atributos: { scope: "col" } })),
    ),
  ]);

  const grupos = GRUPOS_DE_COR.map((grupo) => {
    const itens = TOKENS.filter(
      (item) => item.tipo === "color" && grupo.prefixos.some((p) => item.caminho.startsWith(p)),
    );
    const linhas = itens.map((item) => {
      const valor = cor(item.caminho, tema);
      const amostra = comEstilo(elemento("span", { classe: "amostra" }), {
        background: `var(${item.variavel})`,
      });
      return elemento("tr", {}, [
        elemento("td", {}, [amostra]),
        elemento("td", {}, [elemento("code", { texto: item.variavel })]),
        elemento("td", { texto: corEmTexto(valor) }),
        elemento("td", {
          classe: "numero",
          texto: grupo.contraste ? contrasteEmTexto(item.caminho, tema) : "",
        }),
      ]);
    });
    return elemento("tbody", {}, [
      elemento("tr", {}, [
        elemento("th", {
          classe: "tabela__grupo",
          texto: t(grupo.titulo),
          atributos: { colspan: "4", scope: "colgroup" },
        }),
      ]),
      ...linhas,
    ]);
  });

  return [elemento("div", { classe: "tabela" }, [elemento("table", {}, [cabecalho, ...grupos])])];
}

/**
 * PT: Seção de cores semânticas, com o claro e o escuro lado a lado.
 * EN: Semantic colors section.
 *
 * @returns {HTMLElement}
 */
export function secaoCores() {
  return secao("cores", "catalogo.cores", "catalogo.cores-explicacao", [ladoALado(tabelaDeCores)]);
}

/**
 * PT: Seção da paleta primitiva do Carbon, que não muda com o tema.
 * EN: Carbon primitive palette section.
 *
 * @returns {HTMLElement}
 */
export function secaoPaleta() {
  const familias = ["gray", "blue", "teal", "yellow", "red", "purple", "green", "cyan", "magenta"];
  const faixas = familias.map((familia) => {
    const degraus = TOKENS.filter(
      (item) => item.camada === "primitivo" && item.caminho.startsWith(`color.${familia}.`),
    );
    return elemento("div", { classe: "paleta__familia" }, [
      elemento("p", { classe: "paleta__nome", texto: familia }),
      elemento(
        "ol",
        { classe: "paleta__degraus" },
        degraus.map((item) =>
          elemento("li", {}, [
            comEstilo(elemento("span", { classe: "amostra amostra--larga" }), {
              background: `var(${item.variavel})`,
            }),
            elemento("span", {
              classe: "paleta__degrau",
              texto: nomeCurto(item, `color.${familia}`),
            }),
          ]),
        ),
      ),
    ]);
  });
  return secao("paleta", "catalogo.paleta", "catalogo.paleta-explicacao", faixas);
}

// -----------------------------------------------------------------------------
// PT: Tipo, espaço e raio
// EN: Type, space and radius
// -----------------------------------------------------------------------------

/**
 * PT: Seção da escala tipográfica.
 * EN: Type scale section.
 *
 * @returns {HTMLElement}
 */
export function secaoTipografia() {
  const estilos = TOKENS.filter((item) => item.tipo === "typography");
  const itens = estilos.map((item) => {
    const codigo = item.caminho === "type.code-01";
    const exemplo = comEstilo(
      elemento("p", {
        classe: "tipo__exemplo",
        texto: t(codigo ? "catalogo.tipografia-codigo" : "catalogo.tipografia-exemplo"),
      }),
      { font: `var(${item.variavel})`, "letter-spacing": `var(${item.variavel}-letter-spacing)` },
    );
    const [peso, resto] = valorLiteral(item.variavel).split(" ");
    const [tamanho] = resto.split("/");
    return elemento("li", { classe: "tipo" }, [
      elemento("p", { classe: "tipo__meta" }, [
        elemento("code", { texto: nomeCurto(item, "type") }),
        ` ${comEspaco(tamanho)} · peso ${peso}`,
      ]),
      exemplo,
    ]);
  });
  return secao("tipografia", "catalogo.tipografia", "catalogo.tipografia-explicacao", [
    elemento("ul", { classe: "tipos" }, itens),
  ]);
}

/**
 * PT: Seção da escala de espaçamento.
 * EN: Spacing scale section.
 *
 * @returns {HTMLElement}
 */
export function secaoEspacamento() {
  const itens = TOKENS.filter((item) => item.caminho.startsWith("space.")).map((item) =>
    elemento("li", { classe: "espaco" }, [
      elemento("code", { texto: `space-${nomeCurto(item, "space")}` }),
      elemento("span", { classe: "numero", texto: comEspaco(item.css) }),
      comEstilo(elemento("span", { classe: "espaco__barra" }), {
        "inline-size": `var(${item.variavel})`,
      }),
    ]),
  );
  return secao("espacamento", "catalogo.espacamento", "catalogo.espacamento-explicacao", [
    elemento("ol", { classe: "espacos" }, itens),
  ]);
}

/**
 * PT: Seção dos raios, pelo uso.
 * EN: Radius section.
 *
 * @returns {HTMLElement}
 */
export function secaoRaios() {
  const itens = TOKENS.filter((item) => item.caminho.startsWith("radius.")).map((item) =>
    elemento("li", { classe: "raio" }, [
      comEstilo(elemento("span", { classe: "raio__caixa" }), {
        "border-radius": `var(${item.variavel})`,
      }),
      elemento("code", { texto: nomeCurto(item, "radius") }),
      elemento("span", { classe: "numero", texto: comEspaco(valorLiteral(item.variavel)) }),
    ]),
  );
  return secao("raios", "catalogo.raios", "catalogo.raios-explicacao", [
    elemento("ul", { classe: "raios" }, itens),
  ]);
}

// -----------------------------------------------------------------------------
// PT: Elevação, vidro e movimento
// EN: Elevation, glass and motion
// -----------------------------------------------------------------------------

/**
 * PT: Seção de elevação, nos dois temas.
 * EN: Elevation section, in both themes.
 *
 * @returns {HTMLElement}
 */
export function secaoElevacao() {
  return secao("elevacao", "catalogo.elevacao", "catalogo.elevacao-explicacao", [
    ladoALado(() => [
      elemento("div", { classe: "superficies" }, [
        elemento("div", { classe: "superficie superficie--1", texto: t("catalogo.nivel-1") }),
        elemento("div", { classe: "superficie superficie--2", texto: t("catalogo.nivel-2") }),
      ]),
    ]),
  ]);
}

/**
 * PT: Seção dos vidros sobre o campo de luz, nos dois temas.
 * EN: Glass over the light field, in both themes.
 *
 * @returns {HTMLElement}
 */
export function secaoVidro() {
  // PT: o vidro claro só leva rótulo curto, como nos controles que flutuam; o
  //     texto de ajuda vai só no regular, onde o contraste é conferido no teste
  // EN: clear glass only carries a short label; helper text goes on regular glass
  const claro = elemento("div", { classe: "vidro vidro--claro" }, [
    elemento("p", { classe: "vidro__titulo", texto: t("catalogo.vidro-claro") }),
  ]);
  const regular = elemento("div", { classe: "vidro vidro--regular" }, [
    elemento("p", { classe: "vidro__titulo", texto: t("catalogo.vidro-regular") }),
    elemento("p", { classe: "vidro__texto", texto: t("catalogo.vidro-texto") }),
  ]);
  /** @param {HTMLElement} el */
  const copia = (el) => /** @type {HTMLElement} */ (el.cloneNode(true));
  return secao("vidro", "catalogo.vidro", "catalogo.vidro-explicacao", [
    ladoALado(() => [elemento("div", { classe: "campo-de-luz" }, [copia(claro), copia(regular)])]),
  ]);
}

/**
 * PT: Seção de movimento: a mola ao lado da curva produtiva do Carbon.
 * EN: Motion section: the spring beside Carbon's productive curve.
 *
 * @returns {HTMLElement}
 */
export function secaoMovimento() {
  const duracao = comEspaco(valorLiteral(token("motion.duracao.longa").variavel));
  /** @param {"mola" | "produtiva"} curva */
  const trilho = (curva) =>
    elemento("div", { classe: "movimento__linha" }, [
      elemento("p", {
        texto: `${t(curva === "mola" ? "catalogo.mola" : "catalogo.produtiva")}, ${duracao}`,
      }),
      elemento("div", { classe: "trilho" }, [
        elemento("span", { classe: `bolinha bolinha--${curva}` }),
      ]),
    ]);

  const botao = elemento("button", {
    classe: "movimento__botao",
    texto: t("catalogo.mover"),
    atributos: { type: "button", "aria-pressed": "false" },
  });
  const bloco = elemento("div", { classe: "movimento" }, [
    trilho("mola"),
    trilho("produtiva"),
    botao,
  ]);
  botao.addEventListener("click", () => {
    const movido = bloco.classList.toggle("movimento--movido");
    botao.setAttribute("aria-pressed", String(movido));
  });

  return secao("movimento", "catalogo.movimento", "catalogo.movimento-explicacao", [bloco]);
}
