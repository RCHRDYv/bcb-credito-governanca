/**
 * PT: Configuração do Vite, que serve o ambiente de desenvolvimento e gera o
 *     site estático publicado no GitHub Pages (ADRs 0016 e 0017).
 *
 *     O `base: "./"` faz todos os caminhos do build serem relativos. Assim o
 *     mesmo `dist/` funciona no `vite preview`, na raiz de um domínio e no
 *     subcaminho do Pages (`/bcb-credito-governanca/`), sem configurar o
 *     endereço em lugar nenhum.
 *
 *     O plugin da política de segurança de conteúdo põe a `<meta>` da
 *     política em toda página do build, e só no build (#68). O texto mora em
 *     `politica-de-seguranca.js`.
 *
 * EN: Vite configuration: the dev server and the static build published on
 *     GitHub Pages. A relative `base` lets the same `dist/` work in preview,
 *     at a domain root and under the Pages subpath. The content security
 *     policy plugin adds the policy `<meta>` to every built page.
 */

import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import { politicaDeSeguranca } from "./politica-de-seguranca.js";

/**
 * PT: Caminho absoluto de um arquivo desta pasta.
 * EN: Absolute path of a file in this folder.
 *
 * @param {string} arquivo
 * @returns {string}
 */
const aqui = (arquivo) => fileURLToPath(new URL(arquivo, import.meta.url));

export default defineConfig({
  base: "./",
  plugins: [politicaDeSeguranca()],
  build: {
    outDir: "dist",
    // PT: sem mapa de código no site publicado, que é só para leitura
    // EN: no source maps in the published site
    sourcemap: false,
    rolldownOptions: {
      // PT: o site e o catálogo do design system, que é documentação viva (#62 e #64)
      // EN: the site and the design system catalog, a living document
      input: {
        principal: aqui("index.html"),
        catalogo: aqui("catalogo.html"),
      },
    },
  },
  preview: {
    port: 4173,
    strictPort: true,
  },
});
