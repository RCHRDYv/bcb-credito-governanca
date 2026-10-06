/**
 * PT: Testes de ponta a ponta da Tela 1 (#69), no site construído.
 *
 *     Conferem os requisitos gerais e os da visão:
 *     - a navegação marca a visão atual (RF-G01);
 *     - filtrar pela modalidade muda os títulos e não muda a escala de cor
 *       do território (RF-G04);
 *     - escolher uma UF abre o painel de detalhe ao lado (RF-G05);
 *     - a tabela tem uma linha por UF, e o ranking uma barra por UF abaixo
 *       da mediana, as mesmas que a tabela mostra com crédito faltando
 *       (RF-G06);
 *     - a definição se abre a partir do número (RF-G07);
 *     - a impressão sai sem vidro (RF-G09);
 *     - os estados vazio e de erro dizem como sair deles (RF-G11);
 *     - o aviso da UF da sede aparece junto do território (RF-104);
 *     - o CSV só aparece na forma de tabela e baixa um arquivo.
 *
 * EN: End-to-end tests for Screen 1: navigation, filters, detail panel,
 *     table and ranking, definitions, print, empty and error states, the
 *     head-office caveat and the CSV download.
 */

import { expect, test } from "@playwright/test";
import { ptBR } from "../../src/textos/pt-BR.js";

test.use({ viewport: { width: 1536, height: 864 } });

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
 * PT: Escolhe uma forma do território.
 * EN: Picks a territory form.
 *
 * @param {import("@playwright/test").Page} page
 * @param {string} forma
 */
function escolherForma(page, forma) {
  return page.locator(`.visao__filtros [data-valor="${forma}"]`).click();
}

test("a navegação marca a visão atual", async ({ page }) => {
  await abrir(page);
  await expect(page.locator('.navegacao [aria-current="page"]')).toHaveText(
    ptBR["navegacao.credito-por-uf"],
  );
});

test("filtrar pela modalidade muda os títulos e mantém a escala de cor", async ({ page }) => {
  await abrir(page);
  const escala = () =>
    page.locator(".visao__forma .escala__barra").evaluate((el) => el.style.backgroundImage);
  const antes = await escala();
  await page.locator(".visao__filtros select").selectOption("04");
  await expect(page.locator(".visao__destaque .cartao-grafico__titulo")).toContainText(
    "Financiamentos",
  );
  expect(await escala()).toBe(antes);
});

test("escolher uma UF na tabela abre o painel dela, e fechar traz o ranking", async ({ page }) => {
  await abrir(page);
  await escolherForma(page, "tabela");
  await page.locator('[data-uf="MG"]').click();
  await expect(page.locator(".detalhe__titulo")).toHaveText("Minas Gerais");
  await escolherForma(page, "mapa");
  await expect(page.locator(".visao__ranking")).toBeHidden();
  await page.locator(".detalhe__fechar").click();
  await expect(page.locator(".visao__ranking")).toBeVisible();
});

test("a tabela e o ranking mostram as mesmas UFs abaixo da mediana", async ({ page }) => {
  await abrir(page);
  const barras = await page
    .locator(".visao__ranking .grafico--ranking")
    .evaluate((el) => Number(getComputedStyle(el).getPropertyValue("--itens")));
  await escolherForma(page, "tabela");
  await expect(page.locator(".visao__tabela tbody tr")).toHaveCount(27);
  const comCredito = await page
    .locator(".visao__tabela tbody tr")
    .evaluateAll(
      (linhas) =>
        linhas.filter((linha) => linha.lastElementChild?.textContent?.trim() !== "–").length,
    );
  expect(comCredito).toBe(barras);
});

test("a definição se abre a partir do número", async ({ page }) => {
  await abrir(page);
  const botao = page.locator(".visao__resumo .definicao__botao").first();
  await botao.click();
  await expect(page.locator(".definicao__caixa:popover-open")).toBeVisible();
});

test("o aviso da UF da sede aparece junto do território", async ({ page }) => {
  await abrir(page);
  await expect(page.locator(".visao__sobre-o-territorio")).toContainText(
    ptBR["tela1.aviso-sede"].slice(0, 30),
  );
});

test("o CSV só aparece na tabela e baixa um arquivo", async ({ page }) => {
  await abrir(page);
  await expect(page.getByRole("button", { name: ptBR["tela1.baixar-csv"] })).toHaveCount(0);
  await escolherForma(page, "tabela");
  const [arquivo] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: ptBR["tela1.baixar-csv"] }).click(),
  ]);
  expect(arquivo.suggestedFilename()).toMatch(/^credito-pj-por-uf-todas-.*\.csv$/);
});

test("uma modalidade sem UF comparável mostra o estado vazio com o motivo", async ({ page }) => {
  await abrir(page);
  await page.locator(".visao__filtros select").selectOption("01");
  await expect(page.locator(".visao__destaque")).toContainText(ptBR["tela1.vazio-titulo"]);
});

test("sem os dados, a tela mostra o erro e como tentar de novo", async ({ page }) => {
  await page.route("**/data/decisao.json", (rota) => rota.abort());
  await page.goto("./");
  await expect(page.getByText(ptBR["navegacao.erro-titulo"])).toBeVisible();
  await expect(page.getByRole("button", { name: ptBR["estado.tentar-de-novo"] })).toBeVisible();
});

test("a impressão sai sem vidro", async ({ page }) => {
  await abrir(page);
  await page.emulateMedia({ media: "print" });
  const desfoque = await page
    .locator(".detalhe")
    .evaluate((el) => getComputedStyle(el).backdropFilter);
  expect(["none", ""]).toContain(desfoque);
});
