/**
 * PT: Configuração do Vitest, para os testes unitários. Herda a do Vite e só
 *     diz onde estão os testes, para ele não tentar rodar os de ponta a ponta,
 *     que são do Playwright.
 *
 * EN: Vitest configuration for unit tests. It extends Vite's and only points
 *     at the unit tests, leaving the end-to-end ones to Playwright.
 */

import { defineConfig, mergeConfig } from "vitest/config";
import configuracaoDoVite from "./vite.config.js";

export default mergeConfig(
  configuracaoDoVite,
  defineConfig({
    test: {
      include: ["tests/unit/**/*.test.js"],
      environment: "node",
    },
  }),
);
