/**
 * PT: Testes de ponta a ponta da Tela 2 (#70), no site construído.
 *
 *     Conferem os requisitos da visão e os gerais:
 *     - a navegação leva à Tela 2 e marca a visão atual (RF-G01);
 *     - filtrar pela modalidade muda os títulos e não muda a escala (RF-G04);
 *     - escolher uma UF abre o painel na coluna inteira, com a série mensal
 *       das duas taxas, e fechar traz o custo do risco e o ranking (RF-G05);
 *     - a tabela e o ranking mostram as mesmas UFs que pioraram, e a tabela
 *       marca o alerta antecipado nas mesmas UFs que o resumo conta (RF-G06,
 *       RF-202);
 *     - os dois números de atraso aparecem com a definição a um clique
 *       (RF-202, RF-G07);
 *     - a ressalva da mudança de critério aparece quando a janela a cruza, e
 *       só então (RF-203);
 *     - sem a série mensal, o painel diz o problema e os números continuam;
 *     - o CSV só aparece na forma de tabela e baixa um arquivo.
 *
 * EN: End-to-end tests for Screen 2: navigation, filters, the full-column
 *     state panel with the monthly series, table and ranking, both arrears
 *     measures, the criterion-break caveat, the missing-series state and CSV.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";
import { ptBR } from "../../src/textos/pt-BR.js";

test.use({ viewport: { width: 1536, height: 864 } });

const ENDERECO = "./#/risco-por-uf";

/**
 * PT: Abre a Tela 2 e espera o território desenhar.
 * EN: Opens Screen 2 and waits for the territory to draw.
 *
 * @param {import("@playwright/test").Page} page
 */
async function abrir(page) {
  await page.goto(ENDERECO);
  await expect(page.locator(".visao--risco-por-uf .visao__forma svg").first()).toBeVisible();
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

test("a navegação leva à Tela 2 e marca a visão atual", async ({ page }) => {
  await page.goto("./");
  await page.getByRole("link", { name: ptBR["navegacao.risco-por-uf"] }).click();
  await expect(page.locator(".visao--risco-por-uf .visao__forma svg").first()).toBeVisible();
  await expect(page.locator('.navegacao [aria-current="page"]')).toHaveText(
    ptBR["navegacao.risco-por-uf"],
  );
  await expect(page).toHaveTitle(`${ptBR["navegacao.risco-por-uf"]} · ${ptBR["produto.nome"]}`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(ptBR["tela2.titulo"]);
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

test("escolher uma UF abre o painel na coluna inteira, com a série, e fechar traz o ranking", async ({
  page,
}) => {
  await abrir(page);
  await escolherForma(page, "tabela");
  await page.locator('[data-uf="MA"]').click();
  await expect(page.locator(".detalhe__titulo")).toHaveText("Maranhão");
  await expect(page.locator(".detalhe .etiqueta--alerta")).toBeVisible();
  await expect(page.locator(".detalhe .grafico--linhas svg")).toBeVisible();
  await expect(page.locator(".detalhe")).toContainText(ptBR["tela2.quebra-marco"]);
  await escolherForma(page, "mapa");
  await expect(page.locator(".visao__destaque")).toBeHidden();
  await expect(page.locator(".visao__ranking")).toBeHidden();
  await page.locator(".detalhe__fechar").click();
  await expect(page.locator(".visao__destaque")).toBeVisible();
  await expect(page.locator(".visao__ranking")).toBeVisible();
});

test("a tabela e o ranking mostram as mesmas UFs que pioraram, e o alerta bate com o resumo", async ({
  page,
}) => {
  await abrir(page);
  await expect(page.locator(".visao__ranking .grafico--ranking svg")).toBeVisible();
  const barras = await page
    .locator(".visao__ranking .grafico--ranking")
    .evaluate((el) => Number(getComputedStyle(el).getPropertyValue("--itens")));
  const alertasNoResumo = Number(await page.locator(".visao__resumo dd").nth(3).textContent());
  await escolherForma(page, "tabela");
  await expect(page.locator(".visao__tabela tbody tr")).toHaveCount(27);
  const pioraram = await page
    .locator(".visao__tabela tbody tr")
    .evaluateAll(
      (linhas) =>
        linhas.filter((linha) => linha.querySelector(".etiqueta--observar, .etiqueta--nao-entrar"))
          .length,
    );
  expect(pioraram).toBe(barras);
  await expect(page.locator(".visao__tabela tbody .etiqueta--alerta")).toHaveCount(alertasNoResumo);
});

test("os dois números de atraso aparecem com a definição a um clique", async ({ page }) => {
  await abrir(page);
  const caixa = page.locator(".risco__dois-numeros");
  await expect(caixa).toContainText(ptBR["tela2.inadimplida"]);
  await expect(caixa).toContainText(ptBR["tela2.ativo-problematico"]);
  await caixa.locator(".definicao__botao").first().click();
  await expect(page.locator(".definicao__caixa:popover-open")).toBeVisible();
});

test("a ressalva da mudança de critério aparece só quando a janela a cruza", async ({ page }) => {
  await abrir(page);
  // PT: um trecho da ressalva sem lacuna / EN: a placeholder-free excerpt
  const ressalva = "cruza a mudança de critério do ativo problemático";
  await expect(page.locator(".visao__sobre-o-territorio")).not.toContainText(ressalva);

  // PT: a mesma exportação, com a janela começando antes de jan/2025
  // EN: the same export, with the window starting before Jan 2025
  const pasta = join(dirname(fileURLToPath(import.meta.url)), "../../public/data/");
  const decisao = JSON.parse(readFileSync(`${pasta}decisao.json`, "utf8"));
  decisao.colunas.data_base_anterior = decisao.colunas.data_base_anterior.map(() => "2024-12-31");
  await page.route("**/data/decisao.json", (rota) => rota.fulfill({ json: decisao }));
  await page.reload();
  await expect(page.locator(".visao__sobre-o-territorio")).toContainText(ressalva);
});

test("sem a série mensal, o painel diz o problema e os números continuam", async ({ page }) => {
  await page.route("**/data/carteira_mensal_pj.json", (rota) => rota.abort());
  await abrir(page);
  await escolherForma(page, "tabela");
  await page.locator('[data-uf="MA"]').click();
  await expect(page.locator(".detalhe")).toContainText(ptBR["tela2.serie-erro"]);
  await expect(page.locator(".detalhe__lista")).toContainText("12,5%");
});

test("o CSV só aparece na tabela e baixa um arquivo", async ({ page }) => {
  await abrir(page);
  await expect(page.getByRole("button", { name: ptBR["tela1.baixar-csv"] })).toHaveCount(0);
  await escolherForma(page, "tabela");
  const [arquivo] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: ptBR["tela1.baixar-csv"] }).click(),
  ]);
  expect(arquivo.suggestedFilename()).toMatch(/^risco-pj-por-uf-02-.*\.csv$/);
});

test("uma modalidade sem UF comparável mostra o estado vazio com o motivo", async ({ page }) => {
  await abrir(page);
  await page.locator(".visao__filtros select").selectOption("01");
  await expect(page.locator(".visao__destaque")).toContainText(ptBR["tela2.vazio-titulo"]);
});
