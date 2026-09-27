/**
 * PT: Roda o Lighthouse no site construído e confere as metas do requisito
 *     RNF-02, no celular e no computador.
 *
 *     Como funciona:
 *     1. sobe o `vite preview` sobre o `dist/`, pela API do Vite;
 *     2. abre o Google Chrome instalado, que é o navegador que o Lighthouse
 *        foi feito para medir e que o runner do CI já traz. Sem Chrome
 *        instalado, usa o Chromium do Playwright;
 *     3. roda o Lighthouse duas vezes: com a configuração padrão, que simula
 *        um celular, e com a de computador;
 *     4. imprime as notas e as medidas do RNF-01 (LCP, CLS e tempo de
 *        bloqueio, que no laboratório faz o papel do INP) e falha abaixo de
 *        qualquer meta.
 *
 *     O Lighthouse é usado direto, sem o `@lhci/cli`, porque o `@lhci/cli`
 *     está parado desde jun/2025, com uma versão antiga do Lighthouse dentro.
 *
 *     Uso: `npm run build` e depois `npm run lighthouse`.
 *
 * EN: Runs Lighthouse on the built site, on mobile and desktop, and checks
 *     requirement RNF-02's targets. It serves `dist/` with Vite's preview API,
 *     drives the installed Google Chrome (Playwright's Chromium as a
 *     fallback), prints scores plus LCP, CLS and total
 *     blocking time, and fails below any target. Lighthouse is used directly
 *     because `@lhci/cli` has been idle since June 2025.
 */

import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";
import * as chromeLauncher from "chrome-launcher";
import lighthouse from "lighthouse";
import configuracaoDeComputador from "lighthouse/core/config/desktop-config.js";
import { preview } from "vite";

const RAIZ = fileURLToPath(new URL("..", import.meta.url));

/** @typedef {"performance" | "accessibility" | "best-practices"} Categoria */

/**
 * PT: Metas do RNF-02, de 0 a 1, como o Lighthouse devolve.
 * EN: RNF-02 targets, from 0 to 1, as Lighthouse reports them.
 *
 * @type {Record<"celular" | "computador", Record<Categoria, number>>}
 */
const METAS = {
  celular: { performance: 0.8, accessibility: 1, "best-practices": 0.95 },
  computador: { performance: 0.9, accessibility: 1, "best-practices": 0.95 },
};

/** PT: auditorias do RNF-01 que são impressas / EN: RNF-01 audits that are printed */
const MEDIDAS = ["largest-contentful-paint", "cumulative-layout-shift", "total-blocking-time"];

/**
 * PT: Roda o Lighthouse num perfil e devolve as falhas contra as metas.
 * EN: Runs Lighthouse on one profile and returns the misses against targets.
 *
 * @param {string} endereco
 * @param {number} porta Porta de depuração do Chromium / Chromium debugging port
 * @param {"celular" | "computador"} perfil
 * @returns {Promise<string[]>}
 */
async function auditar(endereco, porta, perfil) {
  const metas = METAS[perfil];
  const configuracao = perfil === "computador" ? configuracaoDeComputador : undefined;
  const resultado = await lighthouse(
    endereco,
    { port: porta, logLevel: "error", onlyCategories: Object.keys(metas) },
    configuracao,
  );
  if (!resultado) {
    return [`${perfil}: o Lighthouse não devolveu resultado`];
  }

  const { categories, audits } = resultado.lhr;
  const falhas = [];
  console.log(`\n${perfil}`);
  for (const [categoria, meta] of Object.entries(metas)) {
    const nota = categories[categoria]?.score ?? 0;
    const ok = nota >= meta;
    const aviso = ok ? "" : " ABAIXO";
    console.log(`  ${categoria}: ${Math.round(nota * 100)} (meta ${meta * 100})${aviso}`);
    if (!ok) {
      falhas.push(`${perfil}: ${categoria} ${Math.round(nota * 100)} abaixo de ${meta * 100}`);
    }
  }
  for (const medida of MEDIDAS) {
    console.log(`  ${medida}: ${audits[medida]?.displayValue ?? "sem valor"}`);
  }
  return falhas;
}

/**
 * PT: O Chrome instalado, se houver; senão, o Chromium do Playwright. O
 *     Chromium do Playwright não é assinado, e há Windows que bloqueiam
 *     programa sem assinatura.
 * EN: The installed Chrome if any, else Playwright's Chromium, which is
 *     unsigned and blocked on some Windows setups.
 *
 * @returns {string}
 */
function caminhoDoNavegador() {
  return chromeLauncher.Launcher.getInstallations()[0] ?? chromium.executablePath();
}

async function main() {
  if (!existsSync(`${RAIZ}/dist`)) {
    console.error("Não achei dist/. Rode `npm run build` antes do Lighthouse.");
    process.exit(1);
  }

  // PT: porta diferente da dos testes de ponta a ponta, para os dois poderem rodar juntos
  // EN: a port other than the end-to-end tests', so both can run at once
  const servidor = await preview({
    root: RAIZ,
    logLevel: "warn",
    preview: { port: 4174, strictPort: true },
  });
  const endereco = servidor.resolvedUrls?.local[0] ?? "http://localhost:4174/";

  const falhas = [];
  /** @type {chromeLauncher.LaunchedChrome | undefined} */
  let navegador;
  try {
    const chromePath = caminhoDoNavegador();
    console.log(`Navegador: ${chromePath}`);
    navegador = await chromeLauncher.launch({
      chromePath,
      chromeFlags: ["--headless=new", "--no-sandbox"],
    });
    falhas.push(...(await auditar(endereco, navegador.port, "celular")));
    falhas.push(...(await auditar(endereco, navegador.port, "computador")));
  } finally {
    navegador?.kill();
    await servidor.close();
  }

  if (falhas.length > 0) {
    console.error(`\nMetas do RNF-02 não atingidas:\n  ${falhas.join("\n  ")}`);
    process.exit(1);
  }
  console.log("\nTodas as metas do RNF-02 atingidas.");
}

await main();
