/**
 * PT: Gera o CSS e a lista dos tokens do design system a partir de `tokens/`
 *     (issue #62, ADRs 0018 e 0020).
 *
 *     Os tokens estão no formato W3C DTCG, em três camadas: primitivo,
 *     semântico e componente. O Style Dictionary lê os arquivos, resolve as
 *     referências e converte as cores; o formato próprio deste script escreve
 *     o CSS. Duas escolhas dele valem registrar:
 *
 *     1. **Referência vira `var()`.** Um token que aponta para outro vira
 *        `var(--outro)` no CSS, e não o valor copiado. Assim, trocar um
 *        primitivo muda a interface inteira, e o DevTools mostra de onde cada
 *        valor vem.
 *     2. **O tema escuro mora na própria cor.** Cada cor semântica com valor
 *        escuro em `$extensions` vira `light-dark(claro, escuro)`, e o tema é
 *        escolhido só pelo `color-scheme` (ADR 0017, decisão 3): segue o
 *        sistema do visitante, pode ser fixado por `data-tema`, e a impressão
 *        sai sempre clara. Sombras e brilhos usam cores semânticas, então
 *        também mudam de tema sem valor próprio.
 *
 *     Gera dois arquivos, versionados e nunca editados à mão:
 *     - `src/estilos/tokens.css`, as variáveis CSS;
 *     - `src/estilos/tokens.json`, a lista resolvida, que o catálogo e o teste
 *       de contraste leem.
 *
 *     Uso:
 *       node scripts/gerar-tokens.js            escreve os dois arquivos
 *       node scripts/gerar-tokens.js --conferir  falha se estiverem desatualizados
 *
 * EN: Generates the design system's CSS and token list from `tokens/` (DTCG,
 *     three layers). References become `var()`, so changing a primitive
 *     changes the whole interface, and each semantic color with a dark value
 *     becomes `light-dark(light, dark)`, with the theme picked by
 *     `color-scheme` alone. `--conferir` fails when the committed files are
 *     out of date, which is what CI runs.
 */

import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import StyleDictionary from "style-dictionary";

const RAIZ = fileURLToPath(new URL("..", import.meta.url));
const DESTINO_CSS = "src/estilos/tokens.css";
const DESTINO_JSON = "src/estilos/tokens.json";

/** PT: chave das extensões deste projeto nos tokens / EN: this project's extension key */
const EXTENSAO = "credito-pj";

const CABECALHO = `/*
 * PT: Gerado por scripts/gerar-tokens.js a partir de dashboard/tokens/. Não edite
 *     à mão: mude o token e rode \`npm run tokens\`. O CI reprova este arquivo
 *     quando ele diverge dos tokens.
 * EN: Generated from dashboard/tokens/. Do not edit by hand.
 */
`;

/**
 * @typedef {import("style-dictionary/types").TransformedToken} Token
 * @typedef {{ value: number, unit: string }} Medida
 */

// -----------------------------------------------------------------------------
// PT: Nomes e referências
// EN: Names and references
// -----------------------------------------------------------------------------

/**
 * PT: Nome da variável CSS a partir do caminho do token.
 * EN: CSS variable name from the token path.
 *
 * @param {string[]} caminho
 * @returns {string}
 */
function variavel(caminho) {
  return `--${caminho.join("-")}`;
}

/**
 * PT: Diz se o valor é uma referência DTCG, como `{color.gray.10}`.
 * EN: Whether a value is a DTCG reference.
 *
 * @param {unknown} valor
 * @returns {valor is string}
 */
function ehReferencia(valor) {
  return typeof valor === "string" && /^\{[^{}]+\}$/.test(valor);
}

/**
 * PT: Converte a referência `{a.b.c}` em `var(--a-b-c)`.
 * EN: Turns a `{a.b.c}` reference into `var(--a-b-c)`.
 *
 * @param {string} referencia
 * @returns {string}
 */
function referenciaParaVar(referencia) {
  return `var(${variavel(referencia.slice(1, -1).split("."))})`;
}

// -----------------------------------------------------------------------------
// PT: Valores em CSS
// EN: CSS values
// -----------------------------------------------------------------------------

/**
 * PT: Uma parte de um valor composto: referência vira `var()`, medida vira
 *     número com unidade, e o resto passa como texto.
 * EN: One part of a composite value.
 *
 * @param {unknown} parte
 * @returns {string}
 */
function parteCss(parte) {
  if (ehReferencia(parte)) {
    return referenciaParaVar(parte);
  }
  if (parte && typeof parte === "object" && "value" in parte && "unit" in parte) {
    const medida = /** @type {Medida} */ (parte);
    return `${medida.value}${medida.unit}`;
  }
  return String(parte);
}

