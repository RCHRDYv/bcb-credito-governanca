/**
 * PT: Confere o orçamento de carga do site construído (requisito RNF-03).
 *
 *     Comprime com gzip cada arquivo de `dist/`, do mesmo jeito que o GitHub
 *     Pages entrega, soma por tipo e compara com o limite do requisito. Falha
 *     quando algum tipo passa do limite, para o CI barrar a PR que pesa demais.
 *
 *     Os limites ficam num objeto só, `LIMITES`. Hoje só o JavaScript tem
 *     limite; os dados (300 KB) e a malha das UFs (100 KB) entram quando a
 *     #66 e a #67 criarem esses arquivos. As fontes entram só no relatório,
 *     sem limite, porque o requisito pede "só os pesos usados", e não um
 *     número.
 *
 *     Uso: `npm run build` e depois `npm run budget`.
 *
 * EN: Checks the built site's load budget (requirement RNF-03). Each file in
 *     `dist/` is gzipped, as GitHub Pages serves it, summed by type and
 *     compared with the limit. It fails when a type goes over, so CI blocks a
 *     pull request that weighs too much. Limits live in `LIMITES`.
 */

import { existsSync } from "node:fs";
import { readdir, readFile } from "node:fs/promises";
import { extname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const RAIZ = fileURLToPath(new URL("..", import.meta.url));
const DIST = join(RAIZ, "dist");

// PT: 1 KB = 1000 bytes, como o DevTools do Chrome mostra
// EN: 1 KB = 1000 bytes, as Chrome DevTools shows
const KB = 1000;

/**
 * @typedef {object} Limite
 * @property {string} nome Nome do grupo de arquivos / file group name
 * @property {(caminho: string) => boolean} inclui Diz se o arquivo entra no grupo / whether a file belongs
 * @property {number | null} maximoKb Limite comprimido em KB, ou null para só relatar / limit in KB, or null to report only
 * @property {string} origem Requisito que fixou o limite / requirement that set the limit
 */

/** @type {Limite[]} */
const LIMITES = [
  {
    nome: "JavaScript",
    inclui: (caminho) => extname(caminho) === ".js",
    maximoKb: 350,
    origem: "RNF-03",
  },
  {
    nome: "Fontes",
    inclui: (caminho) => extname(caminho) === ".woff2",
    maximoKb: null,
    origem: "RNF-03, só os pesos usados",
  },
];

/**
 * PT: Lista todos os arquivos de uma pasta, descendo nas subpastas.
 * EN: Lists every file under a folder, recursively.
 *
 * @param {string} pasta
 * @returns {Promise<string[]>}
 */
async function listarArquivos(pasta) {
  const entradas = await readdir(pasta, { withFileTypes: true, recursive: true });
  return entradas.filter((e) => e.isFile()).map((e) => join(e.parentPath, e.name));
}

/**
 * PT: Tamanho do arquivo depois do gzip, em bytes.
 * EN: File size after gzip, in bytes.
 *
 * @param {string} caminho
 * @returns {Promise<number>}
 */
async function tamanhoComprimido(caminho) {
  return gzipSync(await readFile(caminho), { level: 9 }).length;
}

/**
 * PT: Formata bytes em KB com uma casa, no formato brasileiro.
 * EN: Formats bytes as KB with one decimal, Brazilian style.
 *
 * @param {number} bytes
 * @returns {string}
 */
function emKb(bytes) {
  return `${(bytes / KB).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} KB`;
}

async function main() {
  if (!existsSync(DIST)) {
    console.error("Não achei dist/. Rode `npm run build` antes do orçamento.");
    process.exit(1);
  }

  const arquivos = await listarArquivos(DIST);
  let estourou = false;

  for (const limite of LIMITES) {
    const doGrupo = arquivos.filter(limite.inclui);
    const tamanhos = await Promise.all(doGrupo.map(tamanhoComprimido));
    const total = tamanhos.reduce((soma, t) => soma + t, 0);
    const passou = limite.maximoKb !== null && total > limite.maximoKb * KB;
    estourou ||= passou;

    const regra =
      limite.maximoKb === null
        ? "sem limite, só relatório"
        : `limite de ${limite.maximoKb} KB comprimido`;
    console.log(`\n${limite.nome}, ${regra} (${limite.origem})`);
    doGrupo.forEach((caminho, i) => {
      console.log(`  ${relative(DIST, caminho).replaceAll("\\", "/")}  ${emKb(tamanhos[i])}`);
    });
    const situacao =
      limite.maximoKb === null ? "" : passou ? "  ACIMA DO LIMITE" : "  dentro do limite";
    console.log(`  Total: ${emKb(total)}${situacao}`);
  }

  if (estourou) {
    process.exit(1);
  }
}

await main();
