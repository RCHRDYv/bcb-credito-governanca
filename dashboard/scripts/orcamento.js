/**
 * PT: Confere o orçamento de carga do site construído (requisito RNF-03).
 *
 *     Comprime com gzip cada arquivo de `dist/`, do mesmo jeito que o GitHub
 *     Pages entrega, soma por tipo e compara com o limite do requisito. Falha
 *     quando algum tipo passa do limite, para o CI barrar a PR que pesa demais.
 *
 *     Os limites por tipo de arquivo ficam num objeto só, `LIMITES`. As
 *     fontes entram só no relatório, sem limite, porque o requisito pede "só
 *     os pesos usados", e não um número. A malha das UFs, versionada desde
 *     a #67, tem limite próprio de 100 KB.
 *
 *     Os dados têm conta própria, por visão (#66): cada visão, quando é a
 *     primeira a abrir, carrega até 300 KB comprimidos. A soma usa as visões
 *     que o `manifesto.json` registra para cada arquivo, mais o próprio
 *     manifesto, que toda visão lê.
 *
 *     Uso: `npm run build` e depois `npm run budget`.
 *
 * EN: Checks the built site's load budget (requirement RNF-03). Each file in
 *     `dist/` is gzipped, as GitHub Pages serves it, summed by type and
 *     compared with the limit. It fails when a type goes over, so CI blocks a
 *     pull request that weighs too much. Limits live in `LIMITES`. Data is
 *     checked per view: each view, when opened first, loads at most 300 KB,
 *     summed from the views the manifest records for each file.
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
  {
    nome: "Malha das UFs",
    inclui: (caminho) => relative(DIST, caminho).replaceAll("\\", "/").startsWith("geo/"),
    maximoKb: 100,
    origem: "RNF-03, #67",
  },
];

/**
 * PT: Limite de dados de cada visão, em KB comprimidos (RNF-03). Vale por
 *     visão, e não para todos os arquivos juntos (decidido em 2026-09-27, na
 *     #66).
 * EN: Per-view data limit, in compressed KB.
 */
const DADOS_POR_VISAO_KB = 300;

/**
 * PT: O que o orçamento lê do manifesto dos dados.
 * EN: What the budget reads from the data manifest.
 *
 * @typedef {object} ManifestoDosDados
 * @property {number[]} visoes_do_manifesto
 * @property {{ arquivo: string, visoes: number[] }[]} arquivos
 */

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

/**
 * PT: Soma, para cada visão, o peso comprimido dos arquivos de dados que ela
 *     carrega, e compara com o limite. Sem o manifesto, falha: os dados são
 *     versionados desde a #66, e o build precisa trazê-los.
 * EN: Sums each view's compressed data files and compares with the limit.
 *
 * @returns {Promise<boolean>} true se alguma visão passou do limite / true if over
 */
async function conferirDados() {
  const pasta = join(DIST, "data");
  const caminhoDoManifesto = join(pasta, "manifesto.json");
  console.log(`
Dados por visão, limite de ${DADOS_POR_VISAO_KB} KB comprimido (RNF-03)`);
  if (!existsSync(caminhoDoManifesto)) {
    console.error("  Não achei dist/data/manifesto.json. Os dados precisam estar em public/data/.");
    return true;
  }

  /** @type {ManifestoDosDados} */
  const manifesto = JSON.parse(await readFile(caminhoDoManifesto, "utf-8"));
  const tamanhoDoManifesto = await tamanhoComprimido(caminhoDoManifesto);
  const visoes = [...new Set(manifesto.arquivos.flatMap((a) => a.visoes))].sort((a, b) => a - b);

  let estourou = false;
  for (const visao of visoes) {
    const daVisao = manifesto.arquivos.filter((a) => a.visoes.includes(visao));
    const tamanhos = await Promise.all(
      daVisao.map((a) => tamanhoComprimido(join(pasta, a.arquivo))),
    );
    const doManifesto = manifesto.visoes_do_manifesto.includes(visao) ? tamanhoDoManifesto : 0;
    const total = tamanhos.reduce((soma, t) => soma + t, doManifesto);
    const passou = total > DADOS_POR_VISAO_KB * KB;
    estourou ||= passou;

    console.log(`  Visão ${visao}`);
    daVisao.forEach((a, i) => {
      console.log(`    ${a.arquivo}  ${emKb(tamanhos[i])}`);
    });
    if (doManifesto) console.log(`    manifesto.json  ${emKb(doManifesto)}`);
    console.log(`    Total: ${emKb(total)}${passou ? "  ACIMA DO LIMITE" : "  dentro do limite"}`);
  }
  return estourou;
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

  estourou = (await conferirDados()) || estourou;

  if (estourou) {
    process.exit(1);
  }
}

await main();