/**
 * PT: Uma sombra DTCG em CSS, com `inset` quando for o caso.
 * EN: A DTCG shadow as CSS.
 *
 * @param {Record<string, unknown>} sombra
 * @returns {string}
 */
function sombraCss(sombra) {
  const partes = ["offsetX", "offsetY", "blur", "spread", "color"].map((chave) =>
    parteCss(sombra[chave]),
  );
  return (sombra.inset ? ["inset", ...partes] : partes).join(" ");
}

/**
 * PT: O valor CSS de um token. Primitivos saem como o Style Dictionary os
 *     converteu; referências e compostos saem com `var()`.
 * EN: A token's CSS value. Primitives come as converted; references and
 *     composites use `var()`.
 *
 * @param {Token} token
 * @returns {string}
 */
function valorCss(token) {
  const original = token.original.$value;
  if (ehReferencia(original)) {
    return referenciaParaVar(original);
  }
  switch (token.$type) {
    case "shadow":
      return (Array.isArray(original) ? original : [original]).map(sombraCss).join(", ");
    case "typography":
      return `${parteCss(original.fontWeight)} ${parteCss(original.fontSize)}/${parteCss(original.lineHeight)} ${parteCss(original.fontFamily)}`;
    case "dimension":
    case "duration":
    case "number":
    case "fontWeight":
      return parteCss(original);
    case "cubicBezier":
      // PT: a mola é uma função linear() guardada em $extensions (o DTCG não a descreve)
      // EN: the spring is a linear() function kept in $extensions
      return token.original.$extensions?.[EXTENSAO]?.css ?? String(token.$value);
    default:
      return String(token.$value);
  }
}

/**
 * PT: A declaração CSS do token, com o `light-dark()` quando há valor escuro,
 *     e a variável extra de espaçamento entre letras na tipografia.
 * EN: The token's CSS declaration(s).
 *
 * @param {Token} token
 * @returns {string[]}
 */
function declaracoes(token) {
  const nome = variavel(token.path);
  const escuro = token.original.$extensions?.[EXTENSAO]?.escuro;
  const valor = ehReferencia(escuro)
    ? `light-dark(${valorCss(token)}, ${referenciaParaVar(escuro)})`
    : valorCss(token);
  const linhas = [`${nome}: ${valor};`];
  if (token.$type === "typography") {
    linhas.push(`${nome}-letter-spacing: ${parteCss(token.original.$value.letterSpacing)};`);
  }
  return linhas;
}

/**
 * PT: A camada do token, pela pasta do arquivo de onde ele veio.
 * EN: The token's layer, from its source folder.
 *
 * @param {Token} token
 * @returns {"primitivo" | "semantico" | "componente"}
 */
function camada(token) {
  const arquivo = token.filePath.replaceAll("\\", "/");
  if (arquivo.includes("/componentes/")) return "componente";
  if (arquivo.includes("/semanticos/")) return "semantico";
  return "primitivo";
}

// -----------------------------------------------------------------------------
// PT: Formatos
// EN: Formats
// -----------------------------------------------------------------------------

/**
 * PT: O tokens.css: as variáveis por camada, a escolha do tema pelo
 *     `color-scheme` e a alternativa para a mola.
 * EN: tokens.css: variables by layer, theme choice through `color-scheme`, and
 *     the spring fallback.
 *
 * @param {{ dictionary: { allTokens: Token[] } }} argumentos
 * @returns {string}
 */
function formatoCss({ dictionary }) {
  const blocos = ["primitivo", "semantico", "componente"].map((qual) => {
    const linhas = dictionary.allTokens
      .filter((token) => camada(token) === qual)
      .flatMap(declaracoes)
      .map((linha) => `    ${linha}`);
    return `    /* ${qual} */\n${linhas.join("\n")}`;
  });

  return `${CABECALHO}
@layer tokens {
  :root {
    /* PT: segue o sistema do visitante; claro quando o sistema não diz nada */
    /* EN: follows the visitor's system; light when it states no preference */
    color-scheme: light dark;

${blocos.join("\n\n")}
  }

  /* PT: escolha fixa do tema, se um dia houver botão de troca */
  /* EN: a fixed theme choice, should a switch ever exist */
  :root[data-tema="claro"] {
    color-scheme: light;
  }

  :root[data-tema="escuro"] {
    color-scheme: dark;
  }

  /* PT: impressão e PDF sempre claros (RF-G09) / EN: print is always light */
  @media print {
    :root,
    :root[data-tema] {
      color-scheme: light;
    }
  }

  /* PT: sem linear(), a mola vira a curva produtiva do Carbon */
  /* EN: without linear(), the spring falls back to Carbon's productive curve */
  @supports not (transition-timing-function: linear(0, 1)) {
    :root {
      --easing-mola: var(--easing-produtiva);
    }
  }
}
`;
}

