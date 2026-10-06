/**
 * PT: Testes de ponta a ponta dos gráficos do catálogo (#63).
 *
 *     Conferem, no navegador de verdade:
 *     - que cada área de gráfico ganhou um SVG, nos dois painéis de tema;
 *     - que o mesmo gráfico fica com cores diferentes no painel claro e no
 *       escuro, lidas do SVG desenhado;
 *     - que a troca de tema da página muda as cores do gráfico sem recriá-lo:
 *       o identificador da instância do ECharts e o próprio elemento SVG
 *       continuam os mesmos;
 *     - que o axe não acha violação com os gráficos já desenhados, nos dois
 *       esquemas de cor. O teste das páginas roda o axe logo depois de abrir,
 *       quando os gráficos ainda podem estar esperando a fonte.
 *
 *     O mapa depende da malha das UFs, versionada desde a #67. Ela é parte
 *     do site, e o teste exige o mapa desenhado nos dois painéis, sem o
 *     estado de erro da malha.
 *
 * EN: End-to-end chart tests: every chart area renders an SVG in both theme
 *     panels, the same chart differs between panels, and switching the page
 *     theme updates colors on the same ECharts instance and SVG element.
 */

import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

// PT: as mesmas regras do teste das páginas / EN: same rules as the pages test
const REGRAS_WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22a", "wcag22aa"];

/**
 * PT: A cor do traço da série temporal da demonstração, lida do SVG.
 * EN: The demo series stroke color, read from the SVG.
 *
 * @param {import("@playwright/test").Page} page
 * @param {string} seletor
 * @returns {Promise<string | null>}
 */
function tracoDaSerie(page, seletor) {
  return page.locator(seletor).evaluate((el) => {
    const traco = [...el.querySelectorAll("svg path")].find(
      (caminho) =>
        caminho.getAttribute("fill") === "none" && caminho.getAttribute("stroke-width") === "3",
    );
    return traco?.getAttribute("stroke") ?? null;
  });
}

test.describe("gráficos do catálogo", () => {
  test.use({ colorScheme: "light" });

  test.beforeEach(async ({ page }) => {
    await page.goto("./catalogo.html");
    await expect(page.locator('[data-teste="grafico-da-demonstracao"] svg')).toBeVisible();
  });

  test("toda área de gráfico ganha um SVG, inclusive o mapa", async ({ page }) => {
    const areas = page.locator(".grafico");
    const comSvg = page.locator(".grafico:has(svg)");
    await expect(areas.first()).toBeVisible();
    // PT: dois painéis, com oito gráficos cada (a matriz de calor entrou na
    //     #69, e a série com duas medidas na #70), mais a demonstração
    // EN: two panels of eight charts each, plus the demo
    expect(await areas.count()).toBe(17);
    await expect(page.locator(".grafico--mapa svg")).toHaveCount(2);
    expect(await comSvg.count()).toBe(17);
    await expect(page.locator(".grafico-erro")).toHaveCount(0);
  });

  test("o mesmo gráfico tem cores diferentes nos painéis claro e escuro", async ({ page }) => {
    const claro = await tracoDaSerie(page, ".tema--claro .grafico--serie");
    const escuro = await tracoDaSerie(page, ".tema--escuro .grafico--serie");
    expect(claro).not.toBeNull();
    expect(escuro).not.toBeNull();
    expect(claro).not.toBe(escuro);
  });

  test("a troca de tema muda as cores sem recriar o gráfico", async ({ page }) => {
    const grafico = page.locator('[data-teste="grafico-da-demonstracao"]');
    const antes = {
      instancia: await grafico.getAttribute("_echarts_instance_"),
      traco: await tracoDaSerie(page, '[data-teste="grafico-da-demonstracao"]'),
    };
    await grafico.locator("svg").evaluate((svg) => svg.setAttribute("data-marca", "original"));

    await page.getByRole("button", { name: /trocar o tema/i }).click();
    await expect(page.locator("html")).toHaveAttribute("data-tema", "escuro");
    await expect
      .poll(() => tracoDaSerie(page, '[data-teste="grafico-da-demonstracao"]'))
      .not.toBe(antes.traco);

    expect(await grafico.getAttribute("_echarts_instance_")).toBe(antes.instancia);
    await expect(grafico.locator('svg[data-marca="original"]')).toHaveCount(1);
  });
});

for (const esquema of /** @type {const} */ (["light", "dark"])) {
  test.describe(`gráficos do catálogo, com o sistema em ${esquema === "light" ? "claro" : "escuro"}`, () => {
    test.use({ colorScheme: esquema });

    test("o axe não encontra violação com os gráficos desenhados", async ({ page }) => {
      await page.goto("./catalogo.html");
      await expect(page.locator('[data-teste="grafico-da-demonstracao"] svg')).toBeVisible();
      const resultado = await new AxeBuilder({ page }).withTags(REGRAS_WCAG).analyze();
      expect(resultado.violations).toEqual([]);
    });
  });
}
