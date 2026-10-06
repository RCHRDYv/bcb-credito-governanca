/**
 * PT: Testes de ponta a ponta da Tela 3 (#72), no site construído.
 *
 *     Conferem os requisitos da visão e os gerais:
 *     - a navegação leva à Tela 3 e marca a visão atual (RF-G01);
 *     - a projeção do Brasil, mês a mês, é a de `docs/previsao.md` (RF-301);
 *     - escolher a série muda o título, o método e o erro, e a ressalva da
 *       mudança de patamar aparece só nas cinco séries que mudaram (RF-302);
 *     - o período muda o realizado, e não a projeção;
 *     - escolher a data do teste muda o título do cartão do erro;
 *     - a tabela tem uma linha por mês e baixa o CSV (RF-G06).
 *
 * EN: End-to-end tests for Screen 3: navigation, Brazil's forecast, series,
 *     period and test-date choices, the level-change caveat, table and CSV.
 */

import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";
import { ptBR } from "../../src/textos/pt-BR.js";

test.use({ viewport: { width: 1536, height: 864 } });

const ENDERECO = "./#/projecao";

/**
 * PT: Abre a Tela 3 e espera a série desenhar.
 * EN: Opens Screen 3 and waits for the series to draw.
 *
 * @param {import("@playwright/test").Page} page
 */
async function abrir(page) {
  await page.goto(ENDERECO);
  await expect(page.locator(".visao--projecao .visao__forma svg").first()).toBeVisible();
}

/**
 * PT: Escolhe uma série pelo campo de seleção.
 * EN: Picks a series in the select field.
 *
 * @param {import("@playwright/test").Page} page
 * @param {string} chave
 */
function escolherSerie(page, chave) {
  return page.locator(".visao--projecao .visao__filtros select").selectOption(chave);
}

test("a navegação leva à Tela 3 e marca a visão atual", async ({ page }) => {
  await page.goto("./");
  await page.getByRole("link", { name: ptBR["navegacao.projecao"] }).click();
  await expect(page.locator(".visao--projecao .visao__forma svg").first()).toBeVisible();
  await expect(page.locator('.navegacao [aria-current="page"]')).toHaveText(
    ptBR["navegacao.projecao"],
  );
  await expect(page).toHaveTitle(`${ptBR["navegacao.projecao"]} · ${ptBR["produto.nome"]}`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(ptBR["tela3.titulo"]);
});

test("a projeção do Brasil é a do relatório", async ({ page }) => {
  await abrir(page);
  const linhas = page.locator(".projecao__mes-a-mes tbody tr");
  await expect(linhas).toHaveCount(3);
  await expect(linhas.nth(0)).toContainText("R$ 2,93 tri");
  await expect(linhas.nth(0)).toContainText("2,88 a 2,97 tri");
  await expect(linhas.nth(2)).toContainText("R$ 2,96 tri");
  await expect(linhas.nth(2)).toContainText("2,87 a 3,04 tri");
  await expect(page.locator(".visao__resumo")).toContainText(ptBR["tela3.modelo.deriva"]);
  await expect(page.locator(".projecao__frase")).toContainText("0,65%");
  await expect(page.locator(".projecao__frase")).toContainText("1,03%");
});

test("escolher a série muda o título e o método, e a ressalva só aparece onde vale", async ({
  page,
}) => {
  await abrir(page);
  const ressalva = page.getByText(ptBR["tela3.aviso-mudanca-de-nivel"]);
  await expect(ressalva).toHaveCount(0);

  await escolherSerie(page, "uf:SC");
  await expect(page.locator(".visao__sobre-o-territorio .cartao-grafico__titulo")).toContainText(
    "Santa Catarina",
  );
  await expect(page.locator(".visao__resumo")).toContainText(ptBR["tela3.modelo.combinacao"]);
  await expect(ressalva).toHaveCount(0);

  await escolherSerie(page, "uf:AC");
  await expect(ressalva).toBeVisible();
});

test("o período muda o realizado, e não a projeção", async ({ page }) => {
  await abrir(page);
  await page.locator('.visao__filtros [data-valor="tabela"]').click();
  const linhas = page.locator(".visao__tabela tbody tr");
  await expect(linhas).toHaveCount(12 + 3);
  await page.locator('.visao__filtros [data-valor="desde-2024"]').click();
  await expect(linhas).toHaveCount(31 + 3);
  await expect(page.locator(".projecao__mes-a-mes tbody tr")).toHaveCount(3);
});

test("escolher a data do teste muda o cartão do erro", async ({ page }) => {
  await abrir(page);
  const titulo = page.locator(".projecao__teste .cartao-grafico__titulo");
  await expect(titulo).toHaveText(ptBR["tela3.titulo-teste"].replace("{mes}", "abr/2026"));
  await page.locator('.projecao__teste [data-valor="2026-01-31"]').click();
  await expect(titulo).toHaveText(ptBR["tela3.titulo-teste"].replace("{mes}", "jan/2026"));
  await expect(page.locator(".projecao__teste svg").first()).toBeVisible();
});

test("o CSV só aparece na tabela e baixa a série inteira", async ({ page }) => {
  await abrir(page);
  const botao = page.getByRole("button", { name: ptBR["tela1.baixar-csv"] });
  await expect(botao).toHaveCount(0);
  await page.locator('.visao__filtros [data-valor="tabela"]').click();
  const [download] = await Promise.all([page.waitForEvent("download"), botao.click()]);
  expect(download.suggestedFilename()).toBe("projecao-carteira-pj-pais-BR-2026-07-31.csv");
  const conteudo = readFileSync(/** @type {string} */ (await download.path()), "utf8");
  expect(conteudo.trim().split(/\r?\n/)).toHaveLength(1 + 31 + 3);
});
