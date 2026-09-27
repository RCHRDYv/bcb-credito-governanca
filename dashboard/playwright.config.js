/**
 * PT: Configuração dos testes de ponta a ponta.
 *
 *     Os testes rodam contra o site já construído (`vite build` e depois
 *     `vite preview`), e não contra o servidor de desenvolvimento, porque é o
 *     build que vai para o Pages. Rodam nos três motores que o RNF-06 exige:
 *     Chromium (Chrome e Edge), Firefox e WebKit (Safari).
 *
 * EN: End-to-end test configuration. Tests run against the built site, not
 *     the dev server, because the build is what ships. They run on the three
 *     engines requirement RNF-06 asks for.
 */

import { defineConfig, devices } from "@playwright/test";

const ENDERECO = "http://localhost:4173";

export default defineConfig({
  testDir: "tests/e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  // PT: no CI, o relatório "github" marca a falha na própria linha do teste, na PR
  // EN: in CI, the "github" reporter annotates the failing line in the pull request
  reporter: process.env.CI ? [["list"], ["github"]] : "list",
  use: {
    baseURL: ENDERECO,
    trace: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
  webServer: {
    command: "npm run build && npm run preview",
    url: ENDERECO,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
