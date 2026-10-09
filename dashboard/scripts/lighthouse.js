/**
 * PT: Roda o Lighthouse no site construído e confere as metas do requisito
 *     RNF-02, no celular e no computador.
 *
 *     Como funciona:
 *     1. sobe o `vite preview` sobre o `dist/`, pela API do Vite;
 *     2. abre o Google Chrome instalado, que é o navegador que o Lighthouse
 *        foi feito para medir e que o runner do CI já traz. Sem Chrome
 *        instalado, usa o Chromium do Playwright;
 *     3. roda o Lighthouse com a configuração padrão, que simula um celular,
 *        três vezes, e com a de computador, uma vez;
 *     4. imprime as notas e as medidas do RNF-01 (LCP, CLS e tempo de
 *        bloqueio, que no laboratório faz o papel do INP) de cada rodada e
 *        falha quando a mediana fica abaixo de qualquer meta.
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
 * PT: Quantas vezes cada perfil roda. O celular roda três vezes, e a meta
 *     compara a mediana de cada nota, como a documentação do Lighthouse
 *     recomenda contra a variação da máquina: uma rodada só reprovava o CI
 *     sem nada errado no site (#92, decidido pelo Yuri em 2026-10-06). O
 *     computador, que não varia, roda uma vez.
 * EN: Runs per profile; mobile runs three times and the targets apply to the
 *     median of each score, as Lighthouse recommends against host variance.
 *
 * @type {Record<"celular" | "computador", number>}
 */
const RODADAS = { celular: 3, computador: 1 };

/**
 * PT: A mediana de uma lista de números.
 * EN: The median of a list of numbers.
 *
 * @param {number[]} valores
 * @returns {number}
 */
function mediana(valores) {
  const ordenados = [...valores].sort((a, b) => a - b);
  const meio = Math.floor(ordenados.length / 2);
  return ordenados.length % 2 ? ordenados[meio] : (ordenados[meio - 1] + ordenados[meio]) / 2;
}

/**
 * PT: Roda o Lighthouse num perfil, as vezes de `RODADAS`, imprime cada
 *     rodada e devolve as falhas da mediana contra as metas. Quando a meta
 *     falha, o diagnóstico é o da rodada com a nota de desempenho mediana.
 * EN: Runs Lighthouse on one profile `RODADAS` times, prints each run and
 *     returns the median's misses; diagnostics come from the median run.
 *
 * @param {string} endereco
 * @param {number} porta Porta de depuração do Chromium / Chromium debugging port
 * @param {"celular" | "computador"} perfil
 * @returns {Promise<string[]>}
 */
async function auditar(endereco, porta, perfil) {
  const metas = METAS[perfil];
  const configuracao = perfil === "computador" ? configuracaoDeComputador : undefined;
  console.log(`
${perfil}`);
  /** @type {import("lighthouse").Result[]} */
  const rodadas = [];
  for (let i = 1; i <= RODADAS[perfil]; i += 1) {
    const resultado = await lighthouse(
      endereco,
      { port: porta, logLevel: "error", onlyCategories: Object.keys(metas) },
      configuracao,
    );
    if (!resultado) return [`${perfil}: o Lighthouse não devolveu resultado`];
    const { categories, audits, environment } = resultado.lhr;
    const notas = Object.keys(metas)
      .map((c) => `${c} ${Math.round((categories[c]?.score ?? 0) * 100)}`)
      .join(", ");
    const medidas = MEDIDAS.map((m) => `${m} ${audits[m]?.displayValue ?? "sem valor"}`).join(", ");
    // PT: a nota de CPU que o Lighthouse mede da máquina; a simulação do
    //     celular multiplica o tempo observado, então máquina lenta pesa (#89)
    // EN: Lighthouse's own CPU benchmark of the host
    console.log(`  rodada ${i}: ${notas}`);
    console.log(`    ${medidas}, benchmarkIndex ${environment.benchmarkIndex}`);
    rodadas.push(resultado.lhr);
  }

  const falhas = [];
  const titulo = rodadas.length > 1 ? `  mediana de ${rodadas.length} rodadas:` : "  nota:";
  console.log(titulo);
  for (const [categoria, meta] of Object.entries(metas)) {
    const nota = mediana(rodadas.map((lhr) => lhr.categories[categoria]?.score ?? 0));
    const ok = nota >= meta;
    const aviso = ok ? "" : " ABAIXO";
    console.log(`    ${categoria}: ${Math.round(nota * 100)} (meta ${meta * 100})${aviso}`);
    if (!ok) {
      falhas.push(`${perfil}: ${categoria} ${Math.round(nota * 100)} abaixo de ${meta * 100}`);
    }
  }
  if (falhas.length > 0) {
    const desempenho = (/** @type {import("lighthouse").Result} */ lhr) =>
      lhr.categories.performance?.score ?? 0;
    const alvo = mediana(rodadas.map(desempenho));
    const doMeio = rodadas.find((lhr) => desempenho(lhr) === alvo) ?? rodadas[0];
    diagnostico(/** @type {Record<string, { details?: unknown }>} */ (doMeio.audits));
  }
  return falhas;
}

/**
 * PT: Quando a meta falha, o que ocupou a thread principal: o tempo por tipo
 *     de trabalho, os scripts que mais custaram e as tarefas longas, para o
 *     log do CI dizer onde mexer (#89).
 * EN: On a miss, what kept the main thread busy: work by kind, the costliest
 *     scripts and the long tasks.
 *
 * @param {Record<string, { details?: unknown }>} audits
 */
function diagnostico(audits) {
  /**
   * @param {string} id
   * @returns {Record<string, unknown>[]}
   */
  const itens = (id) =>
    /** @type {{ items?: Record<string, unknown>[] } | undefined} */ (audits[id]?.details)?.items ??
    [];
  const ms = (/** @type {unknown} */ v) => `${Math.round(Number(v))} ms`;
  const arquivo = (/** @type {unknown} */ url) => String(url).split("/").pop() || String(url);
  console.log("  thread principal, por tipo:");
  for (const item of itens("mainthread-work-breakdown").slice(0, 6)) {
    console.log(`    ${item.groupLabel}: ${ms(item.duration)}`);
  }
  console.log("  scripts que mais custaram:");
  for (const item of itens("bootup-time").slice(0, 5)) {
    console.log(`    ${arquivo(item.url)}: ${ms(item.total)} (execução ${ms(item.scripting)})`);
  }
  console.log("  tarefas longas:");
  for (const item of itens("long-tasks").slice(0, 8)) {
    console.log(`    ${arquivo(item.url)}: ${ms(item.duration)}, aos ${ms(item.startTime)}`);
  }
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
