/**
 * PT: A política de segurança de conteúdo do site (#68, RNF-11), num lugar só.
 *
 *     O GitHub Pages não deixa configurar cabeçalho HTTP, então a política vai
 *     num `<meta>` do HTML (ADR 0016, decisão 1). O texto mora aqui, e não no
 *     HTML, por dois motivos:
 *     - o build a injeta no `index.html` e no `catalogo.html`, e só no build:
 *       o modo de desenvolvimento do Vite põe o CSS em elementos `<style>`,
 *       que a política bloquearia;
 *     - os testes de ponta a ponta comparam a política publicada com esta,
 *       sem uma cópia do texto para envelhecer.
 *
 *     As diretivas são as da arquitetura (docs/dashboard/arquitetura.md). A
 *     única exceção ao "só do próprio site" é o `style-src-attr`, porque o
 *     ECharts aplica estilo pelo atributo `style`, e estilo em atributo não
 *     executa script. Na v0.3, o chat acrescenta ao `connect-src` o
 *     huggingface.co e o endereço do Space (#51 e #73).
 *
 * EN: The site's content security policy, in one place. GitHub Pages allows
 *     no custom HTTP headers, so the policy goes in a `<meta>`. The build
 *     injects it, only in the build, because Vite's dev mode puts CSS in
 *     `<style>` elements; end-to-end tests compare the published policy with
 *     this one. The only exception to same-origin is `style-src-attr`, which
 *     ECharts needs.
 */

/**
 * PT: Cada diretiva com as fontes que ela aceita, na ordem da arquitetura.
 * EN: Each directive with its allowed sources, in the architecture's order.
 *
 * @type {ReadonlyArray<readonly [string, string]>}
 */
export const DIRETIVAS = [
  ["default-src", "'none'"],
  ["script-src", "'self'"],
  ["style-src", "'self'"],
  ["style-src-attr", "'unsafe-inline'"],
  ["img-src", "'self'"],
  ["font-src", "'self'"],
  ["connect-src", "'self'"],
  ["base-uri", "'self'"],
  ["form-action", "'none'"],
];

/**
 * PT: A política como vai no atributo `content` do `<meta>`.
 * EN: The policy as it goes in the `<meta>` content attribute.
 */
export const POLITICA = DIRETIVAS.map(([diretiva, fontes]) => `${diretiva} ${fontes}`).join("; ");

/**
 * PT: O ponto do HTML depois do qual a política entra. Ela precisa vir antes
 *     de qualquer script ou folha de estilo para valer para eles, e o
 *     `charset` continua sendo o primeiro elemento do `<head>`.
 * EN: The HTML anchor after which the policy goes: before any script or
 *     stylesheet, with `charset` still first in `<head>`.
 */
const ANCORA = '<meta charset="utf-8" />';

/**
 * PT: Põe a política logo depois do `charset`. Falha se a página não tiver
 *     a âncora, para nenhuma página sair publicada sem a política.
 * EN: Inserts the policy right after `charset`; fails when the anchor is
 *     missing, so no page ships without it.
 *
 * @param {string} html
 * @returns {string}
 */
export function comPolitica(html) {
  if (!html.includes(ANCORA)) {
    throw new Error(`Página sem ${ANCORA}: a política de segurança não tem onde entrar`);
  }
  return html.replace(
    ANCORA,
    `${ANCORA}\n    <meta http-equiv="Content-Security-Policy" content="${POLITICA}" />`,
  );
}

/**
 * PT: O plugin do Vite que aplica `comPolitica()` em toda página do build.
 * EN: The Vite plugin applying `comPolitica()` to every built page.
 *
 * @returns {import("vite").Plugin}
 */
export function politicaDeSeguranca() {
  return {
    name: "politica-de-seguranca",
    apply: "build",
    transformIndexHtml: (html) => comPolitica(html),
  };
}
