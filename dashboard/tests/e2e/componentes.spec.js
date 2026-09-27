/**
 * PT: Testes de ponta a ponta dos componentes (#64), no navegador de
 *     verdade:
 *     - o controle de tema do topo fixa o tema, a escolha continua depois de
 *       recarregar a página, e o automático volta a seguir o sistema;
 *     - o controle segmentado funciona pelas setas do teclado;
 *     - a dica abre com o foco do teclado e fecha com o Esc.
 *
 * EN: End-to-end component tests: the theme control persists across reloads
 *     and automatic follows the system again; the segmented control works
 *     with arrow keys; the tooltip opens on focus and closes on Escape.
 */

import { expect, test } from "@playwright/test";

// PT: o fundo da página em cada tema / EN: page background per theme
const FUNDO = { claro: "rgb(244, 244, 244)", escuro: "rgb(22, 22, 22)" };

test.describe("controle de tema", () => {
  test.use({ colorScheme: "light" });

  test("fixa o escuro, guarda a escolha e volta ao automático", async ({ page }) => {
    await page.goto("./");
    const tema = page.getByRole("radiogroup", { name: "Tema" });
    await expect(tema.getByRole("radio", { name: "Automático" })).toHaveAttribute(
      "aria-checked",
      "true",
    );

    await tema.getByRole("radio", { name: "Escuro" }).click();
    await expect(page.locator("html")).toHaveAttribute("data-tema", "escuro");
    await expect(page.locator("html")).toHaveCSS("background-color", FUNDO.escuro);

    // PT: depois de recarregar, o script do <head> aplica a escolha guardada
    // EN: after a reload, the head script applies the stored choice
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-tema", "escuro");
    await expect(
      page.getByRole("radiogroup", { name: "Tema" }).getByRole("radio", { name: "Escuro" }),
    ).toHaveAttribute("aria-checked", "true");

    await page
      .getByRole("radiogroup", { name: "Tema" })
      .getByRole("radio", { name: "Automático" })
      .click();
    await expect(page.locator("html")).not.toHaveAttribute("data-tema", /.+/);
    await expect(page.locator("html")).toHaveCSS("background-color", FUNDO.claro);
  });
});

test.describe("componentes do catálogo", () => {
  test("o controle segmentado troca a opção pelas setas", async ({ page }) => {
    await page.goto("./catalogo.html");
    const grupo = page.getByRole("radiogroup", { name: "Visão" }).first();
    await grupo.getByRole("radio", { name: "Recomendação" }).focus();
    await page.keyboard.press("ArrowLeft");
    const risco = grupo.getByRole("radio", { name: "Onde o risco piora" });
    await expect(risco).toHaveAttribute("aria-checked", "true");
    await expect(risco).toBeFocused();
  });

  test("a dica abre com o foco e fecha com o Esc", async ({ page }) => {
    await page.goto("./catalogo.html");
    const gatilho = page.locator(".com-dica > button").first();
    const dica = page.locator(".com-dica > .dica").first();
    await expect(dica).toBeHidden();
    await gatilho.focus();
    await expect(dica).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(dica).toBeHidden();
    await expect(gatilho).toBeFocused();
  });
});