/**
 * PT: A cor final de um token num tema, seguindo a cadeia de referências até
 *     o primitivo. No escuro, o primeiro token da cadeia que tiver valor
 *     escuro em `$extensions` desvia a cadeia para ele. Assim, um token de
 *     componente que aponta para uma cor semântica herda o escuro dela.
 * EN: A token's final color in a theme, following the reference chain to the
 *     primitive; in dark, the first token with a dark extension redirects it.
 *
 * @param {Token | undefined} token
 * @param {"claro" | "escuro"} tema
 * @param {Map<string, Token>} porCaminho
 * @returns {{ hex: string, alpha: number }}
 */
function corNoTema(token, tema, porCaminho) {
  if (!token) {
    throw new Error("Referência de cor que não leva a nenhum token");
  }
  const escuro = token.original.$extensions?.[EXTENSAO]?.escuro;
  const proximo = tema === "escuro" && ehReferencia(escuro) ? escuro : token.original.$value;
  if (ehReferencia(proximo)) {
    // PT: depois do primeiro desvio, o resto da cadeia é o valor do próprio primitivo
    // EN: past the first redirect, the rest of the chain is the primitive's own value
    const seguinte = porCaminho.get(proximo.slice(1, -1));
    return corNoTema(seguinte, proximo === escuro ? "claro" : tema, porCaminho);
  }
  if (!proximo || typeof proximo !== "object" || !("hex" in proximo)) {
    throw new Error(`Cor sem valor no fim da cadeia: ${token.path.join(".")}`);
  }
  return { hex: proximo.hex, alpha: proximo.alpha ?? 1 };
}

/**
 * PT: O tokens.json: a lista resolvida, com as cores dos dois temas.
 * EN: tokens.json: the resolved list, with both themes' colors.
 *
 * @param {{ dictionary: { allTokens: Token[] } }} argumentos
 * @returns {string}
 */
function formatoJson({ dictionary }) {
  const porCaminho = new Map(dictionary.allTokens.map((t) => [t.path.join("."), t]));
  const lista = dictionary.allTokens.map((token) => {
    const caminho = token.path.join(".");
    /** @type {Record<string, unknown>} */
    const item = {
      caminho,
      variavel: variavel(token.path),
      tipo: token.$type,
      camada: camada(token),
      descricao: token.$description ?? null,
      css: valorCss(token),
    };
    if (token.$type === "color") {
      item.claro = corNoTema(token, "claro", porCaminho);
      item.escuro = corNoTema(token, "escuro", porCaminho);
    }
    return item;
  });
  return `${JSON.stringify(lista, null, 2)}\n`;
}

// -----------------------------------------------------------------------------
// PT: Execução
// EN: Run
// -----------------------------------------------------------------------------

StyleDictionary.registerFormat({ name: "credito-pj/css", format: formatoCss });
StyleDictionary.registerFormat({ name: "credito-pj/json", format: formatoJson });

/**
 * PT: Monta o Style Dictionary e devolve o texto dos dois arquivos.
 * EN: Builds the Style Dictionary and returns both files' text.
 *
 * @returns {Promise<Map<string, string>>}
 */
async function gerar() {
  const sd = new StyleDictionary({
    // PT: o glob pede barras normais, também no Windows / EN: globs need forward slashes
    source: [`${RAIZ.replaceAll("\\", "/")}tokens/**/*.tokens.json`],
    usesDtcg: true,
    log: { verbosity: "silent" },
    platforms: {
      web: {
        transforms: ["color/css", "fontFamily/css", "cubicBezier/css"],
        files: [
          { destination: DESTINO_CSS, format: "credito-pj/css" },
          { destination: DESTINO_JSON, format: "credito-pj/json" },
        ],
      },
    },
  });
  const saidas = await sd.formatPlatform("web");
  return new Map(saidas.map((s) => [String(s.destination), String(s.output)]));
}

async function main() {
  const conferir = process.argv.includes("--conferir");
  const saidas = await gerar();
  const desatualizados = [];

  for (const [destino, conteudo] of saidas) {
    const caminho = join(RAIZ, destino);
    if (conferir) {
      const atual = await readFile(caminho, "utf8").catch(() => "");
      if (atual.replaceAll("\r\n", "\n") !== conteudo) {
        desatualizados.push(destino);
      }
    } else {
      await writeFile(caminho, conteudo, "utf8");
      console.log(`Escrito: ${destino}`);
    }
  }

  if (desatualizados.length > 0) {
    console.error(
      `Tokens desatualizados: ${desatualizados.join(", ")}. Rode \`npm run tokens\` e versione o resultado.`,
    );
    process.exit(1);
  }
  if (conferir) {
    console.log("Tokens em dia com o CSS versionado.");
  }
}

await main();
