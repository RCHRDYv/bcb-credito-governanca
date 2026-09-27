/**
 * PT: Testes de ponta a ponta da página inicial do esqueleto (#65).
 *
 *     Conferem, em cada motor de navegador:
 *     - a acessibilidade pelo axe, nas regras da WCAG 2.2 AA (RNF-04);
 *     - a ausência de rolagem horizontal nas larguras dos pontos de quebra do
 *       Carbon e nos extremos de 360 e 1920 px (RNF-05);
 *     - o idioma da página e o título vindo do arquivo de tradução (RNF-13).
 *
 * EN: End-to-end tests for the skeleton's home page: axe on WCAG 2.2 AA
 *     rules, no horizontal scroll at the Carbon breakpoints and at 360 and
 *     1920 px, and the page language and title.
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

test.beforeEach(async ({ page }) => {
  await page.goto("./");
});

test("a página está em português e com o título do arquivo de tradução", async ({ page }) => {
  await expect(page.locator("html")).toHaveAttribute("lang", "pt-BR");
  await expect(page).toHaveTitle(ptBR["pagina.titulo"]);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(ptBR["inicio.titulo"]);
});

test("o axe não encontra violação da WCAG 2.2 AA", async ({ page }) => {
  const resultado = await new AxeBuilder({ page }).withTags(REGRAS_WCAG).analyze();
  expect(resultado.violations).toEqual([]);
});

for (const largura of LARGURAS) {
  test(`não há rolagem horizontal em ${largura} px`, async ({ page }) => {
    await page.setViewportSize({ width: largura, height: 900 });
    const sobra = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(sobra).toBeLessThanOrEqual(0);
  });
}
