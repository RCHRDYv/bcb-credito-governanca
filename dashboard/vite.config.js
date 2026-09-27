/**
 * PT: Configuração do Vite, que serve o ambiente de desenvolvimento e gera o
 *     site estático publicado no GitHub Pages (ADRs 0016 e 0017).
 *
 *     O `base: "./"` faz todos os caminhos do build serem relativos. Assim o
 *     mesmo `dist/` funciona no `vite preview`, na raiz de um domínio e no
 *     subcaminho do Pages (`/bcb-credito-governanca/`), sem configurar o
 *     endereço em lugar nenhum.
 *
 * EN: Vite configuration: the dev server and the static build published on
 *     GitHub Pages. A relative `base` lets the same `dist/` work in preview,
 *     at a domain root and under the Pages subpath.
 */

import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  build: {
    outDir: "dist",
    // PT: sem mapa de código no site publicado, que é só para leitura
    // EN: no source maps in the published site
    sourcemap: false,
  },
  preview: {
    port: 4173,
    strictPort: true,
  },
});
