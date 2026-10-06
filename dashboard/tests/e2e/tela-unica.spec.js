/**
 * PT: Testes de ponta a ponta da tela única (ADR 0022, RNF-15, #87).
 *
 *     Conferem, em cada motor de navegador:
 *     - que, a partir de uma janela de 1280×720 px, a Tela 1 cabe sem
 *       rolagem da página, em cada forma do território, e que os gráficos
 *       ficam com altura útil;
 *     - que, abaixo do piso, a página rola e nenhum bloco fica por cima de
 *       outro;
 *     - que o gráfico acompanha quando a janela muda de tamanho.
 *
 *     As janelas são as de um notebook Full HD: a 100% de escala, cerca de
 *     1920×950 maximizada e 1920×1080 em tela cheia; a 125%, 1536×730 e
 *     1536×864; e o piso, 1280×720.
 *
 * EN: End-to-end tests for the single screen: from a 1280×720 window up,
 *     Screen 1 fits with no page scroll in every territory form; below the
 *     floor the page scrolls with no overlapping blocks; charts follow
 *     window resizes.
 */

import { expect, test } from "@playwright/test";

const ACIMA_DO_PISO = [
  { width: 1280, height: 720 },
  { width: 1536, height: 730 },
  { width: 1536, height: 864 },
  { width: 1920, height: 950 },
  { width: 1920, height: 1080 },
];

const ABAIXO_DO_PISO = [
  { width: 1280, height: 600 },
  { width: 1100, height: 900 },
];

const FORMAS = ["mapa", "grade", "matriz", "tabela"];

// PT: a menor altura em que o desenho do território ainda se lê, em px
// EN: the smallest height at which the territory drawing still reads
const ALTURA_UTIL = 240;

/**
 * PT: Abre a Tela 1 e espera o território desenhar.
 * EN: Opens Screen 1 and waits for the territory to draw.
 *
 * @param {import("@playwright/test").Page} page
 */
async function abrir(page) {
  await page.goto("./");
  await expect(page.locator(".visao__forma svg").first()).toBeVisible();
}

/**
 * PT: Quanto a página passa da janela, em px.
 * EN: How far the page overflows the window, in px.
 *
 * @param {import("@playwright/test").Page} page
 * @returns {Promise<number>}
 */
function sobraVertical(page) {
  return page.evaluate(
    () => document.documentElement.scrollHeight - document.documentElement.clientHeight,
  );
}

for (const janela of ACIMA_DO_PISO) {
  test.describe(`numa janela de ${janela.width}×${janela.height}`, () => {
    test.use({ viewport: janela });

    for (const forma of FORMAS) {
      test(`a Tela 1 cabe sem rolagem da página, com ${forma}`, async ({ page }) => {
        await abrir(page);
        await page.locator(`.visao__filtros [data-valor="${forma}"]`).click();
        if (forma === "tabela") {
          await expect(page.locator(".visao__tabela")).toBeVisible();
        } else {
          await expect(page.locator(".visao__forma svg").first()).toBeVisible();
        }
        expect(await sobraVertical(page)).toBeLessThanOrEqual(0);
        const altura = await page
          .locator(".visao__forma")
          .evaluate((el) => el.getBoundingClientRect().height);
        expect(altura).toBeGreaterThanOrEqual(ALTURA_UTIL);
      });
    }

    test("o painel rola por dentro, sem alongar a página", async ({ page }) => {
      await abrir(page);
      await page.locator('.visao__filtros [data-valor="tabela"]').click();
      await page.locator('[data-uf="MG"]').click();
      await expect(page.locator(".detalhe__titulo")).toHaveText("Minas Gerais");
      expect(await sobraVertical(page)).toBeLessThanOrEqual(0);
    });
  });
}

for (const janela of ABAIXO_DO_PISO) {
  test.describe(`abaixo do piso, em ${janela.width}×${janela.height}`, () => {
    test.use({ viewport: janela });

    test("nenhum bloco da Tela 1 fica por cima de outro", async ({ page }) => {
      await abrir(page);
      const sobrepostos = await page.evaluate(() => {
        const caixas = [...document.querySelectorAll(".visao > *")]
          .filter((el) => getComputedStyle(el).display !== "none")
          .filter((el) => !el.classList.contains("visualmente-oculto"))
          .map((el) => ({ nome: el.className, caixa: el.getBoundingClientRect() }));
        /** @type {string[][]} */
        const pares = [];
        for (const [i, a] of caixas.entries()) {
          for (const b of caixas.slice(i + 1)) {
            const cruza =
              a.caixa.left < b.caixa.right - 1 &&
              b.caixa.left < a.caixa.right - 1 &&
              a.caixa.top < b.caixa.bottom - 1 &&
              b.caixa.top < a.caixa.bottom - 1;
            if (cruza) pares.push([a.nome, b.nome]);
          }
        }
        return pares;
      });
      expect(sobrepostos).toEqual([]);
    });
  });
}

test("abaixo do piso, a página volta a rolar", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 600 });
  await abrir(page);
  expect(await sobraVertical(page)).toBeGreaterThan(0);
});

test("o mapa acompanha quando a janela cresce", async ({ page }) => {
  await page.setViewportSize({ width: 1536, height: 730 });
  await abrir(page);
  const mapa = page.locator(".grafico--mapa svg");
  const antes = await mapa.evaluate((el) => el.getBoundingClientRect().height);
  await page.setViewportSize({ width: 1920, height: 1080 });
  await expect
    .poll(() => mapa.evaluate((el) => el.getBoundingClientRect().height))
    .toBeGreaterThan(antes + 100);
});
