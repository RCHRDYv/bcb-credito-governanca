/**
 * PT: Testes de ponta a ponta das páginas do site (#65 e #62).
 *
 *     Conferem, em cada motor de navegador e nos dois esquemas de cor do
 *     sistema:
 *     - a acessibilidade pelo axe, nas regras da WCAG 2.2 AA (RNF-04);
 *     - a ausência de rolagem horizontal nas larguras do RNF-05;
 *     - que o tema segue o sistema, e que a impressão sai sempre clara;
 *     - o idioma e o título vindos do arquivo de tradução (RNF-13).
 *
 * EN: End-to-end tests for the site's pages, in every engine and both system
 *     color schemes: axe on WCAG 2.2 AA, no horizontal scroll, the theme
 *     following the system with print always light, and language and title.
 */

import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { ptBR } from "../../src/textos/pt-BR.js";

// PT: regras do axe que correspondem à WCAG 2.2 nos níveis A e AA
// EN: axe rule tags matching WCAG 2.2 levels A and AA
const REGRAS_WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22a", "wcag22aa"];

// PT: 360 e 1920 são os extremos do RNF-05; os outros são os pontos de quebra do Carbon
// EN: 360 and 1920 are RNF-05's extremes; the others are Carbon breakpoints
const LARGURAS = [360, 672, 1056, 1312, 1920];

const PAGINAS = [
  { onde: "na página inicial", caminho: "./" },
  { onde: "no catálogo", caminho: "./catalogo.html" },
];

// PT: o fundo da página em cada tema, como o navegador o calcula
// EN: the page background in each theme, as the browser computes it
const FUNDO = { light: "rgb(244, 244, 244)", dark: "rgb(22, 22, 22)" };

test("a página inicial está em português e com o título do arquivo de tradução", async ({
  page,
}) => {
  await page.goto("./");
  await expect(page.locator("html")).toHaveAttribute("lang", "pt-BR");
  // PT: o endereço abre na Tela 1, e o título é o da visão aberta (#69)
  // EN: the address opens on Screen 1, titled after the open view
  await expect(page).toHaveTitle(`${ptBR["navegacao.credito-por-uf"]} · ${ptBR["produto.nome"]}`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(ptBR["tela1.titulo"]);
});

for (const esquema of /** @type {const} */ (["light", "dark"])) {
  test.describe(`com o sistema em ${esquema === "light" ? "claro" : "escuro"}`, () => {
    test.use({ colorScheme: esquema });

    test("o tema segue o sistema", async ({ page }) => {
      await page.goto("./");
      await expect(page.locator("html")).toHaveCSS("background-color", FUNDO[esquema]);
    });

    test("a impressão sai sempre clara", async ({ page }) => {
      await page.goto("./");
      await page.emulateMedia({ media: "print" });
      await expect(page.locator("html")).toHaveCSS("background-color", FUNDO.light);
    });

    for (const pagina of PAGINAS) {
      test(`o axe não encontra violação ${pagina.onde}`, async ({ page }) => {
        await page.goto(pagina.caminho);
        const resultado = await new AxeBuilder({ page }).withTags(REGRAS_WCAG).analyze();
        expect(resultado.violations).toEqual([]);
      });

      for (const largura of LARGURAS) {
        test(`não há rolagem horizontal ${pagina.onde} em ${largura} px`, async ({ page }) => {
          await page.setViewportSize({ width: largura, height: 900 });
          await page.goto(pagina.caminho);
          const sobra = await page.evaluate(
            () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
          );
          expect(sobra).toBeLessThanOrEqual(0);
        });
      }
    }
  });
}
