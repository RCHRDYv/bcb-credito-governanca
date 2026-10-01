/**
 * PT: Testes de ponta a ponta da política de segurança de conteúdo e do que o
 *     build publica (#68, RNF-10 e RNF-11).
 *
 *     Conferem, no site construído, que é o que vai para o Pages:
 *     - que as duas páginas trazem a política de `politica-de-seguranca.js`
 *       no `<meta>`;
 *     - que nenhuma página viola a política ao abrir, nos dois esquemas de
 *       cor. No catálogo, o teste espera os gráficos e o mapa desenhados e
 *       troca o tema da página, porque o ECharts é a peça que mais mexe em
 *       estilo, e a troca de tema repinta os gráficos;
 *     - o controle negativo: um script e uma folha de estilo embutidos,
 *       injetados pelo teste, são bloqueados. Sem ele, uma política que não
 *       estivesse valendo passaria em silêncio no teste anterior;
 *     - que o `dist/` só tem os arquivos do site, e nada do experimento.
 *
 * EN: End-to-end tests for the content security policy and the published
 *     files: both pages carry the policy, no page violates it on load in
 *     either color scheme, injected inline script and style are blocked (the
 *     negative control), and `dist/` holds only the site's files.
 */

import { readdirSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";
import { POLITICA } from "../../politica-de-seguranca.js";

const PAGINAS = [
  { onde: "a página inicial", caminho: "./", pronta: "main", trocaOTema: false },
  {
    onde: "o catálogo",
    caminho: "./catalogo.html",
    pronta: ".grafico--mapa svg",
    trocaOTema: true,
  },
];

/**
 * @typedef {Window & { violacoes?: string[] }} JanelaVigiada
 */

/**
 * PT: Passa a anotar, desde antes do primeiro script da página, toda
 *     violação da política que o navegador relatar.
 * EN: Records every policy violation the browser reports, from before the
 *     page's first script.
 *
 * @param {import("@playwright/test").Page} page
 * @returns {Promise<void>}
 */
async function vigiarViolacoes(page) {
  await page.addInitScript(() => {
    const janela = /** @type {JanelaVigiada} */ (window);
    janela.violacoes = [];
    document.addEventListener("securitypolicyviolation", (evento) => {
      janela.violacoes?.push(`${evento.effectiveDirective}: ${evento.blockedURI || "embutido"}`);
    });
  });
}

/**
 * PT: As violações anotadas até agora.
 * EN: The violations recorded so far.
 *
 * @param {import("@playwright/test").Page} page
 * @returns {Promise<string[]>}
 */
function violacoes(page) {
  return page.evaluate(() => /** @type {JanelaVigiada} */ (window).violacoes ?? []);
}

test.describe("política de segurança de conteúdo", () => {
  for (const { onde, caminho, pronta, trocaOTema } of PAGINAS) {
    test(`${onde} traz a política no <meta>`, async ({ page }) => {
      await page.goto(caminho);
      const meta = page.locator('meta[http-equiv="Content-Security-Policy"]');
      await expect(meta).toHaveCount(1);
      await expect(meta).toHaveAttribute("content", POLITICA);
    });

    for (const esquema of /** @type {const} */ (["light", "dark"])) {
      test(`${onde} abre sem violar a política, com o sistema em ${esquema === "light" ? "claro" : "escuro"}`, async ({
        page,
      }) => {
        await page.emulateMedia({ colorScheme: esquema });
        await vigiarViolacoes(page);
        await page.goto(caminho);
        await expect(page.locator(pronta).first()).toBeVisible();
        if (trocaOTema) {
          const antes = await page.locator("html").getAttribute("data-tema");
          await page.getByRole("button", { name: /trocar o tema/i }).click();
          await expect(page.locator("html")).not.toHaveAttribute("data-tema", antes ?? "");
        }
        await page.waitForLoadState("networkidle");
        expect(await violacoes(page)).toEqual([]);
      });
    }
  }

  test("controle negativo: script e estilo embutidos são bloqueados", async ({ page }) => {
    await vigiarViolacoes(page);
    await page.goto("./");
    await expect(page.locator("main")).toBeVisible();

    const resultado = await page.evaluate(() => {
      const script = document.createElement("script");
      script.textContent = "document.documentElement.dataset.injetado = 'sim'";
      document.head.append(script);

      const estilo = document.createElement("style");
      estilo.textContent = "body { outline: 7px solid rgb(255, 0, 0); }";
      document.head.append(estilo);

      return {
        scriptRodou: document.documentElement.dataset.injetado === "sim",
        contorno: getComputedStyle(document.body).outlineWidth,
      };
    });

    expect(resultado.scriptRodou).toBe(false);
    expect(resultado.contorno).not.toBe("7px");
    await expect
      .poll(() => violacoes(page))
      .toEqual(
        expect.arrayContaining([
          expect.stringContaining("script-src"),
          expect.stringContaining("style-src"),
        ]),
      );
  });
});

test.describe("o que o build publica", () => {
  // PT: Lê o disco, e não o navegador, então basta um motor.
  // EN: Reads the disk, not the browser, so one engine is enough.
  test.skip(({ browserName }) => browserName !== "chromium", "confere o disco, não o navegador");

  test("o dist só tem os arquivos do site, e nada do experimento", () => {
    const dist = fileURLToPath(new URL("../../dist/", import.meta.url));
    const arquivos = readdirSync(dist, { recursive: true, withFileTypes: true })
      .filter((entrada) => entrada.isFile())
      .map((entrada) =>
        relative(dist, join(entrada.parentPath, entrada.name)).replaceAll("\\", "/"),
      );

    // PT: as duas páginas, os arquivos servidos como estão, o que o Vite
    //     gera em assets/, os dados do contrato e a malha das UFs
    // EN: both pages, files served as is, Vite's assets, contract data and the mesh
    const permitido =
      /^(index\.html|catalogo\.html|favicon\.svg|tema-inicial\.js|assets\/[\w-]+\.(js|css|woff2)|data\/[a-z_]+\.json|geo\/ufs\.json)$/;
    expect(arquivos.length).toBeGreaterThan(0);
    expect(arquivos.filter((arquivo) => !permitido.test(arquivo))).toEqual([]);
    expect(arquivos.filter((arquivo) => /evaluation|gabarito|questions/i.test(arquivo))).toEqual(
      [],
    );
  });
});
