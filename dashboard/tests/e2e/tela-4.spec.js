/**
 * PT: Testes de ponta a ponta da Tela 4 (#71), no site construído.
 *
 *     Conferem os requisitos da visão e os gerais:
 *     - a navegação leva à Tela 4 e marca a visão atual (RF-G01);
 *     - o custo de errar e a carteira por quadrante são os de
 *       `docs/recomendacao.md` (RF-402);
 *     - as células fora da matriz aparecem com quantas são, quanto somam e
 *       por quê (RF-403);
 *     - todo quadrante aparece com ícone e rótulo, e nunca só com a cor
 *       (RF-404);
 *     - a tabela tem as 147 células avaliadas e baixa o CSV (RF-G06).
 *
 * EN: End-to-end tests for Screen 4: navigation, cost of being wrong,
 *     quadrant bars, cells left out, quadrant tags, table and CSV.
 */

import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";
import { ptBR } from "../../src/textos/pt-BR.js";

test.use({ viewport: { width: 1536, height: 864 } });

const ENDERECO = "./#/recomendacao";

/**
 * PT: Abre a Tela 4 e espera a matriz desenhar.
 * EN: Opens Screen 4 and waits for the matrix to draw.
 *
 * @param {import("@playwright/test").Page} page
 */
async function abrir(page) {
  await page.goto(ENDERECO);
  await expect(page.locator(".visao--recomendacao .grafico--matriz svg").first()).toBeVisible();
}

test("a navegação leva à Tela 4 e marca a visão atual", async ({ page }) => {
  await page.goto("./");
  await page.getByRole("link", { name: ptBR["navegacao.recomendacao"] }).click();
  await expect(page.locator(".visao--recomendacao .grafico--matriz svg").first()).toBeVisible();
  await expect(page.locator('.navegacao [aria-current="page"]')).toHaveText(
    ptBR["navegacao.recomendacao"],
  );
  await expect(page).toHaveTitle(`${ptBR["navegacao.recomendacao"]} · ${ptBR["produto.nome"]}`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(ptBR["tela4.titulo"]);
});

test("o custo de errar e os quadrantes são os do relatório", async ({ page }) => {
  await abrir(page);
  const custos = page.locator(".recomendacao__custo-valor");
  await expect(custos.nth(0)).toHaveText("R$ 141,1 bi");
  await expect(custos.nth(1)).toHaveText("R$ 7,2 bi");
  const barras = page.locator(".recomendacao__barras li");
  await expect(barras).toHaveCount(4);
  await expect(barras.nth(0)).toContainText("R$ 485,5 bi");
  await expect(barras.nth(0)).toContainText("35 células");
  await expect(barras.nth(3)).toContainText("R$ 1,4 tri");
  await expect(page.locator(".recomendacao__fora")).toContainText("162 células, R$ 44,2 bi");
});

test("todo quadrante tem ícone e rótulo", async ({ page }) => {
  await abrir(page);
  for (const chave of /** @type {const} */ (["entrar", "observar", "nao-entrar", "manter"])) {
    const etiquetas = page.locator(`.visao--recomendacao .etiqueta--${chave}`);
    await expect(etiquetas.first()).toContainText(ptBR[`quadrante.${chave}`]);
    await expect(etiquetas.first().locator("svg")).toHaveCount(1);
  }
});

test("a tabela tem as células avaliadas e baixa o CSV", async ({ page }) => {
  await abrir(page);
  await page.locator('.visao__filtros [data-valor="tabela"]').click();
  await expect(page.locator(".visao__tabela tbody tr")).toHaveCount(147);
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: ptBR["tela1.baixar-csv"] }).click(),
  ]);
  expect(download.suggestedFilename()).toBe("recomendacao-credito-pj-2026-07-31.csv");
  const conteudo = readFileSync(/** @type {string} */ (await download.path()), "utf8");
  expect(conteudo.trim().split(/\r?\n/)).toHaveLength(1 + 147);
});
